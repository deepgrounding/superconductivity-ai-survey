#!/usr/bin/env python3
"""Classify the seed corpus into the paper's two-axis taxonomy (v1).

  family (axis 1, research object): conv cuprate febased nickelate unconv_other
                                    lowd topo device general
  task   (axis 2, MODE OF INQUIRY): theory abinitio discovery synthesis
                                    characterization
         (application was removed: it mixed mode with purpose; device context
          now lives on the family axis)
  ai_method (lens, AI-related rows only): surrogate gnn_potential generative
                                          llm nqs autonomous_exp none

Method: weighted keyword scoring on title (x3) + abstract (x1) per axis;
argmax wins, ties broken by the priority order of the rule lists; a row with
no hits on an axis falls to `general` / `theory`. OVERRIDES (by arXiv id)
beat everything — use them for cited papers the rules misplace.

Reads  artifacts/sc_seed.csv (+ sc_seed_clusters.csv for provenance) and, when it
exists, the FROZEN artifacts/sc_supplement.csv, which is re-labelled with the same
rules and concatenated. Freezing the supplement makes this script deterministic:
rerunning it no longer drops supplement rows nor re-hits the arXiv API, so the
counts quoted in the paper stay stable.
Writes artifacts/sc_corpus_v1.csv
"""
import csv, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "artifacts" / "sc_seed.csv"
CLUST = ROOT / "artifacts" / "sc_seed_clusters.csv"
OUT = ROOT / "artifacts" / "sc_corpus_v1.csv"
SUPP = ROOT / "artifacts" / "sc_supplement.csv"
WINDOW_START = "2021-09-01"

def R(p): return re.compile(p, re.I)

# ---------------- axis 1: family (priority order = list order) ----------------
FAMILY = [
    ("nickelate", R(r"nickelate|La_?\$?_?\{?3\}?\$?Ni_?\$?_?\{?2\}?\$?O_?\$?_?\{?7|La3Ni2O7|La4Ni3O10|LaNiO_?\$?_?\{?2|NdNiO_?\$?_?\{?2|PrNiO2|"
                    r"infinite.layer nickel|Ruddlesden.Popper nickel|bilayer nickel|trilayer nickel|Ni_?\$?_?\{?2\}?\$?O_?\$?_?\{?7|NiO_?2\b")),
    ("cuprate", R(r"cuprate|YBa_?\$?_?\{?2\}?\$?Cu|YBCO|Bi_?\$?_?\{?2\}?\$?Sr_?\$?_?\{?2\}?\$?Ca|BSCCO|Bi-?2212|Bi-?2201|La_?\$?_?\{?2-x\}?\$?Sr_?xCuO|LSCO|LBCO|"
                  r"HgBa_?\$?_?\{?2|Hg-?1223|Hg-?1201|Tl_?\$?_?\{?2\}?\$?Ba|Nd_?\$?_?\{?2-x\}?\$?Ce_?xCuO|NCCO|CuO_?\$?_?\{?2\}? plane|Ba_?2CuO|CuO2|pseudogap|stripe order in La")),
    ("febased", R(r"iron.based|iron.pnictide|iron.chalcogenide|iron.selenide|pnictide|FeSe|FeTe|Fe\(Se|Fe\(Te|BaFe_?\$?_?\{?2\}?\$?As|Ba_?\$?_?\{?1-x\}?\$?K_?xFe|"
                  r"LiFeAs|NaFeAs|LaFeAsO|LaOFeAs|KFe_?\$?_?\{?2\}?\$?As|CaKFe_?4As_?4|Fe_?\$?_?\{?1\+y\}?\$?Te|SmFeAsO|RbFe2As2|CsFe2As2|FeAs layer")),
    ("unconv_other", R(r"heavy.fermion|UTe_?\$?_?\{?2|CeCoIn_?\$?_?\{?5|CeRhIn_?5|CeIrIn5|UPt_?3|URu_?2Si_?2|UGe_?2|URhGe|UCoGe|UBe13|CePt_?3Si|CeCu2Si2|PuCoGa5|"
                       r"Sr_?\$?_?\{?2\}?\$?RuO_?\$?_?\{?4|ruthenate|organic superconduct|BEDT|\(TMTSF\)|κ-\(|kappa-\(|K_?2Cr_?3As_?3|Cr_?3As_?3|CrAs|MnP\b|"
                       r"Kondo|noncentrosymmetric|non-centrosymmetric|f-electron|uranium.based|cerium.based|4f|5f|CeSb|YbRh|LaPt3P|Ce\w+In5")),
    ("lowd", R(r"twisted|moir[eé]|magic.angle|graphene|kagome|AV_?\$?_?\{?3\}?\$?Sb_?\$?_?\{?5|CsV_?\$?_?\{?3\}?\$?Sb_?\$?_?\{?5|KV_?3Sb_?5|RbV_?3Sb_?5|"
                r"NbSe_?\$?_?\{?2|TaS_?\$?_?\{?2|TaSe_?2|MoS_?2|WTe_?2|MoTe_?2|PdTe_?2|transition.metal dichalcogenide|TMDC?\b|monolayer|bilayer|few.layer|"
                r"two.dimensional superconduct|2D superconduct|interface superconduct|LaAlO_?\$?_?\{?3\}?\$?/SrTiO|LAO/STO|KTaO_?3|KTO\b|SrTiO_?3 interface|"
                r"Ising superconduct|van der Waals|vdW|rhombohedral|Bernal|quantum well|ultrathin|atomically thin|nanowire superconduct|1D superconduct|one.dimensional superconduct")),
    ("topo", R(r"topological superconduct|Majorana|Kitaev|non.Abelian|parafermion|higher.order topolog|Weyl superconduct|Dirac superconduct|chiral p.wave|p\+ip|"
               r"topological (phase|order|invariant|insulator|crystalline|nodal|semimetal|transition)|Bogoliubov Fermi surface|braiding|anyon|Fu.Kane|proximitized|"
               r"proximity.induced|superconductor.semiconductor|semiconductor.superconductor|InAs|InSb|nanowire.*(Majorana|zero.bias)|zero.bias (peak|conductance)|"
               r"skyrmion|Yu.Shiba.Rusinov|YSR|Shiba|magnet.superconductor hybrid|altermagnet")),
    ("device", R(r"qubit|transmon|fluxonium|SQUID|single.photon detector|SNSPD|nanowire detector|kinetic inductance detector|MKID|bolometer|transition.edge sensor|\bTES\b|"
                 r"parametric amplifier|resonator|coplanar waveguide|superconducting (circuit|electronics|digital|logic|cable|magnet|wire|tape|coil|cavity|accelerator|quantum computer|processor|"
                 r"nanowire|microwave|device|sensor|memory|detector|spintronic|neuromorphic|electronic|radio.frequency|RF |strand|conductor)|SRF\b|RF cavit|accelerating cavit|"
                 r"coated conductor|REBCO|Bi-?2223|Nb_?3Sn|NbTi|Nb-Ti|MgB_?2 (wire|tape|cable|coil)|fault current limiter|tokamak|fusion (magnet|reactor)|MRI|NMR magnet|"
                 r"cryogenic (electronics|memory|computing)|SFQ|RSFQ|AQFP|Josephson (junction array|parametric|traveling|mixer|voltage standard|logic|memory|diode circuit)|"
                 r"quantum (computing|processor|error correction|gate|annealer)|gate fidelity|readout|decoherence|two.level system|TLS\b|dielectric loss|quasiparticle poisoning|"
                 r"circuit QED|cQED|Purcell|dilution refrigerator|cryostat|superconducting radio|niobium (cavity|film)|Nb (film|cavit)|NbN|NbTiN|TiN film|WSi|MoSi|"
                 r"power (transmission|cable|grid|application)|current lead|persistent current switch|levitation|maglev|motor|generator|transformer")),
    ("conv", R(r"hydride|\bH_?\$?_?\{?3\}?\$?S\b|LaH_?\$?_?\{?10|\bYH_?\$?_?\{?[69]\b|\bCaH_?6|\bScH|\bCeH_?9|superhydride|clathrate|hydrogen.rich|metallic hydrogen|polyhydride|"
               r"MgB_?\$?_?\{?2|Nb_?3Sn|Nb_?3Ge|\bV_?3Si\b|\bA15\b|elemental superconduct|niobium|\bNb\b|\bNbN\b|\bNbTiN\b|\bTiN\b|\bTaN\b|\bZrN\b|\bMoN\b|"
               r"electron.phonon coupling|phonon.mediated superconduct|Eliashberg|McMillan|Allen.Dynes|conventional (superconductor|superconductivity|phonon|BCS)|"
               r"\bboride|\bcarbide|\bnitride|Laves phase|high.entropy alloy|\bHEA\b|amorphous superconduct|granular superconduct|"
               r"Ba_?\$?_?\{?1-x\}?\$?K_?xBiO|bismuthate|BKBO|fulleride|\bC_?\{?60\b|graphite intercalation|\bCaC_?6|borocarbide|YNi_?2B_?2C|LuNi2B2C|"
               r"\bMoB_?2|\bWB_?2|\bNbC\b|\bTaC\b|\bMo_?2C\b|\bNb_?2C\b|MXene|\bPb (film|island|monolayer)|aluminum film|\bAl film|\bSn film|indium film|\bTa film|\bRe film|"
               r"LiTi_?2O_?4|Ti_?4O_?7|Nb.doped SrTiO|SrTiO_?3 (bulk|superconduct)|\bKTaO|\bPbTe\b|\bSnTe\b|Cu_?xBi_?2Se_?3|Sr_?xBi_?2Se_?3|"
               r"(binary|ternary|intermetallic|Heusler|half.Heusler|skutterudite|Zintl|sigma.phase|Chevrel|pyrochlore|β-pyrochlore|antiperovskite|silicide|germanide|stannide) (superconduct|compound)")),
]
# generic 'device' words are noisy; the family scorer weights the specific tokens higher via a second, stricter pattern
DEVICE_STRONG = R(r"qubit|transmon|fluxonium|SQUID|SNSPD|MKID|bolometer|parametric amplifier|coplanar|SRF\b|RF cavit|coated conductor|REBCO|Nb_?3Sn|NbTi\b|fault current|"
                  r"tokamak|fusion (magnet|reactor)|SFQ|RSFQ|AQFP|quantum (computing|processor|error correction|annealer)|gate fidelity|readout|circuit QED|cQED|"
                  r"cryogenic (electronics|memory)|power (transmission|cable|grid)|maglev|current lead|superconducting (circuit|electronics|digital|logic|cable|magnet|wire|tape|coil|cavity|accelerator|quantum computer|processor|nanowire|detector|sensor|memory)")

# ---------------- axis 2: task (priority order = list order) ----------------
TASK = [
    ("discovery", R(r"machine.learn|deep.learn|neural network|artificial intelligence|\bAI\b|data.driven|materials informatics|high.throughput|screen(ing|ed)|database|"
                    r"generative|inverse design|random forest|gradient boost|XGBoost|Gaussian process|Bayesian optimi|active learning|symbolic regression|language model|LLM|"
                    r"new superconductor|novel superconductor|discover|we report (the )?(discovery|observation of )?superconductivity in|superconductivity in (a )?(new|novel)|"
                    r"^Superconductivity in |^Discovery of|^Emergence of superconductivity|^Observation of superconductivity|^Pressure.induced superconductivity in|"
                    r"^Superconductivity (up to|above|at|near|with|and) |search for (new )?superconduct|candidate superconductor|predicted? (to be )?(a )?(new )?superconductor|"
                    r"prediction of (new |novel |high.T_?c )?superconduct|design(ing)? (of )?(new |novel )?(high.T_?c )?superconductor|room.temperature superconduct|"
                    r"family of superconductor|new family|structure (search|prediction)|USPEX|CALYPSO|AIRSS|evolutionary (algorithm|search|structure)|crystal structure prediction|"
                    r"composition space|chemical space|materials (discovery|design|genome)|T_?c prediction|predict(ing|ion of)? (the )?(critical temperature|T_?c)")),
    ("abinitio", R(r"first.principles|ab.initio|density.functional|\bDFT\b|DFT\+U|\bDFPT\b|Wannier|electron.phonon coupling (constant|strength|calculation)|Eliashberg (equation|calculation|theory|function)|"
                   r"phonon (dispersion|spectrum|spectra|calculation)|Migdal.Eliashberg|Allen.Dynes|McMillan|SCDFT|superconducting density functional|EPW\b|Quantum ESPRESSO|VASP|"
                   r"anisotropic Eliashberg|electronic structure calculation|band structure calculation|GW\b|hybrid functional|Fermi surface nesting|calculated (T_?c|critical temperature|electron.phonon)|"
                   r"we (calculate|compute) (the )?(electron.phonon|T_?c|critical temperature|superconducting)|DFT\+DMFT|LDA\+DMFT|molecular dynamics|MD simulation|anharmonic|SSCHA|"
                   r"stochastic self.consistent harmonic|enthalpy|formation energy|dynamically stable|convex hull|phonon.mediated superconductivity in|λ\s*=|lambda\s*=|coupling constant")),
    ("synthesis", R(r"thin.film|films? (grown|growth|deposit|prepared|fabricat|synthes)|epitax|molecular.beam epitaxy|\bMBE\b|pulsed.laser deposition|\bPLD\b|sputter|atomic layer deposition|"
                    r"single.crystal growth|crystal growth|crystals? (were|was) grown|flux method|self.flux|floating zone|Bridgman|Czochralski|chemical vapor|CVD|"
                    r"synthes|topotactic|hydrogen reduction|CaH_?2|soft.chemistry|oxygen (reduction|annealing|content control)|high.pressure synthesis|"
                    r"annealing|anneal|fabricat|sample (preparation|quality|synthesis)|substrate|strain engineering|epitaxial strain|superlattice|heterostructure growth|"
                    r"intercalat|ionic gating|ionic liquid|electrochemical|electrostatic gating|gate.tun|protonat|hydrogenat|doping (series|study|dependence)|"
                    r"chemical substitution|substituted|solid.state reaction|arc.melt|powder|polycrystalline sample|nanoparticle|nanocrystal|exfoliat|stacking (sequence|order|fault)|dry.transfer")),
    ("characterization", R(r"ARPES|photoemission|scanning tunneling|\bSTM\b|\bSTS\b|\bSTM/STS\b|neutron|μSR|muSR|muon|\bNMR\b|nuclear (magnetic|quadrupole)|NQR|Raman|optical conductivity|"
                           r"terahertz|THz|infrared|ellipsometry|specific heat|heat capacity|penetration depth|magnetotransport|transport measurement|resistivity|susceptibility|magnetization|"
                           r"thermal (conductivity|transport|Hall)|Hall (effect|coefficient|measurement)|Seebeck|Nernst|thermopower|x.ray|XRD|diffraction|RIXS|EELS|XAS|XPS|XMCD|"
                           r"point.contact|tunneling spectroscop|Andreev reflection spectroscop|quantum oscillation|de Haas|Shubnikov|torque|upper critical field|H_?c2|H_?c1|"
                           r"measurement|we measure|measured|we observe|observed|experimental(ly)? (evidence|study|investigation|observation|signature|realization)|"
                           r"microscop|spectroscop|imaging|magnetic force|MFM|SQUID microscop|Kerr|ultrafast|pump.probe|time.resolved|nonlinear optical|second harmonic|"
                           r"transport propert|magnetic propert|thermodynamic (propert|measurement|evidence)|ultrasound|dilatometry|thermal expansion|Mössbauer|\bESR\b|\bEPR\b|Knight shift|spin.lattice relaxation|"
                           r"experimental (data|results|observation|study|investigation|realization|evidence|signature|setup|technique|probe)|experimentally (observe|measure|demonstrate|realize|confirm|detect)|"
                           r"\bsamples?\b|single.crystals?|specimen|as.grown|our data|error bars|beamline|synchrotron|cryostat|dilution refrigerator|"
                           r"we (find|observe|report|show|demonstrate|identify|reveal|present) (clear |direct |strong |the first |unambiguous )?(experimental |spectroscopic |transport |thermodynamic )?(evidence|signature|observation)")),
    ("theory", R(r"theor|analytic|Hamiltonian|mean.field|Ginzburg.Landau|Bogoliubov|\bBdG\b|Hubbard|\bt.J\b|Kondo lattice|Anderson (model|localization)|Monte Carlo|DMRG|tensor network|"
                 r"renormalization group|\bfRG\b|DMFT|dynamical mean.field|field theor|effective (theory|action|model|Hamiltonian)|tight.binding|gap equation|pairing (symmetry|mechanism|instability|glue)|"
                 r"random phase approximation|\bRPA\b|spin.fluctuation (theory|mediated|exchange)|holograph|lattice model|toy model|minimal model|microscopic (model|theory)|phenomenological (model|theory)|"
                 r"we (derive|argue|propose|predict|show analytically|solve|formulate|develop a (theory|model|framework))|Green.s function|self.energy|vertex correction|diagrammatic|perturbation theory|"
                 r"exact diagonalization|variational|quantum Monte Carlo|\bQMC\b|numerical(ly)? (solv|simulat|stud|calculat)|simulation|semiclassical|quasiclassical|Usadel|Eilenberger|"
                 r"symmetry (analysis|classification)|group.theoretical|topological invariant|Berry (phase|curvature)|quantum geometry|quantum metric|superfluid (weight|stiffness)|"
                 r"collective mode|Higgs mode|Leggett mode|Nambu.Goldstone|critical exponent|scaling theory|universality class|BEC.BCS|odd.frequency|"
                 r"Landau (theory|level|free energy)|free energy functional|Eliashberg theory|strong.coupling theory|weak.coupling|Cooper (problem|instability)|"
                 r"we (study|investigate|consider|analyze|examine) (a |the )?(model|theory|Hamiltonian|lattice|system of|problem)|within (the )?(framework|mean.field|BCS|Eliashberg|Ginzburg)|"
                 r"analytical (solution|expression|result)|closed.form|exactly solvable|Bethe ansatz|bosonization|conformal|Chern.Simons|gauge theory|"
                 r"master equation|Lindblad|Floquet|Keldysh|nonequilibrium Green|Boltzmann equation|kinetic equation|hydrodynamic|Schwinger|path integral|"
                 r"Ising model|XY model|spin model|Heisenberg model|BCS.BEC|Kitaev model|Su.Schrieffer|SSH model|Haldane|Hofstadter|Chern (number|insulator)|Z_?2 invariant")),
]

AI_METHOD = [
    ("nqs", R(r"neural.network quantum state|neural quantum state|\bNQS\b|neural.network (wave ?function|ansatz)|neural.network variational|restricted Boltzmann|RBM ansatz")),
    ("llm", R(r"large language model|\bLLMs?\b|\bGPT-?\d|language model|ChatGPT|agentic|LLM.based agent|text.mining|natural language processing|\bNLP\b")),
    ("generative", R(r"generative (model|adversarial|design|AI|framework|approach)|diffusion model|variational autoencoder|\bVAE\b|\bGANs?\b|flow matching|normalizing flow|inverse design|"
                     r"MatterGen|CDVAE|DiffCSP|crystal generation|de novo (design|generation)|conditional generation")),
    ("gnn_potential", R(r"graph neural|\bGNNs?\b|graph (convolution|network|attention)|message passing|interatomic potential|machine.learn(ed|ing) (potential|force field)|MLIP|MLFF|"
                        r"\bMACE\b|CHGNet|M3GNet|MatterSim|MEGNet|CGCNN|ALIGNN|SchNet|NequIP|Allegro|equivariant (neural|network|graph|model)|universal (potential|force field)|GNoME|foundation (model|potential)|"
                        r"neural network potential|Behler.Parrinello|moment tensor potential|Gaussian approximation potential|DeePMD|deep potential")),
    ("autonomous_exp", R(r"autonomous (lab|experiment|synthesis|discovery|research|workflow|material)|self.driving lab|closed.loop|robotic|active learning|Bayesian optimi|"
                         r"experimental design|adaptive (sampling|experiment)|human.in.the.loop|automated (synthesis|experiment|characterization|lab)")),
    ("surrogate", R(r"machine.learn|deep.learn|neural network|artificial intelligence|\bAI\b|random forest|gradient boost|XGBoost|LightGBM|CatBoost|support vector|kernel ridge|Gaussian process regression|"
                    r"symbolic regression|convolutional neural|\bCNN\b|\bLSTM\b|transformer[- ](model|based|architecture|network)|attention mechanism|data.driven (model|approach|prediction|discovery)|materials informatics|"
                    r"supervised learning|unsupervised learning|classifier|regression model|feature (importance|engineering|selection)|\bSHAP\b|cross.validation|training (set|data)|test set|"
                    r"predictive model|surrogate model|dimensionality reduction|clustering algorithm|principal component|autoencoder|reinforcement learning|Q.learning|"
                    r"compressed sensing|SISSO|Bayesian (inference|neural)|kriging|Hamiltonian learning|neural.network (based|approach|model|potential|fit|reconstruction)")),
]
AI_HARD_GUARD = R(r"neural network|machine.learn|deep.learn|\bAI[- ](driven|assisted|based|guided|enabled|for|accelerated)|artificial intelligence|language model|\bLLMs?\b|graph neural|\bGNNs?\b|"
                  r"generative (model|adversarial|AI|design)|diffusion model|autoencoder|random forest|gradient boost|XGBoost|Gaussian process regression|Bayesian optimi|active learning|"
                  r"symbolic regression|interatomic potential|MLIP|MLFF|\bMACE\b|CHGNet|M3GNet|MatterSim|CGCNN|ALIGNN|MEGNet|GNoME|reinforcement learning|transformer[- ](model|based|architecture|network)|"
                  r"convolutional neural|autonomous (lab|experiment|synthesis|discovery)|self.driving lab|materials informatics|SISSO|equivariant (neural|network|graph|model)|foundation model|"
                  r"neural quantum|neural.network quantum|\bNQS\b|Boltzmann machine|kernel ridge|support vector (machine|regression)|supervised learning|unsupervised learning|"
                  r"\bSHAP\b|feature importance|training (set|data)|test set|cross.validation|surrogate model|predictive model|data.driven (discovery|prediction|model|framework|search|screening)")

# explicit overrides: (family, task) or None to keep one axis; keyed by arXiv id
OVERRIDES = {
    # "2307.12008": ("conv", "discovery"),   # LK-99 example placeholder — fill as cited papers demand
}

def score(rules, title, abstract):
    best, bestv = None, 0
    for i, (lab, rx) in enumerate(rules):
        v = 3 * len(rx.findall(title)) + len(rx.findall(abstract))
        if v > bestv: best, bestv = lab, v
    return best, bestv

def classify(row):
    aid = re.sub(r"v\d+$", "", (row.get("arxiv_id") or "").strip())
    title = row.get("title") or ""; abstract = (row.get("summary") or "")[:1500]
    fam, fv = score(FAMILY, title, abstract)
    # 'device' only wins on a strong token; generic hits (film, microwave, electronic) fall through
    if fam == "device" and not DEVICE_STRONG.search(title + " " + abstract):
        alt = [(l, r) for l, r in FAMILY if l != "device"]
        fam, fv = score(alt, title, abstract)
    if fam is None: fam = "general"
    task, tv = score(TASK, title, abstract)
    if task is None: task = "theory"
    if aid in OVERRIDES:
        of, ot = OVERRIDES[aid]; fam, task = of or fam, ot or task
    return fam, task

def ai_method(row):
    txt = (row.get("title") or "") + " " + (row.get("summary") or "")
    if not AI_HARD_GUARD.search(txt): return "none"
    if re.search(r"neuromorphic|synaptic|spiking neural|neuron circuit|hardware neural|superconducting neural network|neural network (implementation|hardware|circuit)", txt, re.I) \
            and not re.search(r"machine.learn|deep.learn|train(ed|ing) (a |the )?(model|network)|we train", txt, re.I): return "none"
    for lab, rx in AI_METHOD:
        if rx.search(txt): return lab
    return "surrogate"

def main():
    rows = list(csv.DictReader(open(SEED)))
    clusters = {}
    if CLUST.exists():
        clusters = {r["arxiv_id"]: r["cluster"] for r in csv.DictReader(open(CLUST))}
    out = []
    for r in rows:
        f, t = classify(r)
        r["cluster"] = clusters.get(r["arxiv_id"], "")
        r["family"], r["task"], r["ai_method"] = f, t, ai_method(r)
        r["source"] = "seed"; out.append(r)
    n_seed = len(out)
    if SUPP.exists():                       # frozen supplement, re-labelled with the same rules
        for r in csv.DictReader(open(SUPP)):
            f, t = classify(r)
            # T2 rows carry a hand-assigned family/task from the harvest query; keep it
            if r.get("source") == "supplement_t2" and r.get("family"):
                f, t = r["family"], r["task"]
            r["family"], r["task"], r["ai_method"] = f, t, ai_method(r)
            out.append(r)
        print(f"(concatenated {len(out)-n_seed} frozen supplement rows)")
    fields = list(out[0].keys())
    for r in out:                            # enrichment columns exist only after enrich_openalex.py
        for k in r:
            if k not in fields: fields.append(k)
    for r in out:
        for k in fields: r.setdefault(k, "")
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(out)
    fam = Counter(r["family"] for r in out); task = Counter(r["task"] for r in out)
    print("=== family ==="); [print(f"  {k:13s} {v:5d}") for k, v in fam.most_common()]
    print("=== task ==="); [print(f"  {k:16s} {v:5d}") for k, v in task.most_common()]
    ai = Counter(r["ai_method"] for r in out if r["ai_method"] != "none")
    print(f"=== ai_method (n={sum(ai.values())}) ==="); [print(f"  {k:14s} {v:4d}") for k, v in ai.most_common()]
    print("=== family x task ===")
    fams = [k for k, _ in fam.most_common()]; tasks = ["theory", "abinitio", "discovery", "synthesis", "characterization", "application"]
    print("  " + " " * 13 + "".join(f"{t[:8]:>9s}" for t in tasks))
    ct = Counter((r["family"], r["task"]) for r in out)
    for f in fams: print(f"  {f:13s}" + "".join(f"{ct[(f, t)]:9d}" for t in tasks))
    import random; random.seed(1)
    print("\n=== samples per family ===")
    for f in fams:
        pool = [r for r in out if r["family"] == f]
        for r in random.sample(pool, min(4, len(pool))): print(f"  [{f}/{r['task']}] {r['title'][:95]}")
    print("\n=== samples per task ===")
    for t in tasks:
        pool = [r for r in out if r["task"] == t]
        for r in random.sample(pool, min(4, len(pool))): print(f"  [{r['family']}/{t}] {r['title'][:95]}")
    print("\n=== AI samples ===")
    pool = [r for r in out if r["ai_method"] != "none"]
    for r in random.sample(pool, min(15, len(pool))): print(f"  [{r['ai_method']}] {r['title'][:95]}")
    print(f"\nwrote {OUT} ({len(out)} rows)")

if __name__ == "__main__":
    main()
