# arXiv submission metadata

GENERATED from `draft/main.md` by `draft/scripts/build_arxiv_meta.py`. Do not
hand-maintain; regenerate after ANY title, author or abstract edit.

| arXiv form field | file |
|---|---|
| Title | `title.txt` |
| Authors | `authors_arxiv_field.txt` -- arXiv field syntax, NOT the manuscript byline |
| Abstract | `abstract_plaintext.txt` (1831 of 1920 characters) |
| Primary category | `cond-mat.mtrl-sci` |
| Cross-lists | `cond-mat.supr-con`, `cs.LG` |
| Comments | `comments.txt` |

`authors.txt` and `abstract.txt` are aliases of the two files above, written for the
submission driver, which reads those exact filenames.

Upload `draft/sc_survey_overleaf.zip` as the source: `main.tex` sits at the archive
root, which arXiv requires. Do NOT upload the PDF -- this is a TeX-authored paper.
Do NOT upload `sc_survey_overleaf_noauthor.zip`; that is the anonymous review copy.

The abstract is close to arXiv's character cap. This script refuses to write if an
edit pushes it over, so run it before every submission attempt.
