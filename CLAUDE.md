# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this repository is

A research survey manuscript: **a two-axis systematic map of superconductivity research (2021-09 → 2026-09) with a per-cell assessment of where AI for Science can contribute.** Target form: arXiv standalone survey, English, 10–15k words, natbib citations. Built with the `research-survey` skill pipeline (`~/.claude/skills/research-survey/`); the sibling project `../recursive_self_improvement/` is the reference implementation.

Layers:
- `artifacts/` — corpus data. `sc_seed.csv` is the **frozen** systematic seed (every arXiv paper listed under `cond-mat.supr-con`, primary or cross-list, submitted in the window; harvested month-by-month via the arXiv API, raw Atom cached in `artifacts/raw_seed/`). `sc_corpus_v1.csv` is the **canonical** corpus = seed + targeted supplement, each row tagged with the taxonomy (`family`, `task`, `ai_method`). Never hand-edit CSVs.
- `draft/` — `main.md` is the single source of truth; `anchors.bib` (hand-curated, web-verified seminal works) + `references.bib` (auto-generated, never hand-edit); `figures/`, `scripts/`, `latex/` (Overleaf/arXiv project, built by script).
- `archive/` — superseded material (`git mv`, never delete).

No application code, no tests. "Building" = compiling `main.md` with pandoc/tectonic.

## Python

Use the conda interpreter — Homebrew `python3` lacks numpy/sklearn/matplotlib:
```
PY=/opt/homebrew/Caskroom/miniconda/base/bin/python
```

## The taxonomy (v1 — must match paper sections, Table 1, figures)

Axis 1 `family` (research object): `conv` (conventional / electron-phonon incl. high-pressure hydrides), `cuprate`, `febased`, `nickelate`, `unconv_other` (heavy fermion, organic, Sr2RuO4, UTe2 …), `lowd` (2D / interface / moiré / kagome), `topo` (topological SC, Majorana), `device` (qubits, detectors, magnets, wires), `general` (cross-family theory/method).

Axis 2 `task` — **mode of inquiry**, five values: `theory`, `abinitio`, `discovery`, `synthesis`, `characterization`.

`application` was removed from this axis on 2026-09-07. It mixed *how* the work was done with *what it was for*, and that was measurably the single largest source of disagreement: characterization↔application was the top confusion for the keyword rules and for both benchmarked LLMs. Application context is now carried by the `device` family instead, so a qubit paper gets theory / synthesis / characterization like any other.

AI lens `ai_method` (only for AI-related rows): `surrogate`, `gnn_potential`, `generative`, `llm`, `nqs`, `autonomous_exp`, `none`.

**Consistency rule:** taxonomy ↔ CSV labels ↔ section structure ↔ Table 1 ↔ figures must agree at all times. When the taxonomy changes: re-classify, regenerate every figure/table, rename sections, grep prose for stale codes and counts.

## Labelling — how the taxonomy is actually assigned

Keyword rules reached only 80% (family) / 70% (task) agreement with hand labels, so labels come from an **LLM pass** (`llm_label.py`, `google/gemini-3.5-flash-lite` via OpenRouter, cached in `artifacts/llm_labels.jsonl`). The model was chosen by measured agreement against a 150-row stratified hand-labelled sample (`artifacts/label_truth.csv`), not by reputation:

| labels | family | task | both |
|---|---|---|---|
| keyword rules | 80.1% | 70.5%* | 53.4%* |
| gemini-2.5-flash-lite | 82.9% | 79.5% | 64.4% |
| gemini-2.5-flash | 82.2% | 85.6% | 69.2% |
| **gemini-3.5-flash-lite** | **87.7%** | **85.6%** | **76.0%** |

\* rule task/both figures predate the axis change; they are not directly comparable to the LLM rows.

The rule labels survive as `family_rule` / `task_rule` / `ai_method_rule` columns for provenance and disagreement analysis. `label_source` says which applied. The LLM also sets `off_topic`.

**The AI lens was validated separately** (`artifacts/ai_label_truth.csv`, 60 rule-positive + 60 rule-negative hand-labelled): the keyword guard had **77% precision** (14 false positives in 60) and **~98% recall** (1 miss in 60). Its false positives were mostly papers that merely mention ML plus off-topic rows from the AI-infrastructure thread — which is why `ai_method` also comes from the LLM pass.

Disclosure for the Method section: all hand labels were produced by **one annotator** during this pipeline; the comparison is *inter-pass agreement*, not ground-truth accuracy. The author should personally spot-check a slice before submission.

## Data pipeline — ORDER MATTERS

```bash
$PY draft/scripts/harvest_seed.py        # arXiv API -> artifacts/sc_seed.csv (frozen; cached per month, safe to rerun)
$PY draft/scripts/reclassify_corpus.py   # sc_seed.csv + FROZEN sc_supplement.csv -> sc_corpus_v1.csv (deterministic)
# supplement_harvest.py only needs re-running to GROW the supplement; its output is frozen in
# artifacts/sc_supplement.csv, which reclassify concatenates. Re-running it changes quoted counts.
$PY draft/scripts/llm_label.py --model google/gemini-3.5-flash-lite   # -> artifacts/llm_labels.jsonl (cached, resumable)
$PY draft/scripts/llm_label.py --apply   # writes family/task/ai_method/off_topic into the corpus
$PY draft/scripts/enrich_openalex.py     # adds cited_by / venue columns in place (idempotent, cached)
$PY draft/scripts/build_bib.py           # cited rows in main.md -> draft/references.bib
$PY draft/scripts/build_figures.py       # figures + Table 1 markdown
```

**Gotcha:** `reclassify_corpus.py` rebuilds `sc_corpus_v1.csv` and therefore **drops the enrichment columns** — re-run `enrich_openalex.py` (cached, fast) and `llm_label.py --apply` after it. Supplement rows are recency-biased by construction: **exclude `source != seed` from growth/trend figures**. Table 1 reports seed counts only, with supplement in its own column, so it reconciles with Figure 3.

Misclassified *cited* papers are fixed via the `OVERRIDES` dict in `reclassify_corpus.py`, never by editing the CSV.

## Manuscript build

```bash
cd draft
cat references.bib anchors.bib > combined.bib
pandoc main.md --citeproc --bibliography=combined.bib -s --embed-resources --standalone -o survey_v1.html
pandoc main.md --citeproc --bibliography=combined.bib -o survey_v1.docx
pandoc main.md --citeproc --bibliography=combined.bib --pdf-engine=tectonic -H pdf-header.tex -V geometry:margin=1in -V fontsize=11pt -V colorlinks=true -o survey_v1.pdf
$PY scripts/build_latex.py && (cd latex && tectonic main.tex)
```

Citation sanity-check before any compile (keys that would render as `??`):
```bash
$PY -c "
import re
txt=open('draft/main.md').read()
cited=set(re.findall(r'@([A-Za-z]+[0-9]{4}[A-Za-z0-9]*)',txt))
bib=open('draft/references.bib').read()+open('draft/anchors.bib').read()
keys=set(re.findall(r'@\w+\{([^,]+),',bib))
print('MISSING:',sorted(cited-keys) or 'none')"
```

## Bibliography

- `references.bib`: generated by `build_bib.py` for **cited corpus rows only** (the corpus is ~12k rows; a full bib is pointless). Keys = first-author surname + year + first title word; regenerating after metadata changes can rename keys — always rerun the sanity check.
- `anchors.bib`: hand-curated seminal works outside the window (BCS 1957, Bednorz–Müller 1986, Kamihara 2008, Drozdov 2015, LaH10 2019, Li 2019 nickelate, Cao 2018, Stanev 2018, Hamidieh 2018, …). Each entry web-verified (authors, year, venue, ID) before it goes in.

## Author block

Single author: **Mingguang Chen**, affiliation **DeepGrounding**, corresponding email **deepgroundingai@gmail.com** (matches arXiv:2609.00083, first page). Lives in `main.md` YAML and `build_latex.py`'s `AUTHOR_BLOCK` — keep in sync. Anonymous review copies strip YAML `author:`, the LaTeX `\author{}` block, and hyperref's `pdfauthor=`; verify with `pdfinfo`. Anonymous outputs are gitignored.

## Writing rules (from the skill; every one is a past incident)

Write sections from per-category dossiers, never from memory. Fact-check load-bearing claims against the full abstract in the CSV, not dossier excerpts. Check author lists before writing "et al.". No "prove / first / monotone" unless measured. Critical/diagnostic literature (data leakage in Tc regression, synthesizability critiques of generative "discoveries", LK-99 and reproducibility, hydride retractions) is a first-class thread. Numbers in abstract/intro/tables/captions/data-availability must all match.
