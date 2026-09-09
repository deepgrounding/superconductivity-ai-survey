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
          "topo": "Topological", "device": "Devices", "general": "Material-agnostic"}
# Categorical slots 1-8 of the validated reference palette, assigned in fixed order.
# The ninth family cannot take a generated hue, so it takes the neutral slot and every
# cluster is DIRECT-LABELLED in Figure 2 -- identity is never carried by colour alone.
FCOLOR = {"conv": "#2a78d6", "cuprate": "#eb6834", "febased": "#1baf7a",
          "nickelate": "#e34948", "unconv_other": "#4a3aa7", "lowd": "#8a6f4e",
          "topo": "#e87ba4", "device": "#6b6b6b", "general": "#eda100"}
SERIES = "#2a78d6"      # single hue for small multiples: panels are separated in space,
ACCENT = "#e34948"      # so colour carries no identity load
INK, INK2, INK3 = "#0b0b0b", "#52514e", "#8a8985"
GRID = "#e6e5e2"
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
    """Semantic map with non-overlapping direct labels.

    Two label bugs were fixed here. (1) Labels were placed at each family's MEDIAN
    point, which for a bimodal family lands in empty space between its two blobs;
    they now sit at the family's density peak, computed on a coarse 2-D histogram.
    (2) Labels were drawn wherever they fell and several collided; a simple
    box-repulsion pass now separates them, and any label pushed off its anchor keeps
    a leader line back to it. Direct labels are load-bearing here, not decorative:
    nine categorical hues cannot clear the all-pairs colour gates, so the label is
    what carries identity and the colour is only an aid.
    """
    docs = [r["title"] + ". " + r["summary"] for r in rows]
    X = TfidfVectorizer(max_features=30000, sublinear_tf=True, stop_words="english",
                        ngram_range=(1, 2), min_df=5, max_df=0.4).fit_transform(docs)
    Z = normalize(TruncatedSVD(60, random_state=0).fit_transform(X))
    P = TSNE(2, perplexity=40, init="pca", random_state=0, max_iter=1000).fit_transform(Z)

    fig, ax = plt.subplots(figsize=(7.4, 6.2))
    fam_pts = {}
    for f in FAMILIES:
        m = np.array([r["family"] == f for r in rows])
        if m.sum() == 0: continue
        fam_pts[f] = P[m]
        ax.scatter(P[m, 0], P[m, 1], s=2.6, c=FCOLOR[f], alpha=0.42, linewidths=0,
                   label=f"{FLABEL[f]} ({m.sum()})")

    def density_peak(pts):
        """Densest cell of a coarse histogram -- a point the family actually occupies."""
        H, xe, ye = np.histogram2d(pts[:, 0], pts[:, 1], bins=14)
        i, j = np.unravel_index(H.argmax(), H.shape)
        return (xe[i] + xe[i + 1]) / 2, (ye[j] + ye[j + 1]) / 2

    xr = P[:, 0].max() - P[:, 0].min(); yr = P[:, 1].max() - P[:, 1].min()
    anchors = {f: density_peak(pts) for f, pts in fam_pts.items()}
    pos = {f: list(a) for f, a in anchors.items()}
    # approximate label half-extents in data units, from the string length
    half = {f: (0.011 * xr * len(FLABEL[f]) + 0.012 * xr, 0.030 * yr) for f in pos}

    for _ in range(400):                       # iterative box repulsion
        moved = False
        keys = list(pos)
        for i, f in enumerate(keys):
            for g in keys[i + 1:]:
                dx = pos[f][0] - pos[g][0]; dy = pos[f][1] - pos[g][1]
                ox = half[f][0] + half[g][0] - abs(dx)
                oy = half[f][1] + half[g][1] - abs(dy)
                if ox > 0 and oy > 0:          # boxes intersect -> push apart on the
                    moved = True               # axis needing the smaller correction
                    if oy / (half[f][1] + half[g][1]) < ox / (half[f][0] + half[g][0]):
                        sh = (oy / 2 + 0.004 * yr) * (1 if dy >= 0 else -1)
                        pos[f][1] += sh; pos[g][1] -= sh
                    else:
                        sh = (ox / 2 + 0.004 * xr) * (1 if dx >= 0 else -1)
                        pos[f][0] += sh; pos[g][0] -= sh
        if not moved: break

    for f, (lx, ly) in pos.items():
        ax0, ay0 = anchors[f]
        if np.hypot((lx - ax0) / xr, (ly - ay0) / yr) > 0.035:
            ax.plot([ax0, lx], [ay0, ly], color=FCOLOR[f], lw=0.7, alpha=0.6, zorder=3)
            ax.plot([ax0], [ay0], "o", ms=3.2, color=FCOLOR[f], zorder=4)
        ax.text(lx, ly, FLABEL[f], fontsize=8.4, fontweight="bold", ha="center", va="center",
                color=INK, zorder=6,
                bbox=dict(boxstyle="round,pad=0.30", fc="white", ec=FCOLOR[f], lw=1.1, alpha=0.95))

    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_color(GRID)
    ax.set_xlabel("t-SNE dimension 1", fontsize=8.5, color=INK2)
    ax.set_ylabel("t-SNE dimension 2", fontsize=8.5, color=INK2)
    leg = ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False,
                    markerscale=4.5, fontsize=7.6, labelspacing=0.62,
                    title="seed corpus, coloured by family", title_fontsize=8)
    leg.get_title().set_color(INK2)
    fig.tight_layout(); fig.savefig(FIG / "fig2_semantic_map.png", bbox_inches="tight")
    plt.close(fig)
    print("wrote fig2_semantic_map.png")

def quarters(rows):
    out = {}
    for r in rows:
        d = r["pub_date"][:7]
        if not d: continue
        y, m = int(d[:4]), int(d[5:7])
        out[r["arxiv_id"]] = f"{y}Q{(m - 1) // 3 + 1}"
    return out

def _series(rows, key, labels, idx):
    y = np.zeros(len(labels))
    q = quarters(rows)
    for r in rows:
        if r.get(idx) == key and q.get(r["arxiv_id"]) in labels:
            y[labels.index(q[r["arxiv_id"]])] += 1
    return y

def fig_growth(seed):
    """Small multiples, not a 9-line overlay.

    Nine series on one axis is the spaghetti anti-pattern: every family sat in the
    same 20-130 band and nothing could be read off it. Faceting gives each family its
    own panel on a SHARED y-scale, so magnitude stays comparable while shape becomes
    legible, and panels are ordered by growth so the ranking is the first thing read.
    A single hue is used throughout: panels are separated in space, so colour would
    carry no information (and nine categorical hues cannot clear the all-pairs gates).
    """
    q = quarters(seed)
    labels = sorted({v for v in q.values()})
    labels = labels[1:-1] if len(labels) > 2 else labels   # drop both partial endpoints

    def growth(y):
        first, last = y[:4].mean(), y[-4:].mean()
        return (last - first) / first if first else 0.0

    fam_y = {f: _series(seed, f, labels, "family") for f in FAMILIES}
    task_y = {t: _series(seed, t, labels, "task") for t in TASKS}
    fam_order = sorted(FAMILIES, key=lambda f: -growth(fam_y[f]))
    task_order = sorted(TASKS, key=lambda t: -growth(task_y[t]))

    fig = plt.figure(figsize=(7.4, 7.9))
    gs = fig.add_gridspec(5, 3, height_ratios=[1, 1, 1, 0.46, 1.0], hspace=0.70, wspace=0.17)
    x = np.arange(len(labels))
    ticks = [i for i, l in enumerate(labels) if l.endswith("Q1")]
    fam_max = max(v.max() for v in fam_y.values())

    def panel(ax, y, title, sub, ymax, annotate=None):
        ax.fill_between(x, y, color=SERIES, alpha=0.16, linewidth=0)
        ax.plot(x, y, color=SERIES, lw=1.6, solid_capstyle="round")
        ax.set_ylim(0, ymax * 1.20); ax.set_xlim(0, len(labels) - 1)
        ax.set_yticks([0, int(ymax)]); ax.tick_params(labelsize=7, length=2, colors=INK3)
        for sp in ("top", "right"): ax.spines[sp].set_visible(False)
        for sp in ("left", "bottom"): ax.spines[sp].set_color(GRID)
        ax.set_xticks(ticks)
        ax.set_title(title, fontsize=8.6, fontweight="bold", color=INK, loc="left", pad=10)
        ax.text(0, 1.020, sub, transform=ax.transAxes, fontsize=7.1, color=INK2, va="bottom")
        if annotate:
            i, txt = annotate
            ax.plot([i], [y[i]], "o", ms=4, color=ACCENT, zorder=5)
            ax.annotate(txt, (i, y[i]), textcoords="offset points", xytext=(4, -1),
                        fontsize=7, color=ACCENT, fontweight="bold")

    fig.text(0.008, 0.992, "(a) Material families", fontsize=10, fontweight="bold", color=INK)
    fig.text(0.008, 0.973,
             "preprints per quarter, seed corpus \u2014 shared vertical scale, ordered by growth",
             fontsize=7.6, color=INK2)
    spike = labels.index("2023Q3") if "2023Q3" in labels else None
    for i, f in enumerate(fam_order):
        ax = fig.add_subplot(gs[i // 3, i % 3])
        g = growth(fam_y[f])
        panel(ax, fam_y[f], FLABEL[f],
              f"{g:+.0%} · {int(fam_y[f].sum())} papers", fam_max,
              annotate=(spike, "LK-99") if (f == "cuprate" and spike is not None) else None)
        if i // 3 == 2:
            ax.set_xticklabels([labels[t][:4] for t in ticks], fontsize=6.8, color=INK3)
        else:
            ax.set_xticklabels([])

    fig.text(0.008, 0.292, "(b) Modes of inquiry", fontsize=10, fontweight="bold", color=INK)
    fig.text(0.008, 0.273,
             "independent vertical scales \u2014 each panel's maximum is printed; discovery is the "
             "only mode that shrinks",
             fontsize=7.6, color=INK2)
    gs2 = gs[4, :].subgridspec(1, 5, wspace=0.42)
    for i, t in enumerate(task_order):
        ax = fig.add_subplot(gs2[0, i])
        g = growth(task_y[t])
        panel(ax, task_y[t], TLABEL[t], f"{g:+.0%} \u00b7 {int(task_y[t].sum())} papers",
              task_y[t].max())
        ax.set_xticklabels([labels[k][:4] for k in ticks], fontsize=6.4, color=INK3, rotation=45,
                           ha="right")
    fig.subplots_adjust(top=0.905, bottom=0.05, left=0.075, right=0.985)
    fig.savefig(FIG / "fig3_growth_timeline.png", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote fig3_growth_timeline.png ({len(labels)} complete quarters, seed only)")
    print("  family growth:", ", ".join(f"{f} {growth(fam_y[f]):+.0%}" for f in fam_order))
    print("  mode growth:  ", ", ".join(f"{t} {growth(task_y[t]):+.0%}" for t in task_order))

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
                     + f" | {tot} | {sup_ct.get(f, 0)} |")
    # No boldface: arXiv moderators flag emphasis in body text and table cells, and
    # the Seed column and Total row are already distinguished structurally.
    lines.append("| Total | " + " | ".join(str(sum(ct[(f, t)] for f in FAMILIES)) for t in TASKS)
                 + f" | {sum(ct.values())} | {len(supp)} |")
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
