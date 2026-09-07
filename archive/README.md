# Archive

Superseded material. Kept, not deleted, so the history is inspectable — but nothing
here should be used.

| Item | What it is | Why it is dead |
|---|---|---|
| `llm_labels_v1_pre_boundary_prompt.jsonl` | The first full-corpus label pass. | **Do not use.** It was produced before the labelling prompt gained explicit synthesis-vs-characterization and discovery-vs-ab-initio boundary rules. Scoring it against `artifacts/label_truth.csv` gives different, worse numbers than the ones the paper reports, and it would look like a legitimate label set. The live labels are `artifacts/llm_labels.jsonl`. |
