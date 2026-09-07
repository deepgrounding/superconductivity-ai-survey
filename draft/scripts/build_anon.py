#!/usr/bin/env python3
"""Anonymous review copies. Author identity leaks through THREE places, and
stripping only the visible one is the classic mistake:
  1. the YAML `author:` list in main.md      -> visible on the title page
  2. the LaTeX \author{...} block            -> visible on the title page
  3. hyperref's pdfauthor={...}              -> invisible, sits in PDF metadata
Outputs (gitignored): survey_v1_noauthor.pdf and sc_survey_overleaf_noauthor.zip.
Verify with: pdfinfo survey_v1_noauthor.pdf
"""
import re, shutil, subprocess, tempfile, zipfile
from pathlib import Path

DRAFT = Path(__file__).resolve().parents[1]

def strip_yaml_author(md: str) -> str:
    # remove the `author:` key and its indented list items
    return re.sub(r"^author:\n(?:  - .*\n)+", "", md, flags=re.M)

def drop_balanced(tex: str, macro: str) -> str:
    i = tex.find(macro)
    if i < 0: return tex
    j = i + len(macro); depth = 0
    while j < len(tex):
        if tex[j] == "{": depth += 1
        elif tex[j] == "}":
            depth -= 1
            if depth == 0: break
        j += 1
    return tex[:i] + macro + "{}" + tex[j + 1:]

def main():
    md = strip_yaml_author((DRAFT / "main.md").read_text())
    with tempfile.TemporaryDirectory() as td:
        tmp_md = Path(td) / "main_anon.md"; tmp_md.write_text(md)
        for f in ("combined.bib", "pdf-header.tex"):
            shutil.copy(DRAFT / f, Path(td) / f)
        shutil.copytree(DRAFT / "figures", Path(td) / "figures")
        subprocess.run(["pandoc", str(tmp_md), "--citeproc", "--bibliography", "combined.bib",
                        "--pdf-engine=tectonic", "-H", "pdf-header.tex",
                        "-V", "geometry:margin=1in", "-V", "fontsize=11pt",
                        "-V", "colorlinks=true",
                        "-o", str(DRAFT / "survey_v1_noauthor.pdf")], cwd=td, check=True)
    print("wrote survey_v1_noauthor.pdf")

    latex = DRAFT / "latex"
    if (latex / "main.tex").exists():
        tex = (latex / "main.tex").read_text()
        tex = drop_balanced(tex, r"\author")
        tex = re.sub(r"^\s*pdfauthor=\{.*?\},?\s*$", "", tex, flags=re.M | re.S)
        tex = re.sub(r"pdfauthor=\{[^}]*\},?", "", tex)
        out = DRAFT / "sc_survey_overleaf_noauthor.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("main.tex", tex)
            z.write(latex / "references.bib", "references.bib")
            for f in sorted((latex / "figures").glob("*.png")):
                z.write(f, f"figures/{f.name}")
        print(f"wrote {out.name}")
        assert "pdfauthor" not in tex, "pdfauthor survived -- would deanonymise the PDF"

if __name__ == "__main__":
    main()
