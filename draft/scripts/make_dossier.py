#!/usr/bin/env python3
"""Per-category dossiers for section writing.

Ranking is by RECENCY-NORMALISED citations, not raw `cited_by`: over a five-year
window raw counts hand you 2021-2022 papers and starve the 2025-2026 material a
current survey exists to cover. Score = cited_by / max(months_since_submission, 6),
i.e. citations per month, with a floor so brand-new papers are not divided by ~0.
Each dossier therefore lists top-by-rate papers PLUS a most-recent block.

Bib keys are read from artifacts/bibkeys.csv (written by build_bib.py) so the
dossier quotes the exact key the manuscript must cite -- never a guessed one.

Usage:
  python draft/scripts/make_dossier.py --family nickelate
  python draft/scripts/make_dossier.py --task discovery --ai-only
  python draft/scripts/make_dossier.py --family cuprate --exclude-cited   # for expansion rounds
"""
import argparse, csv, re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "artifacts" / "sc_corpus_v1.csv"
KEYS = ROOT / "artifacts" / "bibkeys.csv"
MAIN = ROOT / "draft" / "main.md"
TODAY = date.today()

def months_since(d):
    try:
        y, m = int(d[:4]), int(d[5:7])
    except Exception:
        return 60.0
    return max((TODAY.year - y) * 12 + (TODAY.month - m), 0) + 1.0

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--family"); p.add_argument("--task"); p.add_argument("--ai-only", action="store_true")
    p.add_argument("--top", type=int, default=14); p.add_argument("--recent", type=int, default=6)
    p.add_argument("--chars", type=int, default=520)
    p.add_argument("--exclude-cited", action="store_true", help="skip papers already cited in main.md")
    a = p.parse_args()

    keys = {r["arxiv_id"]: r["key"] for r in csv.DictReader(open(KEYS))} if KEYS.exists() else {}
    cited = set(re.findall(r"@([A-Za-z]+[0-9]{4}[A-Za-z0-9]*)", MAIN.read_text())) if (a.exclude_cited and MAIN.exists()) else set()

    rows = [r for r in csv.DictReader(open(CORPUS)) if r.get("off_topic") != "true"]
    if a.family: rows = [r for r in rows if r["family"] == a.family]
    if a.task: rows = [r for r in rows if r["task"] == a.task]
    if a.ai_only: rows = [r for r in rows if r.get("ai_method") not in ("", "none")]
    if cited: rows = [r for r in rows if keys.get(r["arxiv_id"]) not in cited]
    if not rows: return print("no rows match")

    def rate(r):
        try: c = int(r.get("cited_by") or 0)
        except ValueError: c = 0
        return c / max(months_since(r["pub_date"]), 6.0)

    by_rate = sorted(rows, key=rate, reverse=True)[:a.top]
    chosen = {r["arxiv_id"] for r in by_rate}
    by_recent = [r for r in sorted(rows, key=lambda r: r["pub_date"], reverse=True)
                 if r["arxiv_id"] not in chosen][:a.recent]

    scope = " ".join(filter(None, [a.family, a.task, "AI-only" if a.ai_only else ""])) or "corpus"
    print(f"# Dossier: {scope}   ({len(rows)} papers in scope)\n")
    for header, block in (("## Top by citations per month", by_rate), ("## Most recent", by_recent)):
        print(header + "\n")
        for r in block:
            key = keys.get(r["arxiv_id"], "NO-BIBKEY")
            c = r.get("cited_by") or "?"
            print(f"[@{key}] {r['title']}")
            print(f"    {r['family']}/{r['task']}"
                  + (f" ai={r['ai_method']}" if r.get("ai_method") not in ("", "none") else "")
                  + f" | {r['pub_date'][:10]} | cites {c} | rate {rate(r):.2f}/mo | {r['url']}")
            print(f"    {r['summary'][:a.chars]}...\n")

if __name__ == "__main__":
    main()
