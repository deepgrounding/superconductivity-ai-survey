# Citation audit

Every one of the 109 cited entries was checked against its primary source: arXiv
entries against the arXiv API, DOI-bearing entries against Crossref. Re-run with:

```bash
python draft/scripts/audit_citations.py
```

## Errors found and fixed

| Entry | Error | Fix |
|---|---|---|
| `szymanski2023autonomous` | Title was the original *"...synthesis of novel materials"*. Nature corrected it post-publication to *"...synthesis of inorganic materials"*. | Title updated to the current published form. |
| 43 corpus entries | The generator preferred OpenAlex's DOI, which for an arXiv-DOI query resolves to the **preprint** (`10.48550/arXiv.*`). Those entries carried a journal name next to a DOI pointing at the preprint. | `build_bib.py` now prefers the author-supplied publisher DOI in the arXiv metadata and resolves it through Crossref for journal, volume, pages and year. |
| ~37 corpus entries | arXiv's `journal_ref` is free text (*"Comput. Mater. Sci., 263, 114453 (2026)"*) and was being written verbatim into `journal = {}`. | Structured fields now come from Crossref; an unresolvable `journal_ref` goes to `note = {Published as: ...}` and the entry stays `@misc`. |
| `tran2025superconductor` | Consequences of the above: year 2025 (arXiv posting) instead of 2024 (publication); journal field held a citation string. | Now Chemistry of Materials 36, 10939–10966 (2024) with the publisher DOI. |
| `zhou2025superconductivity`, `adiga2025accelerating`, `wang2025recent` | Same class. | Same fix. |

## Paraphrase corrections

Checking each in-text characterization against the source text, not the dossier
excerpt, changed four claims:

- **Cheetham and Seshadri** — the text had them "questioning how many of the predicted
  structures are meaningfully distinct", which the paper does not say. Replaced with
  their own finding of *"scant evidence for compounds that fulfill the trifecta of
  novelty, credibility, and utility"*.
- **Leeman et al.** — described as disputing the A-Lab's phase identification. Their
  objection is broader and their conclusion stronger: they examine all 43 products,
  identify four recurring shortfalls, and conclude no new materials were discovered.
- **Lee et al. (SDL 2.0)** — glossed as "integrating synthesis, characterization and
  theory"; the paper frames six properties (interoperable, collaborative,
  generalizable, orchestrated, safe, creative). Now stated as published.
- **Saykin et al.** — cited only for "time-reversal-symmetry breaking is contested".
  It is a null result: no Kerr signal to a 30 nrad floor, concluding breaking is
  highly unlikely. Now stated.

An earlier pass over Section 3 corrected four more (Griffin's argument reversed,
Salke et al. miscast as a rebuttal, the 298 K claim unqualified, Ajeesh et al.'s null
result described neutrally).

## Findings that are correct as they stand

The audit still reports 49 differences. Every one was inspected; none is an error.

- **34 × "YEAR vs arXiv v1"** — the entry carries the *publication* year while the
  preprint was posted earlier. Correct for `@article` entries with a publisher DOI.
- **8 × TITLE** — preprint and published titles genuinely differ (`cao2018unconventional`,
  `ran2019nearly`, `sun2023superconductivity`, `drozdov2015conventional`: each confirmed
  the same work via the arXiv page's own journal reference), or Crossref returns markup
  and mojibake (`kamihara2008iron`, `bednorz1986possible`), or Crossref prefixes
  "RETRACTED ARTICLE:" while the entry carries the original title plus a `note`
  documenting the retraction (`snider2020retracted`, `dasenbrock2023retracted`).
- **6 × author differences** — TeX transliteration of Đ, ć, ž, ü against Crossref's raw
  Unicode or mojibake; the bib is correct. `sun2023superconductivity` has 14 authors in
  the published version and 13 on the preprint; the entry cites the published version.
- **1 × unverifiable** — `anthropic2026mhs` is a news post with no DOI. Its URL was
  fetched and resolves; it is cited in the text explicitly as framing, not evidence.
