#!/usr/bin/env python3
"""Generate arXiv submission metadata FROM main.md so it cannot drift.

Hand-maintained submission metadata goes stale silently, because nothing renders it
until submission day. Re-run this after any title, author or abstract edit.

Usage: python draft/scripts/build_arxiv_meta.py
"""
import re
from pathlib import Path

DRAFT = Path(__file__).resolve().parents[1]
OUT = DRAFT / "arxiv_meta"
PRIMARY = "cond-mat.supr-con"
CROSS = ["cs.LG", "cond-mat.mtrl-sci"]
REPO = "https://github.com/deepgrounding/superconductivity-ai-survey"
AUTHORS_ARXIV = "Mingguang Chen (DeepGrounding)"   # arXiv field syntax, not the byline

def main():
    md = (DRAFT / "main.md").read_text()
    OUT.mkdir(parents=True, exist_ok=True)
    title = re.search(r'^title:\s*"(.+?)"\s*$', md, re.M).group(1)
    ab = " ".join(re.search(r"^abstract: \|\n((?:  .*\n|\n)+)", md, re.M).group(1).split())
    if any(c in ab for c in "*`["):
        raise SystemExit("abstract contains markdown; arXiv publishes it literally")
    if len(ab) > 1920:
        raise SystemExit(f"abstract is {len(ab)} chars; arXiv's cap is 1920")
    pdf = DRAFT / "latex" / "main.pdf"
    pages = ""
    if pdf.exists():
        import subprocess
        info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
        m = re.search(r"^Pages:\s*(\d+)", info, re.M)
        pages = m.group(1) if m else ""
    (OUT / "title.txt").write_text(title + "\n")
    (OUT / "abstract_plaintext.txt").write_text(ab + "\n")
    (OUT / "authors_arxiv_field.txt").write_text(AUTHORS_ARXIV + "\n")
    (OUT / "comments.txt").write_text(
        f"{pages} pages, 5 figures, 1 table. Corpus, labels, validation sets and build "
        f"scripts: {REPO}\n")
    (OUT / "README.md").write_text(f"""# arXiv submission metadata

GENERATED from `draft/main.md` by `draft/scripts/build_arxiv_meta.py`. Do not
hand-maintain; regenerate after ANY title, author or abstract edit.

| arXiv form field | file |
|---|---|
| Title | `title.txt` |
| Authors | `authors_arxiv_field.txt` -- arXiv field syntax, NOT the manuscript byline |
| Abstract | `abstract_plaintext.txt` ({len(ab)} of 1920 characters) |
| Primary category | `{PRIMARY}` |
| Cross-lists | {", ".join(f"`{c}`" for c in CROSS)} |
| Comments | `comments.txt` |

Upload `draft/sc_survey_overleaf.zip` as the source: `main.tex` sits at the archive
root, which arXiv requires. Do NOT upload the PDF -- this is a TeX-authored paper.
Do NOT upload `sc_survey_overleaf_noauthor.zip`; that is the anonymous review copy.

The abstract is close to arXiv's character cap. This script refuses to write if an
edit pushes it over, so run it before every submission attempt.
""")
    print(f"wrote {OUT}/  (abstract {len(ab)}/1920 chars, {pages} pages)")

if __name__ == "__main__":
    main()
