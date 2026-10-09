#!/usr/bin/env python3
"""AdaKV per-layer allocation heatmap in the same style/colour convention as figures/A4_layer_importance_heatmap.png
(blue = more than the row's uniform share, red = less). Reads ADAKV_RESULTS/data/*.csv; writes figures/adakv_allocation_shapes.png."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

HERE = Path(__file__).resolve().parent
ADA = HERE.parents[1] / "ICLR_Final_Results" / "ADAKV_RESULTS" / "data"
LESS, MID, MORE = "#B83A32", "#f0efec", "#1F4E79"  # identical to NAS_Assets/analysis/plot_layer_importance.py
CMAP = LinearSegmentedColormap.from_list("div", [LESS, MID, MORE])
LIM = 3.0
ABBR = {"CODE": "Code", "MULTI_DOCUMENT_QA": "MultiDoc", "SINGLE_DOCUMENT_QA": "SingleDoc", "RULER_ALL": "RULER"}
ARCH = {"Winner (rescaled anchor)": "Winner", "Best heuristic": "NAS-refined", "Best random": "NAS-refined", "Best BO": "NAS-refined"}  # three-way view
NATURAL = {"SINGLE_DOCUMENT_QA": 464, "MULTI_DOCUMENT_QA": 188, "CODE": 482, "RULER_ALL": 2536}  # anchors used downstream
ORDER = ["CODE", "MULTI_DOCUMENT_QA", "SINGLE_DOCUMENT_QA", "RULER_ALL"]


def vec(s):
    return [int(float(x)) for x in s.split()]


cells = {}      # (cat, budget) -> {arch: (score, budgets)}
anchors = {}    # cat -> budgets
for r in csv.DictReader(open(ADA / "longbench_slices_step3_4.csv")):
    cells.setdefault((r["category"], int(r["target_budget"])), {})[r["arch_name"]] = (float(r["mean_score"]), vec(r["budgets"]))
for r in csv.DictReader(open(ADA / "longbench_step2_pareto_full_eval.csv")):
    if r["type"] != "uniform" and abs(float(r["avg_budget"]) - NATURAL[r["category"]]) < 1:
        anchors[r["category"]] = vec(r["budgets"])
for r in csv.DictReader(open(ADA / "ruler_all_results.csv")):
    if r["stage"].startswith("step2"):
        if r["arch_name"] != "uniform" and abs(float(r["avg_budget"]) - NATURAL["RULER_ALL"]) < 1:
            anchors["RULER_ALL"] = vec(r["budgets"])
    elif r["stage"] == "step3_4_slice":
        cells.setdefault(("RULER_ALL", int(r["target_budget"])), {})[r["arch_name"]] = (float(r["mean_score"]), vec(r["budgets"]))

top = []
for cat, b in sorted(cells, key=lambda k: (ORDER.index(k[0]), k[1])):
    non = {a: v for a, v in cells[(cat, b)].items() if a != "Uniform"}
    best = max(non, key=lambda a: non[a][0])  # MOSAIC's final config = best non-uniform full-data candidate
    top.append((f"AdaKV · {ABBR[cat]} · B{b} ({ARCH[best]})", non[best][1]))
bottom = [(f"AdaKV · {ABBR[c]} (avg {np.mean(anchors[c]):.0f})", anchors[c]) for c in ORDER if c in anchors]
assert len(bottom) == 4, sorted(anchors)


def panel(ax, items, title, norm):
    mat = np.array([np.log2(np.asarray(b, float) / np.mean(b)) for _, b in items])
    im = ax.imshow(np.clip(mat, -LIM, LIM), cmap=CMAP, norm=norm, aspect="auto", interpolation="nearest")
    ax.set_yticks(range(len(items)))
    ax.set_yticklabels([lab for lab, _ in items], fontsize=7, color="#3b3b38")
    ax.set_xticks(range(0, 32, 4))
    ax.set_xticklabels([str(i) for i in range(0, 32, 4)], fontsize=7, color="#3b3b38")
    ax.set_xticks(np.arange(-0.5, 32, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(items), 1), minor=True)
    ax.grid(which="minor", color="#fcfcfb", linewidth=1.0)
    ax.tick_params(which="both", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(title, fontsize=9, loc="left", color="#1a1a19")
    return im


norm = TwoSlopeNorm(vmin=-LIM, vcenter=0.0, vmax=LIM)
fig, axes = plt.subplots(2, 1, figsize=(8.5, 0.19 * (len(top) + len(bottom)) + 2.2),
                         gridspec_kw={"height_ratios": [len(top), len(bottom)]}, facecolor="#fcfcfb")
im = panel(axes[0], top, "Best full-data config per cell (AdaKV)", norm)
panel(axes[1], bottom, "Stage 2 winner anchors (unconstrained search, natural budget)", norm)
axes[1].set_xlabel("Layer index", fontsize=8, color="#3b3b38")
cbar = fig.colorbar(im, ax=axes, fraction=0.025, pad=0.02, ticks=[-3, -2, -1, 0, 1, 2, 3])
cbar.ax.set_yticklabels(["⅛×", "¼×", "½×", "uniform", "2×", "4×", "8×"], fontsize=7)
cbar.set_label("Layer budget ÷ row average", fontsize=8)
cbar.outline.set_visible(False)
out = HERE / "figures" / "adakv_allocation_shapes.png"
fig.savefig(out, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"wrote {out}: {len(top)} cells + {len(bottom)} anchors")
