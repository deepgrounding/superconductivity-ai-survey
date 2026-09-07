#!/usr/bin/env python3
"""Audit every CITED bib entry against its primary source.
arXiv entries -> arXiv API (authoritative for title + ordered author list).
DOI entries   -> Crossref.
Reports title mismatch, first-author mismatch, author-count mismatch, year mismatch.
"""
import json, re, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path("/Users/minggguangchen/Desktop/2026/manuscript/superconductivity")
NS = {"a": "http://www.w3.org/2005/Atom"}

def parse_bib(path):
    txt = Path(path).read_text()
    out = {}
    for blk in re.split(r"(?m)^(?=@)", txt):
        m = re.match(r"@(\w+)\{([^,]+),", blk)
        if not m: continue
        key = m.group(2).strip()
        f = {}
        for fm in re.finditer(r"^\s*(\w+)\s*=\s*\{(.*?)\},?\s*$", blk, re.M | re.S):
            f[fm.group(1).lower()] = fm.group(2).strip()
        f["_type"] = m.group(1); f["_src"] = Path(path).name
        out[key] = f
    return out

def norm_title(s):
    s = re.sub(r"\\[a-zA-Z]+", " ", s)
    s = re.sub(r"[{}$\\_^]", "", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return re.sub(r"[^a-z0-9 ]", "", s)

def norm_name(s):
    s = re.sub(r"\\[a-zA-Z]+\{(.)\}", r"\1", s)
    s = re.sub(r"[{}\\'`\"^~.]", "", s)
    return re.sub(r"\s+", " ", s).strip().lower()

def surname(full):
    parts = norm_name(full).split()
    return parts[-1] if parts else ""

def fetch_arxiv(ids):
    out = {}
    for i in range(0, len(ids), 20):
        chunk = ids[i:i+20]
        url = "http://export.arxiv.org/api/query?id_list=" + ",".join(chunk) + f"&max_results={len(chunk)}"
        for att in range(4):
            try:
                root = ET.fromstring(urllib.request.urlopen(url, timeout=90).read()); break
            except Exception as e:
                if att == 3: print(f"  arXiv batch FAILED: {e}", file=sys.stderr); root = None
                else: time.sleep(4)
        if root is None: continue
        for e in root.findall("a:entry", NS):
            aid = re.sub(r"v\d+$", "", e.find("a:id", NS).text.split("/abs/")[-1])
            out[aid] = {
                "title": re.sub(r"\s+", " ", e.find("a:title", NS).text.strip()),
                "authors": [a.find("a:name", NS).text.strip() for a in e.findall("a:author", NS)],
                "published": e.find("a:published", NS).text[:10],
            }
        time.sleep(3)
    return out

def fetch_doi(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    for att in range(3):
        try:
            d = json.load(urllib.request.urlopen(url, timeout=60))["message"]
            return {"title": d["title"][0],
                    "authors": [f"{a.get('given','')} {a.get('family','')}".strip() for a in d.get("author", [])],
                    "year": (d.get("published", {}).get("date-parts") or [[None]])[0][0],
                    "container": (d.get("container-title") or [""])[0],
                    "volume": d.get("volume"), "page": d.get("page") or d.get("article-number")}
        except Exception as e:
            if att == 2: return {"_error": str(e)}
            time.sleep(2)

def main():
    bibs = {}
    bibs.update(parse_bib(ROOT / "draft/references.bib"))
    bibs.update(parse_bib(ROOT / "draft/anchors.bib"))
    cited = sorted(set(re.findall(r"@([A-Za-z]+[0-9]{4}[A-Za-z0-9]*)", (ROOT / "draft/main.md").read_text())))
    print(f"auditing {len(cited)} cited entries\n")

    arxiv_keys = [k for k in cited if bibs.get(k, {}).get("eprint")]
    ids = [bibs[k]["eprint"] for k in arxiv_keys]
    ax = fetch_arxiv(ids)
    findings = []

    for k in cited:
        b = bibs.get(k)
        if not b: findings.append((k, "NO BIB ENTRY", "", "")); continue
        eprint, doi = b.get("eprint"), b.get("doi")
        bt, ba = b.get("title", ""), b.get("author", "")
        blist = [x.strip() for x in ba.split(" and ")] if ba else []

        if eprint:
            src = ax.get(eprint)
            if not src: findings.append((k, "arXiv ID NOT FOUND", eprint, "")); continue
            if norm_title(bt) != norm_title(src["title"]):
                findings.append((k, "TITLE", bt[:75], src["title"][:75]))
            if blist and src["authors"]:
                if surname(blist[0]) != surname(src["authors"][0]):
                    findings.append((k, "FIRST AUTHOR", blist[0], src["authors"][0]))
                if len(blist) != len(src["authors"]):
                    findings.append((k, "AUTHOR COUNT", str(len(blist)), str(len(src["authors"]))))
                else:
                    for i, (x, y) in enumerate(zip(blist, src["authors"])):
                        if surname(x) != surname(y):
                            findings.append((k, f"AUTHOR #{i+1}", x, y)); break
            elif not blist:
                findings.append((k, "NO AUTHORS IN BIB", "", src["authors"][0] if src["authors"] else "?"))
            if b.get("year") and b["year"] != src["published"][:4]:
                findings.append((k, "YEAR vs arXiv v1", b["year"], src["published"]))
        elif doi:
            src = fetch_doi(doi)
            if src.get("_error"): findings.append((k, "DOI UNRESOLVED", doi, src["_error"][:50])); continue
            if norm_title(bt) != norm_title(src["title"]):
                findings.append((k, "TITLE", bt[:75], src["title"][:75]))
            if blist and src["authors"]:
                if surname(blist[0]) != surname(src["authors"][0]):
                    findings.append((k, "FIRST AUTHOR", blist[0], src["authors"][0]))
                if len(blist) != len(src["authors"]):
                    findings.append((k, "AUTHOR COUNT", str(len(blist)), str(len(src["authors"]))))
                else:
                    for i, (x, y) in enumerate(zip(blist, src["authors"])):
                        if surname(x) != surname(y):
                            findings.append((k, f"AUTHOR #{i+1}", x, y)); break
            if b.get("year") and src.get("year") and str(b["year"]) != str(src["year"]):
                findings.append((k, "YEAR", b["year"], str(src["year"])))
            if b.get("volume") and src.get("volume") and str(b["volume"]) != str(src["volume"]):
                findings.append((k, "VOLUME", b["volume"], str(src["volume"])))
        else:
            findings.append((k, "NO eprint OR doi (unverifiable)", b.get("_type", ""), b.get("howpublished", "")))
        time.sleep(0.05)

    if not findings:
        print("CLEAN: every cited entry matches its primary source.")
    else:
        print(f"{len(findings)} findings:\n")
        for k, what, got, exp in findings:
            print(f"[{what}] {k}")
            if got or exp:
                print(f"    bib: {got}")
                print(f"    src: {exp}")
    Path(ROOT / "artifacts/citation_audit.txt").write_text(
        "\n".join(f"{k}\t{w}\t{g}\t{e}" for k, w, g, e in findings))

if __name__ == "__main__":
    main()
