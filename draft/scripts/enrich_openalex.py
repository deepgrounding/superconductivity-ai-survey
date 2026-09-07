#!/usr/bin/env python3
"""Enrich the canonical corpus in place with OpenAlex metadata:
cited_by, venue, oa_doi, oa_authors (Latin-only, else blank).

Idempotent: results are cached per arXiv id in artifacts/openalex_cache.jsonl;
only uncached ids are fetched (batches of 50 via the DOI filter
10.48550/arXiv.<id>). Rows OpenAlex has not indexed get cited_by="" (not 0).

Usage: python draft/scripts/enrich_openalex.py [--corpus artifacts/sc_corpus_v1.csv] [--refresh]
"""
import argparse, csv, json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "artifacts" / "openalex_cache.jsonl"
BATCH = 50
NON_LATIN = re.compile(r"[Ѐ-ӿͰ-Ͽ一-鿿぀-ヿ가-힯]")
NEWCOLS = ["cited_by", "venue", "oa_doi", "oa_authors", "oa_fetched"]

def api_key():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("OPENALEX_API_KEY="):
                return line.split("=", 1)[1].strip()
    return None

def fetch_batch(ids, key):
    filt = "doi:" + "|".join(f"10.48550/arXiv.{i}" for i in ids)
    params = {"filter": filt, "per-page": str(len(ids)),
              "select": "doi,title,publication_year,cited_by_count,authorships,primary_location,ids"}
    if key: params["api_key"] = key
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                return json.load(r)["results"]
        except Exception as e:
            print(f"  batch failed ({e}); retry {attempt+1}", file=sys.stderr)
            time.sleep(3 * (attempt + 1))
    return []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=str(ROOT / "artifacts" / "sc_corpus_v1.csv"))
    ap.add_argument("--refresh", action="store_true", help="ignore cache")
    a = ap.parse_args()
    corpus = Path(a.corpus)
    rows = list(csv.DictReader(open(corpus)))
    ids = [re.sub(r"v\d+$", "", r["arxiv_id"].strip()) for r in rows]

    cache = {}
    if CACHE.exists() and not a.refresh:
        for line in CACHE.read_text().splitlines():
            if line.strip():
                d = json.loads(line); cache[d["arxiv_id"]] = d
    todo = [i for i in ids if i not in cache]
    print(f"{len(rows)} rows; {len(cache)} cached; fetching {len(todo)}")
    key = api_key()
    with open(CACHE, "a") as cf:
        for k in range(0, len(todo), BATCH):
            chunk = todo[k:k + BATCH]
            found = {}
            for w in fetch_batch(chunk, key):
                doi = (w.get("doi") or "").lower()
                m = re.search(r"10\.48550/arxiv\.(.+)$", doi)
                if not m: continue
                aid = m.group(1)
                auths = [x.get("author", {}).get("display_name") or "" for x in w.get("authorships", [])]
                if any(NON_LATIN.search(x) for x in auths): auths = []
                src = ((w.get("primary_location") or {}).get("source") or {})
                venue = src.get("display_name") or ""
                if "arxiv" in venue.lower(): venue = ""
                pub_doi = ((w.get("ids") or {}).get("doi") or "")
                found[aid] = {"arxiv_id": aid, "cited_by": w.get("cited_by_count", 0),
                              "venue": venue, "oa_doi": pub_doi.replace("https://doi.org/", ""),
                              "oa_authors": " and ".join(a for a in auths if a)}
            for aid in chunk:
                d = found.get(aid, {"arxiv_id": aid, "cited_by": "", "venue": "", "oa_doi": "", "oa_authors": ""})
                d["oa_fetched"] = time.strftime("%Y-%m-%d")
                cache[aid] = d; cf.write(json.dumps(d) + "\n")
            cf.flush()
            print(f"  {min(k+BATCH, len(todo))}/{len(todo)}  resolved so far {sum(1 for i in ids if cache.get(i, {}).get('cited_by') != '')}", flush=True)
            time.sleep(0.15)

    for r, aid in zip(rows, ids):
        d = cache.get(aid, {})
        for c in NEWCOLS: r[c] = d.get(c, "")
    fields = list(rows[0].keys())
    for c in NEWCOLS:
        if c not in fields: fields.append(c)
    with open(corpus, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    n_res = sum(1 for r in rows if r["cited_by"] != "")
    n_ven = sum(1 for r in rows if r["venue"])
    print(f"\nwrote {corpus}: resolved {n_res}/{len(rows)}; with venue {n_ven}")

if __name__ == "__main__":
    main()
