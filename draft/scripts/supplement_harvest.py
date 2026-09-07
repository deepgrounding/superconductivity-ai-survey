#!/usr/bin/env python3
"""Targeted supplemental arXiv harvest (two threads), appended to
artifacts/sc_corpus_v1.csv with source=supplement_t1 / supplement_t2.

  T1  AI/ML x superconductivity papers NOT already in the seed (i.e. not
      cross-listed to cond-mat.supr-con: typically cond-mat.mtrl-sci,
      physics.comp-ph, cs.LG primaries). Window = survey window.
  T2  AI-for-materials infrastructure the roadmap section needs (universal
      potentials, generative crystal models, autonomous labs, LLM extraction,
      neural quantum states). Not superconductivity-specific; small caps;
      family=general, task=discovery/theory/synthesis as tagged.

Both threads are RECENCY-BIASED BY CONSTRUCTION (sorted by submittedDate,
capped per query) -> exclude source!=seed from growth/trend figures.
Rows are labelled through reclassify_corpus.classify() so the whole corpus
shares one rule set; ai_method is assigned by reclassify_corpus.ai_method().

Usage: python draft/scripts/supplement_harvest.py [--dry]
"""
import argparse, csv, re, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reclassify_corpus import classify, ai_method, WINDOW_START  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "artifacts" / "sc_corpus_v1.csv"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

SC = '(all:superconductivity OR all:superconductor OR all:superconductors OR all:superconducting)'
T1 = [  # (query, cap)
    (f'all:"machine learning" AND {SC}', 200),
    (f'all:"deep learning" AND {SC}', 100),
    (f'all:"neural network" AND all:"critical temperature"', 100),
    (f'all:"graph neural network" AND {SC}', 60),
    (f'all:"generative model" AND {SC}', 60),
    (f'all:"diffusion model" AND {SC}', 40),
    (f'all:"large language model" AND {SC}', 60),
    (f'all:"language model" AND {SC}', 40),
    (f'all:"active learning" AND {SC}', 40),
    (f'all:"Bayesian optimization" AND {SC}', 40),
    (f'all:"high-throughput" AND {SC} AND all:"machine learning"', 60),
    (f'all:"interatomic potential" AND {SC}', 60),
    (f'all:"symbolic regression" AND {SC}', 30),
    (f'all:"neural quantum state" AND {SC}', 40),
    (f'all:"neural network quantum state" AND {SC}', 40),
    (f'all:"autonomous" AND all:"laboratory" AND {SC}', 30),
    (f'all:"materials informatics" AND {SC}', 40),
    (f'all:"SuperCon" AND all:database', 40),
    (f'all:"transformer" AND all:"critical temperature" AND {SC}', 30),
    (f'all:"machine learning" AND all:ARPES', 40),
    (f'all:"machine learning" AND all:"scanning tunneling" AND {SC}', 30),
    (f'all:"machine learning" AND all:"electron-phonon"', 60),
    (f'all:"machine learning" AND all:hydride AND all:pressure', 40),
    (f'all:"machine learning" AND all:"quantum Monte Carlo" AND {SC}', 30),
    (f'all:"machine learning" AND all:"superconducting qubit"', 60),
    (f'all:"reinforcement learning" AND all:"superconducting qubit"', 40),
]
T1_AI = re.compile(r"\b(machine[- ]learn|deep[- ]learn|neural network|neural[- ]quantum|graph neural|GNN|"
                   r"transformer|language model|LLM|generative|diffusion model|active learning|Bayesian optimi|"
                   r"symbolic regression|interatomic potential|random forest|gradient boost|autonomous|"
                   r"reinforcement learning|data[- ]driven|informatics|artificial intelligence|\bAI\b)", re.I)
T1_SC = re.compile(r"superconduct|critical temperature|\bT_?c\b|Cooper pair|hydride.*pressure|qubit", re.I)

T2 = [  # (query, cap, family, task)
    ('all:"universal interatomic potential" OR all:"foundation model" AND all:"interatomic"', 30, "general", "abinitio"),
    ('all:MACE AND all:"interatomic potential" AND all:"machine learning"', 20, "general", "abinitio"),
    ('all:CHGNet OR all:M3GNet OR all:MatterSim OR all:"Orb-v" OR all:"SevenNet"', 30, "general", "abinitio"),
    ('all:"crystal structure" AND all:"diffusion model" AND all:generation', 40, "general", "discovery"),
    ('all:MatterGen OR all:"CDVAE" OR all:"DiffCSP" OR all:"FlowMM"', 30, "general", "discovery"),
    ('all:"GNoME" OR (all:"graph networks" AND all:"materials exploration")', 20, "general", "discovery"),
    ('all:"autonomous laboratory" AND all:materials', 30, "general", "synthesis"),
    ('all:"self-driving lab" AND all:materials', 30, "general", "synthesis"),
    ('all:"synthesizability" AND all:"machine learning"', 30, "general", "synthesis"),
    ('all:"large language model" AND all:"materials" AND all:extraction', 30, "general", "discovery"),
    ('all:"large language model" AND all:"materials discovery"', 40, "general", "discovery"),
    ('all:"LLM agent" AND all:materials', 30, "general", "discovery"),
    ('all:"neural quantum state" AND all:"Hubbard"', 30, "general", "theory"),
    ('all:"neural network quantum state" AND all:fermion', 30, "general", "theory"),
    ('all:"machine learning" AND all:"dynamical mean-field"', 20, "general", "theory"),
    ('all:"AI for science" AND all:materials', 30, "general", "discovery"),
    ('all:"machine learning" AND all:"ARPES"', 20, "general", "characterization"),
    ('all:"machine learning" AND all:"scanning tunneling microscopy"', 30, "general", "characterization"),
]

def fetch(query, n):
    url = ("http://export.arxiv.org/api/query?search_query=" + urllib.parse.quote(query)
           + f"&start=0&max_results={n}&sortBy=submittedDate&sortOrder=descending")
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return ET.fromstring(r.read())
        except Exception as e:
            print(f"  retry {attempt+1}: {e}", file=sys.stderr); time.sleep(6 * (attempt + 1))
    print(f"  FAILED {query}", file=sys.stderr); return None

def entries(root):
    for e in root.findall("atom:entry", NS):
        aid = re.sub(r"v\d+$", "", e.find("atom:id", NS).text.split("/abs/")[-1])
        pub = e.find("atom:published", NS).text
        cats = [c.get("term") for c in e.findall("atom:category", NS)]
        prim = e.find("arxiv:primary_category", NS)
        doi = e.find("arxiv:doi", NS); jr = e.find("arxiv:journal_ref", NS)
        yield {
            "arxiv_id": aid,
            "title": re.sub(r"\s+", " ", e.find("atom:title", NS).text.strip()),
            "year": pub[:4], "pub_date": pub[:19].replace("T", " "),
            "primary_cat": prim.get("term") if prim is not None else (cats[0] if cats else ""),
            "all_cats": ";".join(cats),
            "authors": " and ".join(a.find("atom:name", NS).text.strip() for a in e.findall("atom:author", NS)),
            "doi": doi.text.strip() if doi is not None and doi.text else "",
            "journal_ref": re.sub(r"\s+", " ", jr.text.strip()) if jr is not None and jr.text else "",
            "url": f"https://arxiv.org/abs/{aid}",
            "summary": re.sub(r"\s+", " ", e.find("atom:summary", NS).text.strip()),
        }

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    rows = list(csv.DictReader(open(CORPUS)))
    fields = list(rows[0].keys())
    seen = {r["arxiv_id"] for r in rows}
    new, stats = [], []

    def add(r, source, fam=None, task=None):
        r = {**{k: "" for k in fields}, **r}
        f, t = classify(r)
        r["family"], r["task"] = (fam or f), (task or t)
        r["ai_method"] = ai_method(r)
        r["source"] = source; r["cluster"] = ""
        seen.add(r["arxiv_id"]); new.append(r)

    for q, cap in T1:
        root = fetch(q, cap); time.sleep(3)
        if root is None: continue
        n = 0
        for r in entries(root):
            if r["arxiv_id"] in seen or r["pub_date"] < WINDOW_START: continue
            txt = r["title"] + " " + r["summary"]
            if not (T1_AI.search(txt) and T1_SC.search(txt)): continue
            add(r, "supplement_t1"); n += 1
        stats.append(("T1", q[:70], n)); print(f"  T1 +{n:3d}  {q[:80]}", flush=True)

    for q, cap, fam, task in T2:
        root = fetch(q, cap); time.sleep(3)
        if root is None: continue
        n = 0
        for r in entries(root):
            if r["arxiv_id"] in seen or r["pub_date"] < WINDOW_START: continue
            add(r, "supplement_t2", fam, task); n += 1
        stats.append(("T2", q[:70], n)); print(f"  T2 +{n:3d}  {q[:80]}", flush=True)

    print(f"\n{len(new)} new rows ({Counter(r['source'] for r in new)})")
    print("family x task of new rows:")
    for (f, t), n in sorted(Counter((r["family"], r["task"]) for r in new).items()): print(f"  {f:13s} {t:16s} {n}")
    if a.dry: return
    with open(CORPUS, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=fields).writerows(new)
    print(f"appended to {CORPUS}; corpus total {len(rows)+len(new)}")

if __name__ == "__main__":
    main()
