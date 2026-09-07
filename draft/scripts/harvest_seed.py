#!/usr/bin/env python3
"""Systematic seed harvest: every arXiv paper listed under cond-mat.supr-con
(primary OR cross-list) submitted in the survey window, pulled month by month
through the arXiv API. Per-month raw Atom responses are cached in
artifacts/raw_seed/ so the script can be re-run without re-downloading.

Output: artifacts/sc_seed.csv (frozen seed snapshot; downstream scripts read
it but never write it). Columns:
  arxiv_id, title, year, pub_date, primary_cat, all_cats, authors, doi,
  journal_ref, url, summary, source

Usage: python draft/scripts/harvest_seed.py [--start 2021-09] [--end 2026-09]
"""
import argparse, csv, re, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "artifacts" / "raw_seed"
OUT = ROOT / "artifacts" / "sc_seed.csv"
CAT = "cond-mat.supr-con"
NS = {"atom": "http://www.w3.org/2005/Atom",
      "os": "http://a9.com/-/spec/opensearch/1.1/",
      "arxiv": "http://arxiv.org/schemas/atom"}
FIELDS = ["arxiv_id", "title", "year", "pub_date", "primary_cat", "all_cats",
          "authors", "doi", "journal_ref", "url", "summary", "source"]

def months(start, end):
    y, m = map(int, start.split("-")); ye, me = map(int, end.split("-"))
    while (y, m) <= (ye, me):
        yield y, m
        m += 1
        if m == 13: y, m = y + 1, 1

def month_bounds(y, m):
    last = (date(y + (m == 12), (m % 12) + 1, 1) - date(y, m, 1)).days
    return f"{y}{m:02d}010000", f"{y}{m:02d}{last:02d}2359"

def fetch_month(y, m):
    cache = RAW / f"{y}-{m:02d}.xml"
    if cache.exists() and cache.stat().st_size > 1000:
        return cache.read_bytes(), True
    a, b = month_bounds(y, m)
    q = f"cat:{CAT} AND submittedDate:[{a} TO {b}]"
    url = ("http://export.arxiv.org/api/query?search_query=" + urllib.parse.quote(q)
           + "&start=0&max_results=2000&sortBy=submittedDate&sortOrder=ascending")
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=180) as r:
                data = r.read()
            root = ET.fromstring(data)
            total = int(root.find("os:totalResults", NS).text)
            got = len(root.findall("atom:entry", NS))
            if total > 0 and got == 0:
                raise RuntimeError(f"empty page for total={total} (API hiccup)")
            if got < total:
                print(f"  WARNING {y}-{m:02d}: returned {got} < total {total}", file=sys.stderr)
            cache.write_bytes(data)
            return data, False
        except Exception as e:
            print(f"  retry {attempt+1} {y}-{m:02d}: {e}", file=sys.stderr)
            time.sleep(10 * (attempt + 1))
    raise SystemExit(f"giving up on {y}-{m:02d}")

def parse(data):
    root = ET.fromstring(data)
    for e in root.findall("atom:entry", NS):
        aid = re.sub(r"v\d+$", "", e.find("atom:id", NS).text.split("/abs/")[-1])
        pub = e.find("atom:published", NS).text
        cats = [c.get("term") for c in e.findall("atom:category", NS)]
        prim = e.find("arxiv:primary_category", NS)
        doi = e.find("arxiv:doi", NS); jr = e.find("arxiv:journal_ref", NS)
        yield {
            "arxiv_id": aid,
            "title": re.sub(r"\s+", " ", e.find("atom:title", NS).text.strip()),
            "year": pub[:4],
            "pub_date": pub[:19].replace("T", " "),
            "primary_cat": prim.get("term") if prim is not None else (cats[0] if cats else ""),
            "all_cats": ";".join(cats),
            "authors": " and ".join(a.find("atom:name", NS).text.strip()
                                    for a in e.findall("atom:author", NS)),
            "doi": doi.text.strip() if doi is not None and doi.text else "",
            "journal_ref": re.sub(r"\s+", " ", jr.text.strip()) if jr is not None and jr.text else "",
            "url": f"https://arxiv.org/abs/{aid}",
            "summary": re.sub(r"\s+", " ", e.find("atom:summary", NS).text.strip()),
            "source": "seed",
        }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2021-09"); ap.add_argument("--end", default="2026-09")
    args = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    rows, seen = [], set()
    for y, m in months(args.start, args.end):
        data, cached = fetch_month(y, m)
        n = 0
        for r in parse(data):
            if r["arxiv_id"] in seen: continue
            seen.add(r["arxiv_id"]); rows.append(r); n += 1
        print(f"{y}-{m:02d}: +{n:4d}  total {len(rows):6d}  {'(cache)' if cached else ''}", flush=True)
        if not cached: time.sleep(3)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    prim = sum(r["primary_cat"] == CAT for r in rows)
    print(f"\nwrote {OUT}: {len(rows)} rows ({prim} primary {CAT}, {len(rows)-prim} cross-listed)")

if __name__ == "__main__":
    main()
