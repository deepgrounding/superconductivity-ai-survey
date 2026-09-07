#!/usr/bin/env python3
"""Exploratory clustering of the seed corpus (scaffolding for taxonomy design,
NOT the paper's taxonomy). TF-IDF(title+abstract) -> SVD(60) -> KMeans(k).
Writes artifacts/theme_summary.csv (cluster, size, top terms, 3 sample titles)
and artifacts/sc_seed_clusters.csv (arxiv_id, cluster). Prints the summary.

Usage: python draft/scripts/explore_clusters.py [--k 30]
"""
import argparse, csv
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "artifacts" / "sc_seed.csv"

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--k", type=int, default=30)
    a = ap.parse_args()
    rows = list(csv.DictReader(open(SEED)))
    docs = [r["title"] + ". " + r["title"] + ". " + r["summary"] for r in rows]
    vec = TfidfVectorizer(max_features=30000, sublinear_tf=True, stop_words="english",
                          ngram_range=(1, 2), min_df=5, max_df=0.4)
    X = vec.fit_transform(docs)
    Z = normalize(TruncatedSVD(60, random_state=0).fit_transform(X))
    km = KMeans(a.k, n_init=10, random_state=0).fit(Z)
    terms = np.array(vec.get_feature_names_out())
    out = []
    for c in range(a.k):
        idx = np.where(km.labels_ == c)[0]
        cen = np.asarray(X[idx].mean(axis=0)).ravel()
        top = terms[cen.argsort()[::-1][:12]]
        samp = [rows[i]["title"][:90] for i in idx[:3]]
        out.append({"cluster": c, "size": len(idx), "top_terms": ", ".join(top), "samples": " | ".join(samp)})
    out.sort(key=lambda d: -d["size"])
    with open(ROOT / "artifacts" / "theme_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    with open(ROOT / "artifacts" / "sc_seed_clusters.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["arxiv_id", "cluster"])
        w.writerows((r["arxiv_id"], int(l)) for r, l in zip(rows, km.labels_))
    for d in out:
        print(f"\n[{d['cluster']:2d}] n={d['size']:4d}  {d['top_terms']}")
        for s in d["samples"].split(" | "): print(f"      - {s}")

if __name__ == "__main__":
    main()
