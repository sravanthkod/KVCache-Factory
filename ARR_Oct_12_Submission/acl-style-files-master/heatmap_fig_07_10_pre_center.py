#!/usr/bin/env python3
"""Per-subtask / per-dataset gain heatmaps (MOSAIC - uniform) for the Appendix breakdown figures.
Plotting follows Fig 6 / Fig 6b of ICLR_Final_Results/ADAKV_RESULTS/generate_adakv_report.py (palette, diverging
colormap, TwoSlopeNorm around 0, cell annotations), extended to one panel per eviction method.
heatmap(name, panels, rows) writes figures/<name>.pdf.
panels: [(title, [(col_label, dagger)], {(row_label, col_label): gain})]; rows: [(row_label, group)] in display order."""
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

FIG = Path(__file__).resolve().parent / "figures"

# Palette and colormap as in generate_adakv_report.py
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3de"
DIVERGING = LinearSegmentedColormap.from_list(
    "bluegrayred", ["#104281", "#3987e5", "#f0efec", "#e66767", "#a8201f"])
DIVERGING.set_bad(GRID)

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "axes.titlecolor": INK, "axes.titleweight": "bold", "axes.titlesize": 7.5,
    "axes.titlelocation": "left", "font.size": 6.5, "axes.grid": False,
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
})


def heatmap(name, panels, rows, cell_w=0.27, cell_h=0.17):
    """One subplot per panel, shared colour scale (lim = largest |gain| shown, as in the report script)."""
    mats = []
    for _, cols, vals in panels:
        mats.append(np.array([[vals.get((r, c), np.nan) for c, _ in cols] for r, _ in rows], dtype=float))
    lim = max(1.0, max(np.nanmax(np.abs(m)) for m in mats))
    norm = TwoSlopeNorm(0, -lim, lim)
    widths = [len(cols) for _, cols, _ in panels]
    fig, axes = plt.subplots(1, len(panels), sharey=True, gridspec_kw={"width_ratios": widths, "wspace": 0.06},
                             figsize=(cell_w * sum(widths) + 1.6, cell_h * len(rows) + 0.9))
    axes = np.atleast_1d(axes)
    breaks = [i for i in range(1, len(rows)) if rows[i][1] != rows[i - 1][1]]
    for ax, (title, cols, _), mat in zip(axes, panels, mats):
        im = ax.imshow(mat, cmap=DIVERGING, norm=norm, aspect="auto")
        for i in range(mat.shape[0]):
            for j in range(mat.shape[1]):
                v = mat[i, j]
                if np.isnan(v):
                    ax.text(j, i, "–", ha="center", va="center", fontsize=4.8, color=INK2)
                    continue
                ax.text(j, i, f"{v:+.1f}", ha="center", va="center", fontsize=4.8,
                        color="#ffffff" if abs(v) > 0.6 * lim else INK)
        ax.set_xticks(range(len(cols)))
        ax.set_xticklabels([f"B{c}" + ("†" if d else "") for c, d in cols], fontsize=5.8)
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels([r for r, _ in rows], fontsize=5.8)
        ax.tick_params(length=0)
        for brk in breaks:
            ax.axhline(brk - 0.5, color=SURFACE, lw=2.5)
        ax.set_title(title)
    cb = fig.colorbar(im, ax=list(axes), fraction=0.025, pad=0.015)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=5.8, length=2)
    cb.set_label("MOSAIC $-$ uniform (points)", fontsize=6, color=INK2)
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)
    return lim
