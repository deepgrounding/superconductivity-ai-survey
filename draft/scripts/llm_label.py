#!/usr/bin/env python3
"""LLM labelling pass over the corpus (family / task / ai_method / off_topic).

Why: keyword rules reached only 80% (family) and 70% (task) agreement with hand
labels on a 150-row stratified sample -- the dominant error being papers whose
motivation sentences name the other mode of work (characterization<->theory).
The prompt therefore states the decisive tie-break explicitly: label by what the
abstract claims as the paper's OWN contribution, not by what it mentions.

Results are cached per arXiv id in artifacts/llm_labels.jsonl (resumable).
`--benchmark` scores a model against artifacts/label_truth.csv instead of
labelling the corpus, so the model is chosen by measured agreement.

Usage:
  python draft/scripts/llm_label.py --benchmark --model qwen/qwen3-235b-a22b-2507
  python draft/scripts/llm_label.py --model <winner> [--limit N] [--workers 8]
  python draft/scripts/llm_label.py --apply        # write labels into the corpus CSV
"""
import argparse, csv, json, re, sys, time, urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "artifacts" / "sc_corpus_v1.csv"
TRUTH = ROOT / "artifacts" / "label_truth.csv"
CACHE = ROOT / "artifacts" / "llm_labels.jsonl"
URL = "https://openrouter.ai/api/v1/chat/completions"
BATCH = 10

SYSTEM = """You classify condensed-matter physics preprints for a survey of superconductivity research.

For each paper assign FOUR fields.

FAMILY -- the material system the paper is about:
  conv          conventional / electron-phonon superconductors, including high-pressure hydrides
                (H3S, LaH10, CeH9...), MgB2, elemental metals, nitrides/carbides/borides, A15,
                alloys, bismuthates, fullerides, intermetallics
  cuprate       copper-oxide superconductors (YBCO, BSCCO, LSCO, Hg/Tl-based, Pb-apatite claims)
  febased       iron pnictides and chalcogenides (BaFe2As2, FeSe, LiFeAs, 1111 compounds)
  nickelate     nickelates (infinite-layer NdNiO2/LaNiO2, Ruddlesden-Popper La3Ni2O7, La4Ni3O10)
  unconv_other  other unconventional bulk systems: heavy fermion (UTe2, CeCoIn5, YbRh2Si2),
                Sr2RuO4, organics, Cr/Mn-based, noncentrosymmetric bulk compounds
  lowd          two-dimensional / interface / moire systems: twisted graphene, rhombohedral
                graphene, kagome AV3Sb5, TMDs (NbSe2, TaS2, WSe2), FeSe/STO, oxide interfaces,
                KTaO3, monolayer and few-layer superconductors
  topo          topological superconductivity and Majorana physics: proximitized semiconductor
                nanowires, magnet-superconductor hybrids, Majorana/parafermion modes,
                topological insulator-superconductor structures
  device        superconducting devices and technology: qubits, transmons, SQUIDs, resonators,
                amplifiers, photon detectors, SFQ logic, wires/tapes/magnets, RF cavities
  general       MATERIAL-AGNOSTIC work: formalism, general theory of pairing/vortices/Josephson
                physics, methodology and instrumentation, cold-atom analogues, model studies not
                tied to a specific material family

TASK -- the MODE OF INQUIRY the paper itself uses. This axis is about HOW the work was done,
never about whether the topic is applied: a qubit paper still gets theory / synthesis /
characterization like any other. (Application context is carried by family=device.)
  theory            analytical or numerical many-body theory, model Hamiltonians, field theory,
                    QMC/DMRG/DMFT, symmetry analysis, phenomenology, device/circuit proposals and
                    architectures that are worked out on paper rather than built, reviews
  abinitio          first-principles / DFT / DFPT electron-phonon, Eliashberg or SCDFT Tc
                    calculations, crystal-structure search, molecular dynamics on real compounds
  discovery         reporting a NEW superconducting material, or searching/screening/designing
                    for candidate materials (databases, high-throughput screens, inverse design)
  synthesis         sample growth, thin-film deposition, crystal growth, topotactic reduction,
                    device fabrication process development -- the contribution is MAKING the
                    material or device, not measuring or modelling it
  characterization  measurements on existing samples or devices: ARPES, STM, neutron, muSR, NMR,
                    transport, specific heat, optics, x-ray, qubit/resonator/detector performance
                    measurements, and analyses of such data

AI_METHOD -- only if the paper USES a machine-learning / AI method as part of its own work:
  surrogate       regression/classification models, random forest, boosting, kernel methods,
                    plain neural-network fitting, symbolic regression, dimensionality reduction
  gnn_potential   graph neural networks, machine-learned interatomic potentials, universal
                    potentials/foundation models (MACE, CHGNet, M3GNet, GNoME)
  generative      generative models for structures/compositions: diffusion, VAE, GAN, flows
  llm             large language models, LLM agents, text mining of literature
  nqs             neural-network quantum states / neural wavefunctions
  autonomous_exp  autonomous or self-driving labs, closed-loop active learning, Bayesian
                    optimisation driving experiments
  none            no AI/ML method used (this is the common case -- do NOT tag a paper just
                    because it mentions AI, or because it uses ordinary numerics)

OFF_TOPIC -- true if the paper is not about superconductivity or superconducting materials at
all (e.g. AI in education, catalysis, unrelated cold-atom or plasma work). Otherwise false.

DECISIVE RULE: label by what the abstract claims as the paper's OWN contribution, not by what
it merely mentions or motivates with. A theory paper motivated by ARPES data is theory. An
experiment interpreted with a model is characterization.

BOUNDARY CASES THAT ARE COMMONLY GOT WRONG -- read these carefully:

* synthesis vs characterization. Most experimental papers both make and measure samples. Choose
  synthesis when MAKING the material is presented as the advance: a new or improved growth
  route, first films/crystals of a compound, topotactic reduction, pressure synthesis of a new
  phase, control of stoichiometry/strain/doping through growth, fabrication process development,
  or a study of how growth conditions change the result. Choose characterization only when the
  samples are a means to a measurement and the growth is routine or done elsewhere. Phrases like
  "we report the synthesis of", "films were grown by", "we developed a method to prepare",
  "high-quality single crystals were obtained" signal synthesis.

* discovery vs characterization. Choose discovery when the paper reports superconductivity in a
  material where it was not previously known, or searches/screens/designs across a space of
  candidate materials. "Superconductivity in X", "discovery of superconductivity", "we report a
  new superconductor", "pressure-induced superconductivity in X", high-throughput screens and
  inverse design are discovery. Detailed study of an already-known superconductor is not.

* abinitio vs theory. Choose abinitio when the calculation is performed on a REAL compound with
  first-principles input: DFT, DFPT, electron-phonon coupling, Eliashberg/SCDFT Tc, phonon
  spectra, structure search, DFT+DMFT on a real material, machine-learned potentials fitted to
  DFT. Choose theory for model Hamiltonians and formalism (Hubbard, t-J, BdG, field theory,
  Ginzburg-Landau, symmetry analysis) even when a material motivates them.

* abinitio vs discovery. A first-principles study that PREDICTS a new superconductor or screens
  candidates is discovery; one that explains or computes properties of a known compound is
  abinitio.

If a field is genuinely undecidable from the abstract, answer "unclear" for that field.

Reply with ONLY a JSON array, one object per paper, in the same order:
[{"id":"<given id>","family":"...","task":"...","ai_method":"...","off_topic":false}, ...]"""

def api_key():
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"\'')
    sys.exit("no OPENROUTER_API_KEY in .env")

def ask(batch, model, key):
    user = "\n\n".join(f'id: {r["arxiv_id"]}\ntitle: {r["title"]}\nabstract: {r["abstract"][:600]}'
                       for r in batch)
    body = json.dumps({"model": model, "temperature": 0,
                       "messages": [{"role": "system", "content": SYSTEM},
                                    {"role": "user", "content": user}]}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                txt = json.load(r)["choices"][0]["message"]["content"]
            m = re.search(r"\[.*\]", txt, re.S)
            if not m: raise ValueError("no JSON array in reply")
            got = json.loads(m.group(0))
            by_id = {str(d.get("id", "")).strip(): d for d in got if isinstance(d, dict)}
            return [by_id.get(r["arxiv_id"]) for r in batch]
        except Exception as e:
            if attempt == 3:
                print(f"  batch failed: {e}", file=sys.stderr)
                return [None] * len(batch)
            time.sleep(3 * (attempt + 1))

def run(rows, model, key, workers):
    batches = [rows[i:i + BATCH] for i in range(0, len(rows), BATCH)]
    out, done = {}, [0]
    def work(b):
        res = ask(b, model, key)
        done[0] += len(b)
        if done[0] % 200 < BATCH: print(f"  {done[0]}/{len(rows)}", flush=True)
        return list(zip(b, res))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for pairs in ex.map(work, batches):
            for r, d in pairs:
                if d: out[r["arxiv_id"]] = d
    return out

def benchmark(model, key, workers, n):
    rows = [dict(r, abstract=r["abstract"]) for r in csv.DictReader(open(TRUTH))][:n]
    got = run(rows, model, key, workers)
    valid = [r for r in rows if r["family_true"] != "bleed"]
    fam = sum(got.get(r["arxiv_id"], {}).get("family") == r["family_true"] for r in valid)
    task = sum(got.get(r["arxiv_id"], {}).get("task") == r["task_true"] for r in valid)
    both = sum(got.get(r["arxiv_id"], {}).get("family") == r["family_true"]
               and got.get(r["arxiv_id"], {}).get("task") == r["task_true"] for r in valid)
    bleed_true = {r["arxiv_id"] for r in rows if r["family_true"] == "bleed"}
    flagged = {i for i, d in got.items() if d.get("off_topic") in (True, "true")}
    miss = len(rows) - len(got)
    print(f"\nMODEL {model}   (n={len(valid)} scored, {miss} unanswered)")
    print(f"  family {fam}/{len(valid)} = {fam/len(valid):.1%}")
    print(f"  task   {task}/{len(valid)} = {task/len(valid):.1%}")
    print(f"  both   {both}/{len(valid)} = {both/len(valid):.1%}")
    print(f"  off_topic: flagged {len(flagged)}, true bleed {len(bleed_true)}, "
          f"caught {len(flagged & bleed_true)}")
    for axis, key in (("task", "task_true"), ("family", "family_true")):
        print(f"  per-class recall ({axis}):")
        classes = sorted({r[key] for r in valid})
        for c in classes:
            sub = [r for r in valid if r[key] == c]
            hit = sum(got.get(r["arxiv_id"], {}).get(axis) == c for r in sub)
            print(f"    {c:17s} {hit}/{len(sub)} = {hit/len(sub):.0%}")
    print("  top task confusions:",
          Counter((got.get(r["arxiv_id"], {}).get("task"), r["task_true"])
                  for r in valid if got.get(r["arxiv_id"], {}).get("task") != r["task_true"]).most_common(6))
    print("  top family confusions:",
          Counter((got.get(r["arxiv_id"], {}).get("family"), r["family_true"])
                  for r in valid if got.get(r["arxiv_id"], {}).get("family") != r["family_true"]).most_common(6))

def label_corpus(model, key, workers, limit):
    cache = {}
    if CACHE.exists():
        for line in CACHE.read_text().splitlines():
            if line.strip():
                d = json.loads(line); cache[d["arxiv_id"]] = d
    rows = [{"arxiv_id": r["arxiv_id"], "title": r["title"], "abstract": r["summary"]}
            for r in csv.DictReader(open(CORPUS)) if r["arxiv_id"] not in cache]
    if limit: rows = rows[:limit]
    print(f"{len(cache)} cached; labelling {len(rows)} with {model}")
    got = run(rows, model, key, workers)
    with open(CACHE, "a") as f:
        for aid, d in got.items():
            d["arxiv_id"] = aid; d["model"] = model
            f.write(json.dumps(d) + "\n")
    print(f"wrote {len(got)} labels to {CACHE}")

def apply_labels():
    cache = {}
    for line in CACHE.read_text().splitlines():
        if line.strip():
            d = json.loads(line); cache[d["arxiv_id"]] = d
    rows = list(csv.DictReader(open(CORPUS)))
    fields = list(rows[0].keys())
    for c in ("family_rule", "task_rule", "ai_method_rule", "off_topic", "label_source"):
        if c not in fields: fields.append(c)
    FAM = {"conv","cuprate","febased","nickelate","unconv_other","lowd","topo","device","general"}
    TSK = {"theory","abinitio","discovery","synthesis","characterization"}
    AIM = {"surrogate","gnn_potential","generative","llm","nqs","autonomous_exp","none"}
    n_llm = n_kept = 0
    for r in rows:
        r.setdefault("family_rule", r["family"]); r.setdefault("task_rule", r["task"])
        r.setdefault("ai_method_rule", r["ai_method"])
        r["family_rule"], r["task_rule"], r["ai_method_rule"] = r["family"], r["task"], r["ai_method"]
        d = cache.get(r["arxiv_id"])
        if not d: r["off_topic"], r["label_source"] = "", "rule"; n_kept += 1; continue
        r["off_topic"] = "true" if d.get("off_topic") in (True, "true") else "false"
        f, t, a = d.get("family"), d.get("task"), d.get("ai_method")
        r["family"] = f if f in FAM else r["family_rule"]
        r["task"] = t if t in TSK else r["task_rule"]
        r["ai_method"] = a if a in AIM else r["ai_method_rule"]
        r["label_source"] = "llm"; n_llm += 1
    with open(CORPUS, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    print(f"applied LLM labels to {n_llm} rows; {n_kept} fell back to rules")
    print("family:", Counter(r["family"] for r in rows).most_common())
    print("task:  ", Counter(r["task"] for r in rows).most_common())
    print("ai:    ", Counter(r["ai_method"] for r in rows).most_common())
    print("off_topic:", Counter(r["off_topic"] for r in rows).most_common())

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="qwen/qwen3-235b-a22b-2507")
    p.add_argument("--benchmark", action="store_true")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--limit", type=int); p.add_argument("--workers", type=int, default=8)
    p.add_argument("--n", type=int, default=150)
    a = p.parse_args()
    if a.apply: return apply_labels()
    key = api_key()
    if a.benchmark: return benchmark(a.model, key, a.workers, a.n)
    label_corpus(a.model, key, a.workers, a.limit)

if __name__ == "__main__":
    main()
