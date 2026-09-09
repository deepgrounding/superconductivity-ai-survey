#!/usr/bin/env python3
"""Build the Overleaf/arXiv LaTeX project from main.md.

Pipeline: pandoc (--natbib) -> post-process main.tex (heading levels,
author block, abstract env, figure captions, bibliography hookup) ->
clean references.bib for plain bibtex + pdfLaTeX -> write latex/.

Usage: python3 scripts/build_latex.py   (run from draft/)
Output: latex/{main.tex, references.bib, figures/*.png}
"""

import re
import subprocess
import shutil
from pathlib import Path

DRAFT = Path(__file__).resolve().parents[1]
LATEX = DRAFT / "latex"
(LATEX / "figures").mkdir(parents=True, exist_ok=True)

# Two authors, one shared affiliation, ONE corresponding author. Must stay in sync
# with the `author:` list in main.md and with AUTHORS_ARXIV in build_arxiv_meta.py.
# NB: no \and -- it lays the authors out in side-by-side columns and drags the shared
# affiliation under the last one. One column, comma-separated, keeps the block centred.
AUTHOR_BLOCK = r"""\author{Mingguang Chen\textsuperscript{1,$*$}, Bo Qu\textsuperscript{1}\\[6pt]
{\small \textsuperscript{1}DeepGrounding}\\[2pt]
{\small \textsuperscript{$*$}Corresponding author. Email: \href{mailto:deepgroundingai@gmail.com}{deepgroundingai@gmail.com}}}"""

# ---------- 1. pandoc ----------
subprocess.run([
    # --number-sections: the body cites "Section 2".."Section 8", so the headings
    # have to actually show those numbers.
    "pandoc", str(DRAFT / "main.md"), "-s", "--natbib", "--number-sections",
    "--bibliography", str(DRAFT / "combined.bib"),
    "-V", "documentclass=article", "-V", "fontsize=11pt",
    "-V", "geometry:margin=1in", "-V", "colorlinks=true",
    "-V", "biblio-style=unsrtnat", "-V", "natbiboptions=numbers",
    "-o", str(LATEX / "main.tex"),
], check=True)

tex = (LATEX / "main.tex").read_text()

# ---------- 2. heading levels: md '##' landed one level too deep ----------
tex = tex.replace(r"\subsubsection{", r"\XSUBSECTIONX{")
tex = tex.replace(r"\subsection{", r"\section{")
tex = tex.replace(r"\XSUBSECTIONX{", r"\subsection{")

# ---------- 3. author / date ----------
# Brace-BALANCED replacement: pandoc's \author{...} now contains nested groups
# (\textsuperscript{1,*}), and the old [^{}]* pattern silently matched nothing, so
# AUTHOR_BLOCK stopped being applied without any error. Match the real span instead.
def _replace_balanced(tex, macro, repl):
    i = tex.find(macro)
    if i < 0:
        raise SystemExit(f"no {macro}{{...}} in pandoc output -- refusing to guess")
    j = i + len(macro); depth = 0
    while j < len(tex):
        if tex[j] == "{": depth += 1
        elif tex[j] == "}":
            depth -= 1
            if depth == 0: break
        j += 1
    else:
        raise SystemExit(f"unbalanced braces after {macro}")
    return tex[:i] + repl + tex[j + 1:]

tex = _replace_balanced(tex, r"\author", AUTHOR_BLOCK)
# Date is DERIVED from main.md's YAML, never hardcoded: a hardcoded date in this
# template silently disagreed with the manuscript (it still said "July 2026" from the
# project this script was copied from) while the pandoc PDF showed the right one.
_md = (DRAFT / "main.md").read_text()
_m = re.search(r"^date:\s*(\S+)", _md, re.M)
if not _m:
    raise SystemExit("no `date:` in main.md YAML -- refusing to guess")
_iso = _m.group(1).strip().strip('"\'')
_dt = __import__("datetime").date.fromisoformat(_iso)
DATE = _dt.strftime("%d %B %Y").lstrip("0")
tex = re.sub(r"\\date\{[^}]*\}", lambda m: r"\date{" + DATE + "}", tex)

# ---------- 4. Abstract section -> abstract environment ----------
m = re.search(
    r"\\section\{Abstract\}\\label\{abstract\}\n\n(.*?)\n\n(?=\\section)",
    tex, flags=re.S)
if m:
    abstract_text = m.group(1)
    tex = tex[:m.start()] + tex[m.end():]
    tex = tex.replace(
        r"\maketitle",
        "\\maketitle\n\n\\begin{abstract}\n" + abstract_text + "\n\\end{abstract}",
        1)

# ---------- 5. figure captions: keep the manual 'Figure N:' text, drop
# LaTeX's own auto-number (md figure order is 3,1,2 so auto-numbering
# would contradict the in-text references) ----------
tex = tex.replace(
    r"\usepackage{longtable,booktabs,array}",
    "\\usepackage{longtable,booktabs,array}\n\\usepackage{caption}")
tex = re.sub(r"\\caption\{(Figure \d+:)", r"\\caption*{\1", tex)

# ---------- 6. References: drop the markdown section + provenance note,
# keep natbib's \bibliography pointing at the cleaned local bib ----------
tex = re.sub(
    r"\\section\{References\}\\label\{references\}\n\n\\emph\{.*?\}\n\n",
    "", tex, flags=re.S)
tex = re.sub(r"\\bibliography\{[^}]*\}", r"\\bibliography{references}", tex)

(LATEX / "main.tex").write_text(tex)

# ---------- 7. clean bib for plain bibtex + pdfLaTeX ----------
bib = (DRAFT / "combined.bib").read_text()
# BibTeX 0.99 (what arXiv runs) has no '%' comment syntax: a trailing provenance
# comment makes it report "You're missing a field name" and skip the whole entry.
# This pattern used to hardcode '% theme:', copied from a sibling project, while
# build_bib.py here emits '% family: ... task: ... src: ...' -- so it matched
# nothing and every annotated entry reached arXiv broken. Match the comment, not
# one project's wording, and drop the empty note field it annotated.
bib = re.sub(r"\n  note = \{\},[ \t]*%[^\n]*", "", bib)
bib = re.sub(r"[ \t]*%[^\n]*(?=\n)", "", bib)
# Duplicate keys are also fatal to BibTeX ("Repeated entry"). build_bib.py now
# skips keys defined in anchors.bib, so this is a backstop: keep the first
# definition, which is the order pandoc's citeproc resolves too.
seen, kept = set(), []
for chunk in re.split(r"(?m)^(?=@)", bib):
    m = re.match(r"@\w+\{([^,]+),", chunk)
    if m:
        if m.group(1).strip() in seen:
            print(f"[warn] dropping duplicate bib key {m.group(1).strip()}")
            continue
        seen.add(m.group(1).strip())
    kept.append(chunk)
bib = "".join(kept)
# escape characters missing from pdfLaTeX's standard utf8 support
for src, dst in {
    "‐": "-",            # unicode hyphen
    "­": "",             # soft hyphen
    "ũ": r"\~{u}",       # u with tilde
    "ấ": r"\'{\^{a}}",   # a circumflex + acute
    "ễ": r"\~{\^{e}}",   # e circumflex + tilde
    "ț": r"\c{t}",       # t with comma below (cedilla approximation)
    "Ț": r"\c{T}",
}.items():
    bib = bib.replace(src, dst)
(LATEX / "references.bib").write_text(bib)

# ---------- 8. figures ----------
for png in (DRAFT / "figures").glob("*.png"):
    shutil.copy2(png, LATEX / "figures" / png.name)

# ---------- 9. arXiv/Overleaf source bundle ----------
# Source-only: main.tex at the archive root, figures/ relative, no PDF/aux/log --
# arXiv compiles exactly what it receives. This used to be built by hand, which meant
# the zip named in arxiv_meta/README.md silently went stale between revisions.
import zipfile
BUNDLE = DRAFT / "sc_survey_overleaf.zip"
with zipfile.ZipFile(BUNDLE, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(LATEX / "main.tex", "main.tex")
    z.write(LATEX / "references.bib", "references.bib")
    # arXiv recommends shipping the .bbl so its BibTeX run is not load-bearing.
    # Build it locally first (cd latex && tectonic main.tex) so this exists.
    if (LATEX / "main.bbl").exists():
        z.write(LATEX / "main.bbl", "main.bbl")
    else:
        print("[warn] no latex/main.bbl -- run tectonic once, then rebuild the bundle")
    for f in sorted((LATEX / "figures").glob("*.png")):
        z.write(f, f"figures/{f.name}")

print(f"wrote {LATEX}/main.tex, references.bib, figures/")
print(f"wrote {BUNDLE.name} ({BUNDLE.stat().st_size // 1024} KB) -- the arXiv/Overleaf source bundle")
print("compile check:  cd latex && tectonic main.tex   (or upload to Overleaf)")
