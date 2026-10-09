"""
Compare the 64 initial-batch configs (7 anchors + 57 LHS random-allocation
draws) of a Design-B slice run against the winner-shape anchor and the
uniform baseline — answers "how many random tries come close to (or beat)
the winner shape / uniform?"

Produces <category>/<method>/top_configs/plots/random_vs_winner_uniform.png:
a per-config bar of fitness score (config 1..64, in run order), colored by
role (uniform / winner shape / other heuristic anchor / random LHS), with
horizontal reference lines at the uniform and winner scores.

Usage (from NAS_Assets/):
  python3 plot_random_vs_winner_uniform.py RULER_ALL_B1024 --method snapkv
"""

import argparse
import os
import re

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ANCHOR_LABELS = [
    "uniform", "ramp asc", "ramp desc", "triangle mid",
    "triangle edge", "alternating", "winner shape",
]
N_INIT = 64  # 7 anchors + 57 LHS randoms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("category", help="e.g. RULER_ALL_B1024")
    ap.add_argument("--method", default="snapkv")
    ap.add_argument("--output_file", default=None)
    args = ap.parse_args()

    out_txt = args.output_file or os.path.join(args.category, args.method, "output.txt")
    plots_dir = os.path.join(args.category, args.method, "top_configs", "plots")
    os.makedirs(plots_dir, exist_ok=True)

    rows = [l.split() for l in open(out_txt) if len(l.split()) >= 34]
    d = np.array(rows, dtype=float)
    scores = -d[:, -1]
    n_init = min(N_INIT, len(d))
    init_scores = scores[:n_init]

    idx_uniform = 0
    idx_winner = 6 if n_init > 6 else None  # anchor row 7 = winner shape (1-indexed)

    colors = []
    for i in range(n_init):
        if i == idx_uniform:
            colors.append("tab:red")
        elif idx_winner is not None and i == idx_winner:
            colors.append("gold")
        elif i < 7:
            colors.append("tab:orange")
        else:
            colors.append("tab:blue")

    fig, ax = plt.subplots(figsize=(15, 6))
    ax.bar(range(1, n_init + 1), init_scores, color=colors, width=0.8)
    ax.axhline(init_scores[idx_uniform], color="tab:red", ls="--", lw=1.3,
               label=f"uniform ({init_scores[idx_uniform]:.2f})")
    if idx_winner is not None:
        ax.axhline(init_scores[idx_winner], color="goldenrod", ls="--", lw=1.3,
                   label=f"winner shape ({init_scores[idx_winner]:.2f})")

    # Value labels on the 7 named anchor bars (uniform + 6 heuristic shapes).
    for i in range(min(7, n_init)):
        ax.annotate(f"{init_scores[i]:.2f}", (i + 1, init_scores[i]),
                    textcoords="offset points", xytext=(0, 6),
                    ha="center", fontsize=8, fontweight="bold",
                    rotation=90 if i not in (0, 6) else 0)

    n_random = n_init - 7
    beat_winner = int(np.sum(init_scores[7:] > init_scores[idx_winner])) if idx_winner is not None and n_random > 0 else 0
    beat_uniform = int(np.sum(init_scores[7:] > init_scores[idx_uniform])) if n_random > 0 else 0

    from matplotlib.patches import Patch
    legend_handles = [
        Patch(facecolor="tab:red", label="uniform"),
        Patch(facecolor="gold", label="winner shape"),
        Patch(facecolor="tab:orange", label="other heuristic anchors"),
        Patch(facecolor="tab:blue", label=f"random LHS (n={n_random})"),
    ]
    ax.legend(handles=legend_handles, fontsize=9, loc="lower right")

    m = re.search(r"_B(\d+)$", args.category)
    target = m.group(1) if m else "?"
    ax.set_xlabel("config index (run order, 1-64)")
    ax.set_ylabel("RULER score (fitness subset)")
    ax.set_title(f"{args.category}/{args.method}: 64 initial configs vs winner shape & uniform "
                 f"(mean budget {target})\n"
                 f"random configs beating winner: {beat_winner}/{n_random} | "
                 f"beating uniform: {beat_uniform}/{n_random}")
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    out_path = os.path.join(plots_dir, "random_vs_winner_uniform.png")
    fig.savefig(out_path, dpi=200)
    plt.close(fig)

    print(f"Wrote {out_path}")
    print(f"uniform={init_scores[idx_uniform]:.2f}, winner={init_scores[idx_winner]:.2f}"
          if idx_winner is not None else f"uniform={init_scores[idx_uniform]:.2f}")
    print(f"random LHS (n={n_random}): min={init_scores[7:].min():.2f}, "
          f"max={init_scores[7:].max():.2f}, mean={init_scores[7:].mean():.2f}")
    print(f"random configs beating winner shape: {beat_winner}/{n_random}")
    print(f"random configs beating uniform: {beat_uniform}/{n_random}")


if __name__ == "__main__":
    main()
