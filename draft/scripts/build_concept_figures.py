#!/usr/bin/env python3
"""Figures that encode editorial judgement rather than corpus counts.

  Fig 1  the taxonomy schematic: family x task grid with the AI lens shown as the
         third dimension, drawn programmatically so it can never drift from the
         label vocabulary the corpus actually uses.
  Fig 4  the AI-readiness matrix: per-cell scores for data availability, benchmark
         maturity, validation cost and the binding bottleneck.

Fig 4's scores are AUTHOR JUDGEMENT, not measurements. They live in READINESS
below, one row per (family, task) cell that the survey discusses, and the paper
must say so in the caption and carry the rationale in an appendix.

Usage: python draft/scripts/build_concept_figures.py
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
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
plt.rcParams.update({"font.size": 9, "figure.dpi": 200, "savefig.dpi": 200})

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
    """Three-band schematic: every corpus paper carries one label from each of the two
    axes; AI-tagged papers carry a method from the lens as well. Drawn as chips rather
    than a grid because most family x task cells are populated, so a sparse shaded
    grid would misrepresent the taxonomy as a set of chosen cells."""
    FAM_DESC = [
        ("Conventional & hydrides", "electron-phonon; H$_3$S, LaH$_{10}$, MgB$_2$, nitrides, alloys"),
        ("Cuprates", "YBCO, BSCCO, LSCO, Hg- and Tl-based"),
        ("Iron-based", "pnictides and chalcogenides; FeSe, BaFe$_2$As$_2$"),
        ("Nickelates", "infinite-layer and Ruddlesden-Popper; La$_3$Ni$_2$O$_7$"),
        ("Other unconventional", "heavy fermion, Sr$_2$RuO$_4$, organics, UTe$_2$"),
        ("2D / interface / moire", "twisted graphene, kagome, TMDs, oxide interfaces"),
        ("Topological", "Majorana platforms, proximitised hybrids"),
        ("Devices", "qubits, detectors, magnets, cables, circuits"),
        ("Material-agnostic theory & method", "formalism, general pairing and vortex theory, instrumentation"),
    ]
    TASK_DESC = [
        ("Theory", "models, formalism, many-body numerics"),
        ("Ab initio", "DFT, electron-phonon, Eliashberg on real compounds"),
        ("Discovery", "new superconductors; screening and inverse design"),
        ("Synthesis", "growth, films, topotactic routes, fabrication"),
        ("Characterization", "ARPES, STM, neutron, transport, device metrology"),
    ]
    AI_DESC = [("Surrogate / regression", "#4C72B0"), ("GNN & ML potentials", "#55A868"),
               ("Generative models", "#C44E52"), ("LLM / agents", "#8172B3"),
               ("Neural quantum states", "#DD8452"), ("Autonomous experiment", "#937860")]
    H, GAP, BANDGAP = 0.66, 0.16, 0.62
    fig, ax = plt.subplots(figsize=(7.8, 7.0))
    cur = [0.0]                                   # running cursor, top-down in negative y

    def band(title, subtitle, items, color, cols, chip_h=H, show_desc=True):
        ax.text(0.1, cur[0], title, fontsize=10, fontweight="bold", va="top")
        cur[0] -= 0.30
        ax.text(0.1, cur[0], subtitle, fontsize=8, color="#555555", va="top", style="italic")
        cur[0] -= 0.34
        w = (9.8 - 0.2 * (cols - 1)) / cols
        rows = (len(items) + cols - 1) // cols
        for i, item in enumerate(items):
            name, desc = item if isinstance(item, tuple) else (item, "")
            x = 0.1 + (i % cols) * (w + 0.2)
            top = cur[0] - (i // cols) * (chip_h + GAP)
            ax.add_patch(Rectangle((x, top - chip_h), w, chip_h, facecolor=color, alpha=0.13,
                                   edgecolor=color, lw=1.0))
            if show_desc and desc:
                ax.text(x + 0.16, top - chip_h * 0.34, name, fontsize=8.6, fontweight="bold", va="center")
                ax.text(x + 0.16, top - chip_h * 0.72, desc, fontsize=7.0, color="#444444", va="center")
            else:
                ax.text(x + 0.16, top - chip_h / 2, name, fontsize=8.4, va="center")
        cur[0] -= rows * (chip_h + GAP) - GAP + BANDGAP

    band("Axis 1  ·  Material family", "one label per paper", FAM_DESC, "#4C72B0", 2)
    band("Axis 2  ·  Mode of inquiry",
         "one label per paper; application context is carried by the Devices family",
         TASK_DESC, "#55A868", 2)
    band("AI lens  ·  method used",
         "assigned only to papers that use an AI/ML method in their own work",
         [n for n, _ in AI_DESC], "#8172B3", 3, chip_h=0.52, show_desc=False)
    ax.set_xlim(0, 10); ax.set_ylim(cur[0] + 0.3, 0.55); ax.axis("off")
    fig.tight_layout(); fig.savefig(FIG / "fig1_taxonomy.png", bbox_inches="tight"); plt.close(fig)
    print("wrote fig1_taxonomy.png")

def fig4_readiness():
    cells = list(READINESS.items())
    M = np.array([[v[0], v[1], v[2]] for _, v in cells], dtype=float)
    labels = [f"{FLABEL[f].replace(chr(10), ' ')} × {TLABEL[t]}" for (f, t), _ in cells]
    order = np.argsort(-M.sum(axis=1))
    M, labels = M[order], [labels[i] for i in order]
    bots = [cells[i][1][3] for i in order]
    fig, ax = plt.subplots(figsize=(7.4, 5.6))
    im = ax.imshow(M, cmap="YlGnBu", vmin=0, vmax=3, aspect="auto")
    ax.set_xticks(range(3))
    ax.set_xticklabels(["Data\navailability", "Benchmark\nmaturity", "Cheap\nvalidation"], fontsize=8.5)
    ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels, fontsize=8)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, int(M[i, j]), ha="center", va="center", fontsize=8.5,
                    color="white" if M[i, j] >= 2.5 else "black")
        ax.text(3.05, i, bots[i], ha="left", va="center", fontsize=8, color=BCOLOR[bots[i]], fontweight="bold")
    ax.set_xlim(-0.5, 4.6); ax.set_ylim(len(labels) - 0.5, -1.3)
    ax.text(3.05, -0.95, "binding\nbottleneck", ha="left", va="center", fontsize=8, fontweight="bold")
    ax.set_title("AI readiness by taxonomy cell\n(0 = absent, 3 = mature; author judgement, not measurement)",
                 fontsize=9, loc="left", pad=16)
    fig.colorbar(im, ax=ax, shrink=0.6, ticks=[0, 1, 2, 3], pad=0.16)
    fig.tight_layout(); fig.savefig(FIG / "fig4_ai_readiness.png", bbox_inches="tight"); plt.close(fig)
    print("wrote fig4_ai_readiness.png")

if __name__ == "__main__":
    fig1_taxonomy(); fig4_readiness()
