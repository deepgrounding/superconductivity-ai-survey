#!/usr/bin/env python3
"""Figures that encode editorial judgement rather than corpus counts.

  Fig 1  the taxonomy schematic: family x task grid with the AI lens shown as the
         third dimension, drawn programmatically so it can never drift from the
         label vocabulary the corpus actually uses.
  Fig 5  the AI-readiness matrix: per-cell scores for data availability, benchmark
         maturity, validation cost and the binding bottleneck.

Fig 5's scores are AUTHOR JUDGEMENT, not measurements. They live in READINESS
below, one row per (family, task) cell that the survey discusses, and the paper
must say so in the caption and carry the rationale in an appendix.

Usage: python draft/scripts/build_concept_figures.py
"""
import csv
from collections import Counter
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "artifacts" / "sc_corpus_v1.csv"
FIG = ROOT / "draft" / "figures"
FIG.mkdir(exist_ok=True)

FAMILIES = ["conv", "cuprate", "febased", "nickelate", "unconv_other", "lowd", "topo", "device", "general"]
FLABEL = {"conv": "Conventional\n& hydrides", "cuprate": "Cuprates", "febased": "Iron-based",
          "nickelate": "Nickelates", "unconv_other": "Other\nunconventional",
          "lowd": "2D / interface\n/ moiré", "topo": "Topological", "device": "Devices",
          "general": "Material-agnostic\ntheory & method"}
TASKS = ["theory", "abinitio", "discovery", "synthesis", "characterization"]
TLABEL = {"theory": "Theory", "abinitio": "Ab initio", "discovery": "Discovery",
          "synthesis": "Synthesis", "characterization": "Characterization"}
INK, INK2, INK3 = "#0b0b0b", "#52514e", "#8a8985"
RULE = "#dedcd7"
plt.rcParams.update({"font.size": 9, "figure.dpi": 200, "savefig.dpi": 200})

def corpus_counts():
    """Seed counts per label, so Figure 1 states the taxonomy AND its occupancy.
    Seed only, off-topic excluded -- the same basis as Table 1, so the two agree."""
    rows = [r for r in csv.DictReader(open(CORPUS))
            if r.get("off_topic") != "true" and r.get("source") == "seed"]
    ai = [r for r in csv.DictReader(open(CORPUS)) if r.get("off_topic") != "true"]
    return (Counter(r["family"] for r in rows), Counter(r["task"] for r in rows),
            Counter(r["ai_method"] for r in ai if r["ai_method"] not in ("", "none")),
            len(rows), len(ai))

# --- Fig 4 scores: 0-3 (0 = absent, 3 = mature). AUTHOR JUDGEMENT, see appendix. ---
# data      : is there enough labelled, machine-readable data to train or evaluate on?
# benchmark : does a shared task with an accepted metric exist?
# cheap     : how cheap is it to check a prediction? (3 = a calculation, 0 = a hard experiment)
# bottleneck: what actually blocks progress in this cell
READINESS = {
    ("conv", "abinitio"):            (3, 2, 3, "compute"),
    ("conv", "discovery"):           (3, 2, 2, "data"),
    ("conv", "synthesis"):           (1, 0, 0, "experiment"),
    ("conv", "characterization"):    (2, 1, 2, "data"),
    ("conv", "theory"):              (2, 1, 3, "theory"),
    ("cuprate", "theory"):           (1, 0, 2, "theory"),
    ("cuprate", "characterization"): (2, 1, 2, "data"),
    ("nickelate", "abinitio"):       (2, 1, 3, "theory"),
    ("nickelate", "synthesis"):      (1, 0, 0, "experiment"),
    ("lowd", "characterization"):    (2, 1, 1, "data"),
    ("lowd", "synthesis"):           (1, 0, 0, "experiment"),
    ("topo", "characterization"):    (1, 0, 1, "theory"),
    ("device", "characterization"):  (3, 2, 2, "data"),
    ("device", "synthesis"):         (2, 1, 1, "experiment"),
    ("general", "theory"):           (2, 2, 3, "compute"),
}
BCOLOR = {"data": "#4C72B0", "compute": "#55A868", "theory": "#C44E52", "experiment": "#DD8452"}

def fig1_taxonomy():
    """Horizontal bars, sorted descending, one block per axis.

    The card layout this replaces printed the counts as text, which made the reader do
    the comparison arithmetic. Length is the encoding people read fastest, so the same
    numbers are now bars: theory's dominance, the thinness of synthesis and discovery,
    and the single autonomous-experiment paper all land without reading a digit. The
    descriptors stay, because Figure 1 also has to define the vocabulary that Sections
    3 to 6 use. Each block carries its own scale -- they are different populations --
    and the scale is stated on each block.
    """
    fam_ct, task_ct, ai_ct, n_seed, n_work = corpus_counts()
    FAM = [
        ("conv", "Conventional & hydrides", "electron-phonon; H$_3$S, LaH$_{10}$, MgB$_2$, nitrides"),
        ("cuprate", "Cuprates", "YBCO, BSCCO, LSCO, Hg- and Tl-based"),
        ("febased", "Iron-based", "pnictides and chalcogenides; FeSe, BaFe$_2$As$_2$"),
        ("nickelate", "Nickelates", "infinite-layer and Ruddlesden-Popper; La$_3$Ni$_2$O$_7$"),
        ("unconv_other", "Other unconventional", "heavy fermion, Sr$_2$RuO$_4$, organics, UTe$_2$"),
        ("lowd", "2D / interface / moir\u00e9", "twisted graphene, kagome, TMDs, oxide interfaces"),
        ("topo", "Topological", "Majorana platforms, proximitised hybrids"),
        ("device", "Devices", "qubits, detectors, magnets, cables, circuits"),
        ("general", "Material-agnostic theory & method", "formalism, pairing and vortex theory, instrumentation"),
    ]
    TASK = [
        ("theory", "Theory", "models, formalism, many-body numerics"),
        ("abinitio", "Ab initio", "DFT, electron-phonon, Eliashberg on real compounds"),
        ("discovery", "Discovery", "new superconductors; screening and inverse design"),
        ("synthesis", "Synthesis", "growth, films, topotactic routes, fabrication"),
        ("characterization", "Characterization", "ARPES, STM, neutron, transport, device metrology"),
    ]
    AI = [("surrogate", "Surrogate / regression", "regression, boosting, symbolic regression"),
          ("gnn_potential", "GNN & ML potentials", "graph networks, machine-learned potentials"),
          ("generative", "Generative models", "diffusion, VAE, flows over structures"),
          ("llm", "LLM / agents", "language models, agents, literature mining"),
          ("nqs", "Neural quantum states", "neural wavefunctions for correlated models"),
          ("autonomous_exp", "Autonomous experiment", "self-driving labs, closed-loop active learning")]

    blocks = [
        ("Axis 1  \u00b7  Material family", "what the paper is about \u2014 one label per paper",
         [(n, d, fam_ct.get(k, 0)) for k, n, d in FAM], "#2a78d6", n_seed, "seed corpus"),
        ("Axis 2  \u00b7  Mode of inquiry",
         "how the work was done \u2014 one label per paper; application context is carried by the Devices family",
         [(n, d, task_ct.get(k, 0)) for k, n, d in TASK], "#1baf7a", n_seed, "seed corpus"),
        ("AI lens  \u00b7  method used",
         "only for papers that use an AI/ML method in their own work",
         [(n, d, ai_ct.get(k, 0)) for k, n, d in AI], "#4a3aa7", n_work, "working corpus"),
    ]

    # Kept compact on purpose: at \textwidth this must fit one page WITH its caption,
    # so the row pitch is sized from the page budget, not from what looks airy alone.
    ROW, BLOCK_PAD, BARH = 0.315, 0.66, 0.175
    total_rows = sum(len(b[2]) for b in blocks)
    fig_h = total_rows * ROW + len(blocks) * BLOCK_PAD + 0.55
    fig, ax = plt.subplots(figsize=(7.8, fig_h))
    y = [0.0]
    LEFT = 0.0                      # label column occupies x in [-1, 0); bars grow from 0
    BARW = 1.02                     # bars span x in [0, 1.02]; the value label sits just
                                    # past the tip and the share column is fixed at 1.30

    for title, sub, rows_, color, denom, denom_name in blocks:
        ax.text(-1.0, y[0], title, fontsize=10, fontweight="bold", color=INK, va="top")
        y[0] -= 0.24
        ax.text(-1.0, y[0], sub, fontsize=7.6, color=INK2, va="top", style="italic")
        y[0] -= 0.34
        rows_ = sorted(rows_, key=lambda r: -r[2])
        vmax = max(r[2] for r in rows_) or 1
        for name, desc, v in rows_:
            yc = y[0] - ROW / 2
            ax.text(-0.02, yc + 0.048, name, fontsize=8.2, fontweight="bold", color=INK,
                    ha="right", va="center")
            ax.text(-0.02, yc - 0.088, desc, fontsize=6.4, color=INK3, ha="right", va="center")
            w = BARW * v / vmax * 0.92
            ax.add_patch(FancyBboxPatch((LEFT, yc - BARH / 2), max(w, 0.004), BARH,
                                        boxstyle="round,pad=0,rounding_size=0.012",
                                        mutation_aspect=0.35, facecolor=color,
                                        edgecolor="none", zorder=2))
            # value sits at the bar tip; the share goes in a FIXED column, because
            # offsetting it from the value made the two collide on the longest bars
            ax.text(LEFT + w + 0.016, yc, f"{v:,}", fontsize=8.1, fontweight="bold",
                    color=INK, ha="left", va="center")
            ax.text(1.30, yc, f"{v / denom:.1%}", fontsize=7.2, color=INK3,
                    ha="right", va="center")
            y[0] -= ROW
        ax.text(-1.0, y[0] - 0.06,
                f"bars scaled within this block \u00b7 largest = {vmax:,} \u00b7 "
                f"share of the {denom_name} (n = {denom:,})",
                fontsize=6.7, color=INK3, va="top")
        y[0] -= BLOCK_PAD

    ax.set_xlim(-1.06, 1.34); ax.set_ylim(y[0] + 0.55, 0.34); ax.axis("off")
    fig.tight_layout(); fig.savefig(FIG / "fig1_taxonomy.png", bbox_inches="tight")
    plt.close(fig)
    print("wrote fig1_taxonomy.png")

def fig4_readiness():
    cells = list(READINESS.items())
    M = np.array([[v[0], v[1], v[2]] for _, v in cells], dtype=float)
    labels = [f"{FLABEL[f].replace(chr(10), ' ')} × {TLABEL[t]}" for (f, t), _ in cells]
    order = np.argsort(-M.sum(axis=1))
    M, labels = M[order], [labels[i] for i in order]
    bots = [cells[i][1][3] for i in order]
    from matplotlib.colors import LinearSegmentedColormap
    # single-hue sequential: 0-3 is a magnitude, so lightness does the work
    BLUES = LinearSegmentedColormap.from_list("sc_blue",
                                              ["#eef4fb", "#bcd6f2", "#6fa5e0", "#2a78d6", "#14508f"])
    fig, ax = plt.subplots(figsize=(7.6, 5.6))
    im = ax.imshow(M, cmap=BLUES, vmin=0, vmax=3, aspect="auto")
    ax.set_xticks(range(3))
    ax.set_xticklabels(["Data\navailability", "Benchmark\nmaturity", "Cheap\nvalidation"],
                       fontsize=8.5, color=INK2)
    ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels, fontsize=8, color=INK)
    ax.tick_params(length=0)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, int(M[i, j]), ha="center", va="center", fontsize=8.5,
                    color="white" if M[i, j] >= 2.0 else INK)
        ax.text(3.05, i, bots[i], ha="left", va="center", fontsize=8, color=BCOLOR[bots[i]], fontweight="bold")
    ax.set_xlim(-0.5, 4.55); ax.set_ylim(len(labels) - 0.5, -0.5)
    for sp in ("top", "right", "bottom", "left"): ax.spines[sp].set_visible(False)
    ax.text(3.05, -0.72, "binding bottleneck", ha="left", va="bottom", fontsize=7.6,
            fontweight="bold", color=INK2)
    ax.text(0, 1.10, "AI readiness by taxonomy cell", transform=ax.transAxes,
            fontsize=10.5, fontweight="bold", color=INK, va="bottom")
    ax.text(0, 1.055, "0 = absent, 3 = mature \u2014 author judgement, not measurement",
            transform=ax.transAxes, fontsize=8, color=INK2, va="bottom", style="italic")
    cb = fig.colorbar(im, ax=ax, shrink=0.55, ticks=[0, 1, 2, 3], pad=0.14)
    cb.outline.set_visible(False); cb.ax.tick_params(length=0, labelsize=8, colors=INK2)
    fig.tight_layout(); fig.savefig(FIG / "fig5_ai_readiness.png", bbox_inches="tight"); plt.close(fig)
    print("wrote fig5_ai_readiness.png")

if __name__ == "__main__":
    fig1_taxonomy(); fig4_readiness()
