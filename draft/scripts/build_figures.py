#!/usr/bin/env python3
"""Figures + Table 1 for the superconductivity survey.

  Fig 2  semantic map: TF-IDF -> SVD -> t-SNE, coloured by family, direct labels
  Fig 3  growth timeline (SEED ROWS ONLY - supplements are recency-biased):
         (a) quarterly submissions by family, (b) by task
  Fig 4  AI-method x task matrix over AI-tagged rows (seed + T1 supplement)
  Table 1  family x task counts -> draft/table1.md

Fig 1 (taxonomy schematic) and Fig 5 (AI-readiness matrix) are built by
build_concept_figures.py because they encode editorial judgement, not corpus counts.

Usage: python draft/scripts/build_figures.py
"""
import csv
from collections import Counter
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.manifold import TSNE
from sklearn.preprocessing import normalize

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "artifacts" / "sc_corpus_v1.csv"
FIG = ROOT / "draft" / "figures"
FIG.mkdir(exist_ok=True)

FAMILIES = ["conv", "cuprate", "febased", "nickelate", "unconv_other", "lowd", "topo", "device", "general"]
FLABEL = {"conv": "Conventional / hydrides", "cuprate": "Cuprates", "febased": "Iron-based",
          "nickelate": "Nickelates", "unconv_other": "Other unconventional", "lowd": "2D / interface / moiré",
          "topo": "Topological", "device": "Devices & applications", "general": "Cross-family"}
FCOLOR = {"conv": "#4C72B0", "cuprate": "#DD8452", "febased": "#55A868", "nickelate": "#C44E52",
          "unconv_other": "#8172B3", "lowd": "#937860", "topo": "#DA8BC3", "device": "#8C8C8C",
          "general": "#CCB974"}
TASKS = ["theory", "abinitio", "discovery", "synthesis", "characterization"]
TLABEL = {"theory": "Theory", "abinitio": "Ab initio", "discovery": "Discovery",
          "synthesis": "Synthesis", "characterization": "Characterization"}
AI = ["surrogate", "gnn_potential", "generative", "llm", "nqs", "autonomous_exp"]
ALABEL = {"surrogate": "Surrogate / regression", "gnn_potential": "GNN & ML potentials",
          "generative": "Generative models", "llm": "LLM / agents",
          "nqs": "Neural quantum states", "autonomous_exp": "Autonomous experiment"}
plt.rcParams.update({"font.size": 9, "figure.dpi": 200, "savefig.dpi": 200,
                     "axes.spines.top": False, "axes.spines.right": False})

def load():
    return list(csv.DictReader(open(CORPUS)))

# NOTE: main() drops off_topic rows. They are counted and reported as the corpus's
# quantified bleed in the Method section, never folded into family x task statistics.

def fig_map(rows):
    docs = [r["title"] + ". " + r["summary"] for r in rows]
    X = TfidfVectorizer(max_features=30000, sublinear_tf=True, stop_words="english",
                        ngram_range=(1, 2), min_df=5, max_df=0.4).fit_transform(docs)
    Z = normalize(TruncatedSVD(60, random_state=0).fit_transform(X))
    P = TSNE(2, perplexity=40, init="pca", random_state=0, max_iter=1000).fit_transform(Z)
    fig, ax = plt.subplots(figsize=(7.2, 6.0))
    for f in FAMILIES:
        m = np.array([r["family"] == f for r in rows])
        if m.sum() == 0: continue
        ax.scatter(P[m, 0], P[m, 1], s=2.5, c=FCOLOR[f], alpha=0.45, linewidths=0, label=f"{FLABEL[f]} ({m.sum()})")
        cx, cy = np.median(P[m, 0]), np.median(P[m, 1])
        ax.text(cx, cy, FLABEL[f], fontsize=8.5, fontweight="bold", ha="center", va="center",
                color="black", bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=FCOLOR[f], lw=1.0, alpha=0.88))
    ax.set_xticks([]); ax.set_yticks([]); ax.set_xlabel("t-SNE dimension 1"); ax.set_ylabel("t-SNE dimension 2")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False, markerscale=4, fontsize=7.5)
    fig.tight_layout(); fig.savefig(FIG / "fig2_semantic_map.png", bbox_inches="tight"); plt.close(fig)
    print("wrote fig2_semantic_map.png")

def quarters(rows):
    out = {}
    for r in rows:
        d = r["pub_date"][:7]
        if not d: continue
        y, m = int(d[:4]), int(d[5:7])
        out.setdefault(r["arxiv_id"], f"{y}Q{(m - 1) // 3 + 1}")
    return out

def fig_growth(seed):
    q = quarters(seed)
    labels = sorted({v for v in q.values()})
    labels = labels[1:-1] if len(labels) > 2 else labels   # drop both partial endpoint quarters
    idx = {l: i for i, l in enumerate(labels)}
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 6.4), sharex=True)
    for ax, keys, kl, colors, title in [
        (axes[0], FAMILIES, FLABEL, FCOLOR, "(a) by material family"),
        (axes[1], TASKS, TLABEL, None, "(b) by research task")]:
        for i, k in enumerate(keys):
            y = np.zeros(len(labels))
            for r in seed:
                if r.get("family" if keys is FAMILIES else "task") == k and q.get(r["arxiv_id"]) in idx:
                    y[idx[q[r["arxiv_id"]]]] += 1
            c = colors[k] if colors else plt.cm.viridis(i / max(1, len(keys) - 1))
            ax.plot(range(len(labels)), y, lw=1.6, color=c, label=kl[k])
        ax.set_title(title, fontsize=9, loc="left")
        ax.set_ylabel("preprints per quarter")
        ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False, fontsize=7.5)
    axes[1].set_xticks(range(0, len(labels), 2)); axes[1].set_xticklabels(labels[::2], rotation=45, ha="right")
    fig.tight_layout(); fig.savefig(FIG / "fig3_growth_timeline.png", bbox_inches="tight"); plt.close(fig)
    print(f"wrote fig3_growth_timeline.png ({len(labels)} complete quarters, seed rows only)")

def fig_ai(rows):
    ai_rows = [r for r in rows if r.get("ai_method") not in ("", "none")]
    M = np.zeros((len(AI), len(TASKS)))
    for r in ai_rows:
        if r["ai_method"] in AI and r["task"] in TASKS:
            M[AI.index(r["ai_method"]), TASKS.index(r["task"])] += 1
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    im = ax.imshow(M, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(TASKS))); ax.set_xticklabels([TLABEL[t] for t in TASKS], rotation=30, ha="right")
    ax.set_yticks(range(len(AI))); ax.set_yticklabels([ALABEL[a] for a in AI])
    for i in range(len(AI)):
        for j in range(len(TASKS)):
            if M[i, j]:
                ax.text(j, i, int(M[i, j]), ha="center", va="center", fontsize=8,
                        color="white" if M[i, j] > M.max() * 0.6 else "black")
    ax.set_title(f"AI method by research task (n = {len(ai_rows)} AI-tagged preprints)", fontsize=9, loc="left")
    fig.colorbar(im, ax=ax, shrink=0.85, label="preprints")
    fig.tight_layout(); fig.savefig(FIG / "fig4_ai_method_task.png", bbox_inches="tight"); plt.close(fig)
    print(f"wrote fig4_ai_method_task.png (n={len(ai_rows)})")

def table1(rows):
    """Table 1 reports the SEED corpus only -- it is the systematically harvested,
    sampling-comparable half, and it is what Figure 3 plots. Supplement rows are
    recency-biased by construction and appear as a separate column, never folded
    into the family x task counts."""
    seed = [r for r in rows if r["source"] == "seed"]
    supp = [r for r in rows if r["source"] != "seed"]
    ct = Counter((r["family"], r["task"]) for r in seed)
    sup_ct = Counter(r["family"] for r in supp)
    # compact headers and family names: the full labels overflow the text block in
    # the PDF build and collide with the neighbouring column
    THEAD = {"theory": "Theory", "abinitio": "Ab init.", "discovery": "Discov.",
             "synthesis": "Synth.", "characterization": "Charac."}
    FSHORT = {"conv": "Conventional", "cuprate": "Cuprate", "febased": "Iron-based",
              "nickelate": "Nickelate", "unconv_other": "Other unconv.",
              "lowd": "2D / moiré", "topo": "Topological", "device": "Devices",
              "general": "Material-agnostic"}
    lines = ["| Family | " + " | ".join(THEAD[t] for t in TASKS) + " | Seed | Suppl. |",
             "|:---|" + "---:|" * (len(TASKS) + 2)]
    for f in FAMILIES:
        tot = sum(ct[(f, t)] for t in TASKS)
        lines.append(f"| {FSHORT[f]} | " + " | ".join(str(ct[(f, t)]) for t in TASKS)
                     + f" | **{tot}** | {sup_ct.get(f, 0)} |")
    lines.append("| **Total** | " + " | ".join(f"**{sum(ct[(f, t)] for f in FAMILIES)}**" for t in TASKS)
                 + f" | **{sum(ct.values())}** | **{len(supp)}** |")
    txt = "\n".join(lines)
    (ROOT / "draft" / "table1.md").write_text(txt + "\n")
    print("\n" + txt)
    print(f"\nseed {len(seed)}; supplement {len(supp)}; corpus {len(rows)}")

def main():
    rows = [r for r in load() if r.get("off_topic") != "true"]
    seed = [r for r in rows if r["source"] == "seed"]
    # Fig 2 uses seed rows only so its per-family counts match Table 1 exactly.
    table1(rows); fig_growth(seed); fig_ai(rows); fig_map(seed)

if __name__ == "__main__":
    main()
