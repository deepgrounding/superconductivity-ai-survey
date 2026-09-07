#!/usr/bin/env python3
"""Draw a stratified validation sample for hand-labelling the taxonomy.

Sampling is weighted toward the cells the rules are least confident about
(general / synthesis / discovery) so the accuracy estimate is conservative;
the printout carries title + abstract excerpt so a human can label from
evidence. Writes artifacts/label_sample.csv with the machine labels in
`family_rule` / `task_rule` and blank `family_true` / `task_true` columns.

Usage: python draft/scripts/make_label_sample.py [--n 150]
"""
import argparse, csv, random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "artifacts" / "sc_corpus_v1.csv"
OUT = ROOT / "artifacts" / "label_sample.csv"

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=150)
    ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()
    rows = list(csv.DictReader(open(CORPUS)))
    random.seed(a.seed)
    # stratify: equal-ish draw per family, then per task, then a random top-up.
    # Equal strata (rather than proportional) put the most labelling effort on the
    # small/uncertain families; accuracy is reported per stratum AND corpus-weighted.
    picked, seen = [], set()
    def draw(pool, k):
        random.shuffle(pool)
        for r in pool:
            if len(picked) >= a.n: return
            if r["arxiv_id"] in seen: continue
            seen.add(r["arxiv_id"]); picked.append(r); k -= 1
            if k <= 0: return
    fams = sorted({r["family"] for r in rows}); tasks = sorted({r["task"] for r in rows})
    for f in fams: draw([r for r in rows if r["family"] == f], 11)
    for t in tasks: draw([r for r in rows if r["task"] == t], 6)
    draw(list(rows), a.n - len(picked))
    with open(OUT, "w", newline="") as f:
        wtr = csv.writer(f)
        wtr.writerow(["arxiv_id", "title", "abstract", "family_rule", "task_rule", "family_true", "task_true"])
        for r in picked:
            wtr.writerow([r["arxiv_id"], r["title"], r["summary"][:700], r["family"], r["task"], "", ""])
    print(f"wrote {OUT} ({len(picked)} rows)")
    print("rule family:", Counter(r["family"] for r in picked).most_common())
    print("rule task:  ", Counter(r["task"] for r in picked).most_common())

if __name__ == "__main__":
    main()
