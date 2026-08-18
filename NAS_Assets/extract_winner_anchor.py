"""
Extract the winner (best-score, non-trivial-shape) anchor from an
unconstrained RULER NAS run.

Loads <task_category>/<method>/output.txt (rows = D x-values + f1 + f2,
written by LAMP.py in grid/unconstrained mode), restricts to the Pareto
front (same rank_one selection as eval_top_configs_ruler.py's
load_pareto_archs), drops the trivial UNIFORM anchors (all 32 layers at the
same budget — these are always Pareto-optimal on the score axis but carry no
per-layer allocation information), and picks the remaining row with the best
(lowest) f2. Decodes it into per-layer integer budgets via
run_ruler_lamp._decode_budgets and writes a whitespace-separated anchor file.

This reproduces, by construction, the manual selection that produced
anchor_1756_budgets.txt for SnapKV (arch 11 of the Pareto front: avg_budget
1756, full-500 score 98.38 — the best *shaped* allocation, edging out the
uniform-4096 config at 98.88 only because that one is trivial/uninformative).

That anchor file feeds NAS_ANCHOR_FILE for a budget-constrained ("Design B")
slice search (run_nas_ruler_slices.sh) or eval_fixed_budgets_from_anchor.py's
Step-3 rescale+eval.

Must be run against an UNCONSTRAINED output.txt (NAS_TARGET_BUDGET unset/0),
since the row is decoded with the grid decoder — this script warns if the
env disagrees.

Usage (from NAS_Assets/, PYTHONPATH must include the repo root):
  python3 extract_winner_anchor.py RULER_ALL --method h2o
  python3 extract_winner_anchor.py RULER_ALL --method h2o --out anchors/anchor_h2o.txt
"""

import argparse
import os

import numpy as np

import run_ruler_lamp as rrl
from run_ruler_lamp import _decode_budgets, _get_num_layers
from eval_top_configs_ruler import load_pareto_archs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_category", help="RULER group used for the unconstrained NAS run, e.g. RULER_ALL")
    parser.add_argument("--method", default="snapkv")
    parser.add_argument("--output_file", default=None,
                        help="Read NAS results from this file instead of "
                             "<task_category>/<method>/output.txt")
    parser.add_argument("--out", default=None,
                        help="Anchor file to write (default: anchors/anchor_<method>_<avgbudget>.txt)")
    args = parser.parse_args()

    if rrl.NAS_TARGET_BUDGET != 0:
        print(f"WARNING: NAS_TARGET_BUDGET={rrl.NAS_TARGET_BUDGET} is set in the "
              f"environment — this script expects an UNCONSTRAINED (grid-mode) "
              f"output.txt and decodes with the continuous decoder instead. "
              f"Unset NAS_TARGET_BUDGET before extracting a winner anchor.")

    output_file = args.output_file or os.path.join(args.task_category, args.method, "output.txt")
    if not os.path.isfile(output_file):
        raise SystemExit(f"Error: {output_file} not found — run the unconstrained NAS first (run_nas_ruler.sh)")

    pareto_rows = load_pareto_archs(output_file)
    num_layers = _get_num_layers()

    candidates = []
    for row in pareto_rows:
        budgets = _decode_budgets(row[:-2], num_layers)
        is_uniform = len(set(budgets)) == 1
        candidates.append((row, budgets, is_uniform))

    shaped = [(row, budgets) for row, budgets, is_uniform in candidates if not is_uniform]
    if not shaped:
        raise SystemExit(
            f"No non-uniform (shaped) config found on the Pareto front of {output_file} — "
            f"only trivial uniform-budget anchors are non-dominated. The search likely "
            f"hasn't run long enough to find a genuine per-layer allocation benefit yet.")

    best_row, budgets = min(shaped, key=lambda rb: rb[0][-1])
    avg_budget = float(np.mean(budgets))
    score = -float(best_row[-1])

    out_path = args.out or os.path.join("anchors", f"anchor_{args.method}_{avg_budget:.0f}.txt")
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    np.savetxt(out_path, [budgets], fmt="%d")

    print(f"Pareto front: {len(pareto_rows)} configs "
          f"({len(pareto_rows) - len(shaped)} uniform, {len(shaped)} shaped)")
    print(f"Winner (best shaped): fitness score {score:.2f}, avg_budget {avg_budget:.1f}")
    print(f"Budgets: {budgets}")
    print(f"Anchor written to {out_path}")


if __name__ == "__main__":
    main()
