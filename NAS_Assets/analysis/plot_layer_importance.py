"""
A4 — layer-importance heatmap.

Each row is one allocation; each column one of the 32 layers; colour is the
layer's budget relative to the row's own average (log2 scale, 0 = uniform
share). Top panel: the best full-data config per (category, budget, method)
among the 64-floor cells in analysis_outputs/cells.csv. Bottom panel: the
Step-2 winner anchors (unconstrained search, each at its natural budget).

Draft PNG for internal review; the camera-ready version should be redrawn in
pgfplots with the paper palette.
"""

import csv
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

HERE = os.path.dirname(os.path.abspath(__file__))
NAS = os.path.dirname(HERE)
OUT_DIR = os.path.join(os.path.dirname(NAS), "ICLR_Final_Results", "analysis_outputs")
LESS, MID, MORE = "#B83A32", "#f0efec", "#1F4E79"  # diverging: red <- neutral -> project dark blue
CMAP = LinearSegmentedColormap.from_list("div", [LESS, MID, MORE])
LIM = 3.0  # log2 ratio shown in [-3, 3] = 1/8x .. 8x the uniform share
ABBR = {"CODE": "Code", "MULTI_DOCUMENT_QA": "MultiDoc", "SINGLE_DOCUMENT_QA": "SingleDoc",
        "SUMMARIZATION": "Summ", "RULER_ALL": "RULER"}
ANCHORS = [(c, m, os.path.join(NAS, "anchors", f"anchor_longbench_{c}_{m}.txt"))
           for m in ("snapkv", "h2o")
           for c in ("CODE", "MULTI_DOCUMENT_QA", "SINGLE_DOCUMENT_QA", "SUMMARIZATION")]
ANCHORS += [("RULER_ALL", "snapkv", os.path.join(NAS, "anchor_1756_budgets.txt")),
            ("RULER_ALL", "h2o", os.path.join(NAS, "anchors", "anchor_h2o_2180.txt"))]


def rel_log2(budgets):
    b = np.asarray(budgets, dtype=float)
    return np.log2(b / b.mean())


def best_configs():
    rows = list(csv.DictReader(open(os.path.join(OUT_DIR, "cells.csv"))))
    cells = defaultdict(list)
    for r in rows:
        if r["source"] != "step3" and r["era"] == "64":
            cells[(r["method"], r["category"], int(r["budget"]))].append(r)
    out = []
    for (meth, cat, b), rs in sorted(cells.items()):
        best = max(rs, key=lambda r: float(r["full_score"]))
        out.append((f"{meth} · {ABBR[cat]} · B{b} ({best['label']})",
                    [int(x) for x in best["budgets"].split()]))
    return out


def anchors():
    return [(f"{m} · {ABBR[c]} (avg {np.loadtxt(p).mean():.0f})", np.loadtxt(p).astype(int).tolist())
            for c, m, p in ANCHORS if os.path.isfile(p)]


def panel(ax, items, title, norm):
    mat = np.array([rel_log2(b) for _, b in items])
    im = ax.imshow(np.clip(mat, -LIM, LIM), cmap=CMAP, norm=norm, aspect="auto",
                   interpolation="nearest")
    ax.set_yticks(range(len(items)))
    ax.set_yticklabels([lab for lab, _ in items], fontsize=7, color="#3b3b38")
    ax.set_xticks(range(0, 32, 4))
    ax.set_xticklabels([str(i) for i in range(0, 32, 4)], fontsize=7, color="#3b3b38")
    ax.set_xticks(np.arange(-0.5, 32, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(items), 1), minor=True)
    ax.grid(which="minor", color="#fcfcfb", linewidth=1.0)  # 1px surface gap between cells
    ax.tick_params(which="minor", length=0)
    ax.tick_params(which="major", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(title, fontsize=9, loc="left", color="#1a1a19")
    return im, mat


def main():
    top, bottom = best_configs(), anchors()
    norm = TwoSlopeNorm(vmin=-LIM, vcenter=0.0, vmax=LIM)
    fig, axes = plt.subplots(2, 1, figsize=(8.5, 0.19 * (len(top) + len(bottom)) + 2.2),
                             gridspec_kw={"height_ratios": [len(top), len(bottom)]},
                             facecolor="#fcfcfb")
    im, mat_top = panel(axes[0], top, "Best full-data config per cell (floor = 64)", norm)
    _, mat_bot = panel(axes[1], bottom, "Step-2 winner anchors (unconstrained search, natural budget)", norm)
    axes[1].set_xlabel("Layer index", fontsize=8, color="#3b3b38")
    cbar = fig.colorbar(im, ax=axes, fraction=0.025, pad=0.02,
                        ticks=[-3, -2, -1, 0, 1, 2, 3])
    cbar.ax.set_yticklabels(["⅛×", "¼×", "½×", "uniform", "2×", "4×", "8×"], fontsize=7)
    cbar.set_label("Layer budget ÷ row average", fontsize=8)
    cbar.outline.set_visible(False)
    png = os.path.join(OUT_DIR, "A4_layer_importance_heatmap.png")
    fig.savefig(png, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    paper_figs = os.path.join(os.path.dirname(NAS), "ARR_Oct_12_Submission", "acl-style-files-master", "figures")
    if os.path.isdir(paper_figs):
        fig.savefig(os.path.join(paper_figs, "A4_layer_importance_heatmap.png"), dpi=200,
                    bbox_inches="tight", facecolor=fig.get_facecolor())

    with open(os.path.join(OUT_DIR, "A4_layer_importance.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["panel", "row"] + [f"L{i}" for i in range(32)])
        for (lab, b) in top:
            w.writerow(["best_config", lab] + b)
        for (lab, b) in bottom:
            w.writerow(["anchor", lab] + b)

    allm = np.vstack([mat_top, mat_bot])
    mean = allm.mean(axis=0)
    above = (allm > 0).mean(axis=0)
    print(f"-> {png}")
    print("layer | mean log2(budget/avg) | share of rows above uniform")
    for i in range(32):
        print(f"L{i:<2d} | {mean[i]:+.2f} | {above[i]:.0%}")


if __name__ == "__main__":
    main()
