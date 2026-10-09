"""
Plots for fixed-budget-slice NAS runs (Design B), where f1 is constant and the
generic Pareto plot degenerates to a single point.

Produces, under <category>/<method>/top_configs/plots/:
  1. convergence.png        — best-so-far score vs evaluation, phases marked
  2. score_distribution.png — histogram of all scores; anchors/controls marked
  3. config_profiles.png    — per-layer budget profiles of the notable configs
  4. top_configs_heatmap.png— per-layer budgets of the top-K configs (+uniform)

Usage (from NAS_Assets/):
  python3 plot_slice_results.py RULER_ALL_B1536 --method snapkv
  python3 plot_slice_results.py RULER_ALL_B1024 --method snapkv --top_k 10
"""

import argparse
import os
import re

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from run_ruler_lamp import x_point_to_budgets_continuous

ANCHOR_LABELS = [
    "uniform", "ramp asc", "ramp desc", "triangle mid",
    "triangle edge", "alternating", "winner shape",
]
N_INIT = 64  # anchors (7) + LHS randoms (57)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("category", help="e.g. RULER_ALL_B1536 (target parsed from _B suffix)")
    ap.add_argument("--method", default="snapkv")
    ap.add_argument("--target", type=int, default=None,
                    help="target mean budget (default: parsed from category suffix)")
    ap.add_argument("--top_k", type=int, default=12)
    args = ap.parse_args()

    target = args.target
    if target is None:
        m = re.search(r"_B(\d+)$", args.category)
        if not m:
            raise SystemExit("Category has no _B<target> suffix; pass --target")
        target = int(m.group(1))

    out_txt = os.path.join(args.category, args.method, "output.txt")
    plots_dir = os.path.join(args.category, args.method, "top_configs", "plots")
    os.makedirs(plots_dir, exist_ok=True)

    rows = [l.split() for l in open(out_txt) if len(l.split()) >= 34]
    d = np.array(rows, dtype=float)
    X, scores = d[:, :-2], -d[:, -1]
    n = len(d)
    budgets = np.array([x_point_to_budgets_continuous(x, 32, target) for x in X])

    idx_uniform = 0
    idx_best_heur = 1 + int(np.argmax(scores[1:7])) if n > 7 else None
    idx_best_rand = 7 + int(np.argmax(scores[7:N_INIT])) if n > 7 else None
    idx_best_bo = (N_INIT + int(np.argmax(scores[N_INIT:]))) if n > N_INIT else None
    idx_best = int(np.argmax(scores))

    # ── 1. Convergence ────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 5))
    best_so_far = np.maximum.accumulate(scores)
    ax.plot(range(1, n + 1), scores, ".", color="lightgray", label="candidate score")
    ax.plot(range(1, n + 1), best_so_far, "-", color="tab:blue", lw=2, label="best so far")
    ax.axhline(scores[idx_uniform], color="tab:red", ls="--", lw=1,
               label=f"uniform @ {target} ({scores[idx_uniform]:.2f})")
    ax.axvspan(0.5, 7.5, color="tab:orange", alpha=0.10)
    ax.axvspan(7.5, min(N_INIT, n) + 0.5, color="tab:green", alpha=0.08)
    if n > N_INIT:
        ax.axvspan(N_INIT + 0.5, n + 0.5, color="tab:purple", alpha=0.08)
    for x_txt, lbl in [(4, "anchors"), (min(35, n), "random LHS"),
                       (N_INIT + max(1, (n - N_INIT) // 2), "guided (BO)")]:
        if x_txt <= n:
            ax.text(x_txt, ax.get_ylim()[0] + 0.5, lbl, fontsize=8, ha="center", color="gray")
    ax.set_xlabel("evaluation"); ax.set_ylabel("RULER score (fitness subset)")
    ax.set_title(f"{args.category}/{args.method}: search convergence @ mean budget {target}")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(plots_dir, "convergence.png"), dpi=200)
    plt.close(fig)

    # ── 2. Score distribution with controls ──────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(scores[7:N_INIT], bins=20, color="tab:green", alpha=0.5,
            label=f"random LHS (n={len(scores[7:N_INIT])})")
    if n > N_INIT:
        ax.hist(scores[N_INIT:], bins=20, color="tab:purple", alpha=0.5,
                label=f"guided BO (n={n - N_INIT})")
    marks = [(idx_uniform, "uniform", "tab:red")]
    if idx_best_heur is not None:
        marks.append((idx_best_heur, f"best heuristic ({ANCHOR_LABELS[idx_best_heur]})", "tab:orange"))
    if idx_best_rand is not None:
        marks.append((idx_best_rand, "best random", "tab:green"))
    if idx_best_bo is not None:
        marks.append((idx_best_bo, "best BO", "tab:purple"))
    for i, lbl, c in marks:
        ax.axvline(scores[i], color=c, lw=2, label=f"{lbl}: {scores[i]:.2f}")
    ax.set_xlabel("RULER score (fitness subset)"); ax.set_ylabel("count")
    ax.set_title(f"{args.category}: score distribution @ mean budget {target}")
    ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(plots_dir, "score_distribution.png"), dpi=200)
    plt.close(fig)

    # ── 3. Config profiles (notable configs) ─────────────────────────────────
    fig, ax = plt.subplots(figsize=(11, 5))
    notable = [(idx_uniform, f"uniform ({scores[idx_uniform]:.2f})", "tab:red", "--")]
    if idx_best_heur is not None:
        notable.append((idx_best_heur,
                        f"{ANCHOR_LABELS[idx_best_heur]} ({scores[idx_best_heur]:.2f})",
                        "tab:orange", "-"))
    if idx_best_rand is not None:
        notable.append((idx_best_rand, f"best random ({scores[idx_best_rand]:.2f})", "tab:green", "-"))
    if idx_best_bo is not None:
        notable.append((idx_best_bo, f"best BO ({scores[idx_best_bo]:.2f})", "tab:purple", "-"))
    if idx_best not in [i for i, *_ in notable]:
        notable.append((idx_best, f"best overall ({scores[idx_best]:.2f})", "black", "-"))
    for i, lbl, c, ls in notable:
        ax.step(range(32), budgets[i], where="mid", label=lbl, color=c, ls=ls, lw=1.8, alpha=0.85)
    ax.set_yscale("log", base=2)
    ax.set_yticks([16, 64, 256, 1024, 4096]); ax.set_yticklabels([16, 64, 256, 1024, 4096])
    ax.set_xlabel("layer"); ax.set_ylabel("per-layer budget (log scale)")
    ax.set_title(f"{args.category}: notable allocation profiles (mean budget {target})")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(plots_dir, "config_profiles.png"), dpi=200)
    plt.close(fig)

    # ── 4. Top-K heatmap ──────────────────────────────────────────────────────
    order = np.argsort(-scores)[:args.top_k]
    if idx_uniform not in order:
        order = np.concatenate([order, [idx_uniform]])
    fig, ax = plt.subplots(figsize=(13, 0.45 * len(order) + 2))
    mat = np.log2(budgets[order])
    im = ax.imshow(mat, aspect="auto", cmap="RdYlGn_r")
    for r, i in enumerate(order):
        for c in range(32):
            ax.text(c, r, str(budgets[i][c]), ha="center", va="center", fontsize=4.5)
    phase = lambda i: ("anchor:" + ANCHOR_LABELS[i]) if i < 7 else ("random" if i < N_INIT else "BO")
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([f"#{i+1} {phase(i)} ({scores[i]:.2f})" for i in order], fontsize=7)
    ax.set_xticks(range(0, 32, 2)); ax.set_xticklabels(range(0, 32, 2), fontsize=7)
    ax.set_xlabel("layer")
    ax.set_title(f"{args.category}: top-{args.top_k} allocations by score (+uniform ref), "
                 f"cell = per-layer budget, mean fixed at {target}")
    fig.colorbar(im, ax=ax, label="log2(budget)", shrink=0.8)
    fig.tight_layout(); fig.savefig(os.path.join(plots_dir, "top_configs_heatmap.png"), dpi=200)
    plt.close(fig)

    print(f"Wrote 4 plots to {plots_dir}/")
    print(f"  uniform={scores[idx_uniform]:.2f}"
          + (f", best_heuristic={scores[idx_best_heur]:.2f} ({ANCHOR_LABELS[idx_best_heur]})" if idx_best_heur is not None else "")
          + (f", best_random={scores[idx_best_rand]:.2f}" if idx_best_rand is not None else "")
          + (f", best_BO={scores[idx_best_bo]:.2f}" if idx_best_bo is not None else "")
          + f", best_overall={scores[idx_best]:.2f}")


if __name__ == "__main__":
    main()
