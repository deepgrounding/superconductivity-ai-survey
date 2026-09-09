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
import argparse, csv, html, json, re, sys, time, unicodedata, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "artifacts" / "sc_corpus_v1.csv"
KEYS = ROOT / "artifacts" / "bibkeys.csv"
MAIN = ROOT / "draft" / "main.md"
XREF = ROOT / "artifacts" / "crossref_cache.json"
OUT = ROOT / "draft" / "references.bib"
STOP = {"a", "an", "the", "on", "of", "for", "and", "to", "in", "towards", "toward",
        "with", "via", "from", "what", "why", "how", "do", "does", "is", "are", "at", "by"}

def load_xref():
    return json.loads(XREF.read_text()) if XREF.exists() else {}

def crossref(doi, cache):
    """Authoritative bibliographic data for the PUBLISHED version.

    Why this exists: OpenAlex resolves an arXiv-DOI query to the *preprint*
    record, whose DOI is 10.48550/arXiv.<id>. Emitting that DOI next to a
    journal name sends the reader to the preprint while claiming the article --
    and arXiv's own `journal_ref` is free text ("Comput. Mater. Sci., 263,
    114453 (2026)"), which is not a journal name and must not be written into
    a `journal` field. So: prefer the author-supplied publisher DOI carried in
    the arXiv metadata, and resolve it here for journal / volume / pages / year.
    """
    if not doi or doi.lower().startswith("10.48550"):
        return None
    if doi in cache:
        return cache[doi]
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    rec = None
    for attempt in range(3):
        try:
            d = json.load(urllib.request.urlopen(url, timeout=60))["message"]
            rec = {
                "journal": (d.get("container-title") or [""])[0],
                "volume": d.get("volume") or "",
                "pages": (d.get("page") or d.get("article-number") or ""),
                "year": str(((d.get("published", {}).get("date-parts") or [[""]])[0] or [""])[0] or ""),
                "title": re.sub(r"<[^>]+>", "", (d.get("title") or [""])[0]),
                "n_authors": len(d.get("author", [])),
            }
            break
        except Exception as e:
            if attempt == 2:
                print(f"  crossref miss {doi}: {e}", file=sys.stderr)
            else:
                time.sleep(2)
    cache[doi] = rec
    return rec

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

MATH_SPAN = re.compile(r"\$[^$]*\$")
SUBSUP = re.compile(r"([_^])(\{[^{}]*\}|\\[A-Za-z]+|\w)")

def normalise_math(s):
    r"""arXiv titles carry LaTeX math ('AV$_3$Sb$_5$'), sometimes with broken nesting
    ('La$_{3}$Ni$_{2}$O$_{7-$\delta$}$'). Escaping the '$' and '_' turned all of it
    into literal '$_3$' in the reference list. Instead: drop every delimiter, then
    re-wrap each sub/superscript group in its own math span, which repairs the
    malformed cases as a side effect."""
    if "$" not in s and "_" not in s and "^" not in s:
        return s
    return SUBSUP.sub(r"$\1\2$", s.replace("$", ""))

def outside_math(s, fn):
    out, last = [], 0
    for m in MATH_SPAN.finditer(s):
        out.append(fn(s[last:m.start()])); out.append(m.group(0)); last = m.end()
    out.append(fn(s[last:]))
    return "".join(out)

def _escape_text(s):
    s = (s.replace("\\", r"\textbackslash{}").replace("&", r"\&").replace("%", r"\%")
          .replace("#", r"\#").replace("_", r"\_"))
    return degreek(transliterate(s))

def bib_escape(s):
    return outside_math(normalise_math(html.unescape(s)), _escape_text)

_PROTECT = re.compile(r"\b([A-Za-z]*[A-Z][A-Za-z]*[A-Z][A-Za-z]*|[A-Z]{2,}|[A-Za-z]+\d+[A-Za-z\d]*)\b")

def protect_title(t):
    # Brace-protect capitalised tokens, but never reach inside a math span.
    return outside_math(bib_escape(t), lambda x: _PROTECT.sub(r"{\1}", x))

def entry(row, key, cache):
    aid = row["arxiv_id"].strip()
    authors = row.get("authors") or row.get("oa_authors") or ""
    # publisher DOI supplied by the authors in the arXiv metadata, else whatever
    # OpenAlex had -- but never an arXiv DataCite DOI, which points at the preprint
    doi = (row.get("doi") or "").strip()
    if not doi:
        oa = (row.get("oa_doi") or "").strip()
        doi = "" if oa.lower().startswith("10.48550") else oa
    xr = crossref(doi, cache)
    year = (xr or {}).get("year") or row["year"]
    journal = (xr or {}).get("journal") or row.get("venue") or ""
    volume = (xr or {}).get("volume") or ""
    pages = (xr or {}).get("pages") or ""
    jref = (row.get("journal_ref") or "").strip()
    kind = "article" if journal else "misc"

    lines = [f"@{kind}{{{key},", f"  title = {{{protect_title(row['title'])}}},"]
    if authors:
        lines.append(f"  author = {{{bib_escape(authors)}}},")
    lines.append(f"  year = {{{year}}},")
    if journal:
        lines.append(f"  journal = {{{bib_escape(journal)}}},")
        if volume: lines.append(f"  volume = {{{bib_escape(volume)}}},")
        if pages: lines.append(f"  pages = {{{bib_escape(pages.replace('-', '--', 1))}}},")
        if doi: lines.append(f"  doi = {{{doi}}},")
    lines += [f"  eprint = {{{aid}}},", "  archivePrefix = {arXiv},",
              f"  url = {{https://arxiv.org/abs/{aid}}},"]
    # a journal_ref we could not resolve is recorded verbatim as a note, never as a
    # `journal` value -- it is a citation string, not a journal name
    if jref and not journal:
        lines.append(f"  note = {{Published as: {bib_escape(jref)}}},")
    else:
        lines.append(f"  note = {{}},  % family: {row.get('family','')} task: {row.get('task','')} src: {row.get('source','')}")
    lines.append("}")
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
    cache = load_xref()
    OUT.write_text(f"% Auto-generated by build_bib.py from {CORPUS.name} ({time.strftime('%Y-%m-%d')}); "
                   f"{len(chosen)} entries ({'all rows' if a.all else 'cited rows only'}). Do not hand-edit.\n\n"
                   + "\n\n".join(entry(r, k, cache) for k, r in chosen) + "\n")
    XREF.write_text(json.dumps(cache, indent=1, sort_keys=True))
    print(f"wrote {OUT}: {len(chosen)} entries; keys table {KEYS} ({len(keyed)} rows)")
    if cited:
        missing = sorted(cited - {k for k, _ in keyed})
        print("cited keys not in corpus (must be in anchors.bib):", len(missing))
        for m in missing: print("  ", m)

if __name__ == "__main__":
    main()
