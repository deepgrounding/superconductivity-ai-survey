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
from matplotlib.patches import Rectangle
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
            len(rows))

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
    """Card layout: each label carries its descriptor and its seed-corpus count, so the
    figure states the taxonomy and its occupancy in one read. Cards use a coloured left
    rule rather than a tinted fill -- at nine categories a tint reads as nine competing
    blocks, while a rule keeps the surface calm and still carries the family colour."""
    fam_ct, task_ct, ai_ct, n_seed = corpus_counts()
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
    AI = [("surrogate", "Surrogate / regression"), ("gnn_potential", "GNN & ML potentials"),
          ("generative", "Generative models"), ("llm", "LLM / agents"),
          ("nqs", "Neural quantum states"), ("autonomous_exp", "Autonomous experiment")]
    FCOLOR = {"conv": "#2a78d6", "cuprate": "#eb6834", "febased": "#1baf7a",
              "nickelate": "#e34948", "unconv_other": "#4a3aa7", "lowd": "#8a6f4e",
              "topo": "#e87ba4", "device": "#6b6b6b", "general": "#eda100"}
    TCOLOR = "#2a78d6"; ACOLOR = "#4a3aa7"

    W, GAP, CH = 4.86, 0.20, 0.70
    fig, ax = plt.subplots(figsize=(7.8, 7.2))
    cur = [0.0]

    def heading(title, sub):
        ax.text(0.0, cur[0], title, fontsize=10.5, fontweight="bold", color=INK, va="top")
        cur[0] -= 0.30
        ax.text(0.0, cur[0], sub, fontsize=8.0, color=INK2, va="top", style="italic")
        cur[0] -= 0.40

    def card(x, top, w, name, desc, count, color, h=CH):
        ax.add_patch(Rectangle((x, top - h), w, h, facecolor="#ffffff", edgecolor=RULE,
                               lw=0.9, zorder=1))
        ax.add_patch(Rectangle((x, top - h), 0.055, h, facecolor=color, edgecolor="none",
                               zorder=2))
        ty = top - h / 2 + (0.115 if desc else 0)
        ax.text(x + 0.20, ty, name, fontsize=8.7, fontweight="bold", color=INK, va="center")
        if desc:
            ax.text(x + 0.20, top - h / 2 - 0.145, desc, fontsize=6.9, color=INK2, va="center")
        if count is not None:
            ax.text(x + w - 0.16, top - h / 2, f"{count:,}", fontsize=8.6, color=INK3,
                    va="center", ha="right", fontweight="bold")

    heading("Axis 1  \u00b7  Material family", "one label per paper")
    for i, (k, name, desc) in enumerate(FAM):
        x = (i % 2) * (W + GAP); top = cur[0] - (i // 2) * (CH + 0.12)
        card(x, top, W, name, desc, fam_ct.get(k, 0), FCOLOR[k])
    cur[0] -= 5 * (CH + 0.12) + 0.50

    heading("Axis 2  \u00b7  Mode of inquiry",
            "one label per paper; application context is carried by the Devices family")
    for i, (k, name, desc) in enumerate(TASK):
        x = (i % 2) * (W + GAP); top = cur[0] - (i // 2) * (CH + 0.12)
        card(x, top, W, name, desc, task_ct.get(k, 0), TCOLOR)
    cur[0] -= 3 * (CH + 0.12) + 0.50

    heading("AI lens  \u00b7  method used",
            "only for papers that use an AI/ML method in their own work")
    aw = (2 * W + GAP - 2 * 0.14) / 3
    for i, (k, name) in enumerate(AI):
        x = (i % 3) * (aw + 0.14); top = cur[0] - (i // 3) * (0.50 + 0.12)
        card(x, top, aw, name, "", ai_ct.get(k, 0), ACOLOR, h=0.50)
    cur[0] -= 2 * (0.50 + 0.12) + 0.30

    ax.text(0.0, cur[0], f"counts are seed-corpus papers per label (n = {n_seed:,}); "
            f"the AI lens counts the whole working corpus", fontsize=7.2, color=INK3, va="top")
    cur[0] -= 0.34
    ax.set_xlim(-0.06, 2 * W + GAP + 0.06); ax.set_ylim(cur[0], 0.42); ax.axis("off")
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
