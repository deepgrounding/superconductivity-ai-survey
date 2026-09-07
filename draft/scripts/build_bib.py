#!/usr/bin/env python3
"""Build draft/references.bib from the canonical corpus — for CITED rows only.

Keys follow the skill convention: <firstauthor-surname><year><firsttitleword>.
The key for every corpus row is computed deterministically here and written
to artifacts/bibkeys.csv (arxiv_id -> key) so dossiers can quote the exact key
before the bib exists. main.md citations are matched against those keys;
only matched rows are emitted (pass --all to emit the whole corpus).

Authors: arXiv author list (Latin transliteration, always present) is the
default; OpenAlex authors (from enrich_openalex.py) are used only when the
arXiv list is empty. Venue/DOI come from OpenAlex enrichment, with the arXiv
journal_ref/doi fields as fallback. No network access.

Usage: python draft/scripts/build_bib.py [--all]
"""
import argparse, csv, re, time, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "artifacts" / "sc_corpus_v1.csv"
KEYS = ROOT / "artifacts" / "bibkeys.csv"
MAIN = ROOT / "draft" / "main.md"
OUT = ROOT / "draft" / "references.bib"
STOP = {"a", "an", "the", "on", "of", "for", "and", "to", "in", "towards", "toward",
        "with", "via", "from", "what", "why", "how", "do", "does", "is", "are", "at", "by"}

def slugify_key(first_author, year, title):
    last = first_author.split()[-1] if first_author.strip() else "anon"
    last = re.sub(r"[^a-zA-Z]", "", unicodedata.normalize("NFKD", last)).lower() or "anon"
    word = next((w for w in re.findall(r"[A-Za-z0-9']+", title) if w.lower() not in STOP), "paper")
    return f"{last}{year}{re.sub(r'[^a-z0-9]', '', word.lower())}"

# pdfLaTeX's default font encoding cannot set these; map to LaTeX accent macros so
# the PDF build stops dropping characters out of author names and formulas.
TEX_CHAR = {
    "ş": r"\c{s}", "Ş": r"\c{S}", "ı": r"{\i}", "Ž": r"\v{Z}", "ž": r"\v{z}",
    "đ": r"{\dj}", "Đ": r"{\DJ}", "Ð": r"{\DJ}", "ć": r"\'{c}", "Ć": r"\'{C}",
    "č": r"\v{c}", "Č": r"\v{C}", "š": r"\v{s}", "Š": r"\v{S}", "ő": r"\H{o}",
    "ű": r"\H{u}", "ā": r"\={a}", "ē": r"\={e}", "ī": r"\={i}", "ū": r"\={u}",
    "ğ": r"\u{g}", "ł": r"{\l}", "Ł": r"{\L}", "ř": r"\v{r}", "ų": r"\k{u}",
    "ę": r"\k{e}", "ą": r"\k{a}", "ė": r"\.{e}", "ż": r"\.{z}", "ń": r"\'{n}",
    "ś": r"\'{s}", "ź": r"\'{z}", "ǧ": r"\v{g}",
}
GREEK = {"α": r"$\alpha$", "β": r"$\beta$", "γ": r"$\gamma$", "δ": r"$\delta$",
         "ε": r"$\epsilon$", "θ": r"$\theta$", "κ": r"$\kappa$", "λ": r"$\lambda$",
         "μ": r"$\mu$", "ν": r"$\nu$", "π": r"$\pi$", "ρ": r"$\rho$",
         "σ": r"$\sigma$", "τ": r"$\tau$", "φ": r"$\phi$", "χ": r"$\chi$",
         "ψ": r"$\psi$", "ω": r"$\omega$", "Δ": r"$\Delta$", "Ω": r"$\Omega$",
         "Ξ": r"$\Xi$", "Å": r"{\AA}", "×": r"$\times$", "−": "-", "–": "--",
         "—": "---", "’": "'", "‘": "`", "“": "``", "”": "''"}

def transliterate(s):
    for k, v in TEX_CHAR.items(): s = s.replace(k, v)
    return s

def degreek(s):
    """Greek letters inside an already-math context ($...$) are fine as macros;
    outside one they need their own math mode. Titles here are mixed, so wrap."""
    for k, v in GREEK.items(): s = s.replace(k, v)
    return s

def bib_escape(s):
    s = (s.replace("\\", r"\\").replace("&", r"\&").replace("%", r"\%")
          .replace("#", r"\#").replace("_", r"\_").replace("$", r"\$"))
    return degreek(transliterate(s))

def protect_title(t):
    return re.sub(r"\b([A-Za-z]*[A-Z][A-Za-z]*[A-Z][A-Za-z]*|[A-Z]{2,}|[A-Za-z]+\d+[A-Za-z\d]*)\b",
                  r"{\1}", bib_escape(t))

def entry(row, key):
    aid = row["arxiv_id"].strip()
    authors = row.get("authors") or row.get("oa_authors") or ""
    venue = row.get("venue") or ""
    doi = row.get("oa_doi") or row.get("doi") or ""
    jref = row.get("journal_ref") or ""
    year = row["year"]
    kind = "article" if (venue or jref) else "misc"
    lines = [f"@{kind}{{{key},", f"  title = {{{protect_title(row['title'])}}},"]
    if authors: lines.append(f"  author = {{{bib_escape(authors)}}},")
    lines.append(f"  year = {{{year}}},")
    if venue: lines.append(f"  journal = {{{bib_escape(venue)}}},")
    elif jref: lines.append(f"  journal = {{{bib_escape(jref)}}},")
    if doi and kind == "article": lines.append(f"  doi = {{{doi}}},")
    lines += [f"  eprint = {{{aid}}},", "  archivePrefix = {arXiv},",
              f"  url = {{https://arxiv.org/abs/{aid}}},",
              f"  note = {{}},  % family: {row.get('family','')} task: {row.get('task','')} src: {row.get('source','')}", "}"]
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    rows = list(csv.DictReader(open(CORPUS)))
    # deterministic keys in corpus order, de-dup with a/b/c suffixes
    seen, keyed = set(), []
    for r in rows:
        first = (r.get("authors") or r.get("oa_authors") or "").split(" and ")[0]
        k0 = slugify_key(first, r["year"], r["title"]); k, s = k0, ord("a")
        while k in seen: k = k0 + chr(s); s += 1
        seen.add(k); keyed.append((k, r))
    with open(KEYS, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["arxiv_id", "key"]); w.writerows((r["arxiv_id"], k) for k, r in keyed)
    cited = set(re.findall(r"@([A-Za-z]+[0-9]{4}[A-Za-z0-9]*)", MAIN.read_text())) if MAIN.exists() else set()
    chosen = keyed if a.all else [(k, r) for k, r in keyed if k in cited]
    OUT.write_text(f"% Auto-generated by build_bib.py from {CORPUS.name} ({time.strftime('%Y-%m-%d')}); "
                   f"{len(chosen)} entries ({'all rows' if a.all else 'cited rows only'}). Do not hand-edit.\n\n"
                   + "\n\n".join(entry(r, k) for k, r in chosen) + "\n")
    print(f"wrote {OUT}: {len(chosen)} entries; keys table {KEYS} ({len(keyed)} rows)")
    if cited:
        missing = sorted(cited - {k for k, _ in keyed})
        print("cited keys not in corpus (must be in anchors.bib):", len(missing))
        for m in missing: print("  ", m)

if __name__ == "__main__":
    main()
