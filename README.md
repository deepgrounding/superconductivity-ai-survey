# AI for Superconductivity: A Systematic Map and Readiness Assessment

Corpus, labels and build pipeline for the survey *"AI for Superconductivity: A
Systematic Map and Readiness Assessment"* (Mingguang Chen, DeepGrounding).

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

Two different numbers exist here and they answer different questions.

**Model selection** used `--benchmark`, which re-queries a model. It is how the model
was chosen; its result depends on a run you cannot repeat.

| model | family | mode |
|---|---|---|
| keyword rules | 80.1% | 70.5%* |
| gemini-2.5-flash-lite | 82.9% | 79.5% |
| gemini-2.5-flash | 82.2% | 85.6% |
| **gemini-3.5-flash-lite** (selected) | **87.7%** | **85.6%** |

**The manuscript's reported figures** come from `--score-published`, which scores the
labels that actually ship in `artifacts/llm_labels.jsonl` against `label_truth.csv`.
Anyone with this repository reproduces them exactly:

```bash
python draft/scripts/llm_label.py --score-published
```

```
family 126/146 = 86.3%      task 127/146 = 87.0%      both 109/146 = 74.7%
per-class recall (mode): theory 57/57, characterization 47/52, ab initio 11/13,
                         synthesis 7/11, discovery 5/13
AI lens (n=120): exact 82%, precision 88%, recall 77%
```

The two sets differ by at most two papers per cell. They differ at all because the
benchmark run and the shipped labels are different invocations of the same model. The
manuscript quotes the second set, because that is the one a reader can check.

Note the denominators on the small classes: at n = 13, two papers are fifteen
percentage points. Those recall figures carry about as much information as the counts
beside them.

\* predates the removal of the `application` value from the mode axis; not a
like-for-like comparison. See the manuscript's Method section.

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

## Before submitting

Two things must be done by the author, and neither can be done from the build:

1. **Make this repository public.** The manuscript's Data availability section links
   to it, and that link currently returns 404 for anyone not signed in:
   ```bash
   gh repo edit deepgrounding/superconductivity-ai-survey --visibility public
   curl -s -o /dev/null -w '%{http_code}\n' https://github.com/deepgrounding/superconductivity-ai-survey
   ```
2. **Spot-check a slice of the labels.** The Method section discloses a single
   annotator and reports inter-pass agreement, not accuracy. Open
   `artifacts/label_truth.csv`, read some abstracts, and confirm you would have
   labelled them the same way. If you disagree materially, re-score with
   `draft/scripts/llm_label.py --benchmark` and update the reported figures.

Citation provenance is recorded in `artifacts/CITATION_AUDIT.md`; re-run the audit any
time with `python draft/scripts/audit_citations.py`.
