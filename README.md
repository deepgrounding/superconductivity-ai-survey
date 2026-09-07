# Mapping Superconductivity Research for AI

Corpus, labels and build pipeline for the survey *"Mapping Superconductivity Research
for AI: A Two-Axis Survey of 10,249 Preprints and Where Machine Learning Can Actually
Help"* (Mingguang Chen, DeepGrounding).

## What is here

| Path | Contents |
|---|---|
| `artifacts/sc_seed.csv` | Frozen systematic seed: every arXiv preprint listed under `cond-mat.supr-con` (primary or cross-list) submitted 2021-09-01 to 2026-09-07. 10,303 records with full abstracts. |
| `artifacts/raw_seed/` | Raw per-month arXiv API responses, so the harvest reproduces exactly. |
| `artifacts/sc_supplement.csv` | Frozen targeted supplement (AI × superconductivity, AI-for-materials infrastructure). Recency-biased by construction; excluded from all trend statistics. |
| `artifacts/sc_corpus_v1.csv` | Canonical labelled corpus: family, task, ai_method, off_topic, plus the superseded keyword-rule labels for provenance. |
| `artifacts/llm_labels.jsonl` | Raw language-model label cache (one JSON object per paper). |
| `artifacts/label_truth.csv` | 150-record stratified hand-labelled validation set for the two axes. |
| `artifacts/ai_label_truth.csv` | 120-record hand-labelled validation set for the AI lens (60 rule-positive, 60 rule-negative). |
| `draft/` | `main.md` (single source of truth), bibliographies, figures, scripts, and the built outputs. |

## Reproducing

```bash
PY=/path/to/python           # needs numpy, scikit-learn, matplotlib
$PY draft/scripts/harvest_seed.py         # arXiv API -> sc_seed.csv (cached per month)
$PY draft/scripts/reclassify_corpus.py    # keyword-rule labels (provenance fallback)
$PY draft/scripts/llm_label.py --model google/gemini-3.5-flash-lite
$PY draft/scripts/llm_label.py --apply
$PY draft/scripts/enrich_openalex.py      # citation counts and venues
$PY draft/scripts/build_bib.py            # references.bib for cited rows
$PY draft/scripts/build_figures.py        # Figures 2-4 and Table 1
$PY draft/scripts/build_concept_figures.py # Figures 1 and 5
```

Model selection was done by measurement, not reputation. To re-score any model against
the hand labels:

```bash
$PY draft/scripts/llm_label.py --benchmark --model <model-id>
```

`.env` (gitignored) supplies `OPENALEX_API_KEY` and `OPENROUTER_API_KEY`.

## Labelling accuracy

Agreement with the hand-labelled validation set, family / mode of inquiry:

| labels | family | mode |
|---|---|---|
| keyword rules | 80.1% | 70.5%* |
| gemini-2.5-flash-lite | 82.9% | 79.5% |
| gemini-2.5-flash | 82.2% | 85.6% |
| **gemini-3.5-flash-lite** | **85.6%** | **88.4%** |

\* predates the removal of the `application` value from the task axis; not a
like-for-like comparison. See the manuscript's Method section.

Per-class recall for the selected model: theory 96%, characterization 92%, ab initio
92%, synthesis 64%, discovery 54%. AI lens: 88% precision, 81% recall, 84% exact
agreement on method.

All hand labels were produced by a single annotator, so these are inter-pass agreement
figures rather than accuracy against an external standard.

## Building the manuscript

```bash
cd draft && cat references.bib anchors.bib > combined.bib
pandoc main.md --citeproc --bibliography=combined.bib --pdf-engine=tectonic \
  -H pdf-header.tex -V geometry:margin=1in -V fontsize=11pt -V colorlinks=true \
  -o survey_v1.pdf
python scripts/build_latex.py && (cd latex && tectonic main.tex)   # arXiv/Overleaf
python scripts/build_anon.py                                       # anonymous copies
```

See `CLAUDE.md` for pipeline ordering constraints and known gotchas.
