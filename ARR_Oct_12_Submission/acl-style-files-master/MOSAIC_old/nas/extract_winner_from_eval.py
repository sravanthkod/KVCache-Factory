"""
Extract the winner (best full-data mean_score, non-uniform-shape) anchor from
an ALREADY FULL-DATA-EVALUATED eval_results.csv (written by
eval_top_configs_ruler.py / eval_top_configs_longbench.py).

This is the correct-order sibling of extract_winner_anchor.py: that script
picks the winner using the noisy NAS_SAMPLE_RATIO search-time fitness
straight out of output.txt, BEFORE any full-data eval has run. This script
instead picks using the real full-500 (or full-data) mean_score column of
eval_results.csv, AFTER the Pareto front has already been evaluated on full
data -- "first evaluate the top configs, then pick the winner from that",
(the ordering used for Stage 2).

Standalone, single-file, zero repo-specific imports (only csv + numpy from
the standard toolchain) -- safe to copy to any server.

Usage:
    python3 extract_winner_from_eval.py <eval_results.csv> [--out ANCHOR_PATH]

Excludes rows whose 'budgets' column is uniform (all 32 layers the same
value) -- these are always Pareto-optimal on the score axis but carry no
per-layer allocation information (same exclusion rule as
extract_winner_anchor.py). Among the remaining (shaped) rows, picks the one
with the highest mean_score and writes its per-layer budgets as a
whitespace-separated anchor file.
"""

import argparse
import csv
import os

import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("eval_results_csv", help="Path to a full-data eval_results.csv")
    parser.add_argument("--out", default=None,
                         help="Anchor file to write (default: "
                              "anchors/anchor_<basename>_<avgbudget>.txt next "
                              "to the eval_results.csv's containing repo root "
                              "-- falls back to the current directory's "
                              "anchors/ if that can't be inferred)")
    args = parser.parse_args()

    rows = []
    with open(args.eval_results_csv, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            budgets = [int(x) for x in row["budgets"].split()]
            is_uniform = len(set(budgets)) == 1
            rows.append({
                "arch": row["arch"],
                "avg_budget": float(row["avg_budget"]),
                "mean_score": float(row["mean_score"]),
                "budgets": budgets,
                "is_uniform": is_uniform,
            })

    if not rows:
        raise SystemExit(f"Error: no rows found in {args.eval_results_csv}")

    shaped = [r for r in rows if not r["is_uniform"]]
    if not shaped:
        raise SystemExit(
            f"No non-uniform (shaped) config found in {args.eval_results_csv} -- "
            f"only trivial uniform-budget rows are present.")

    winner = max(shaped, key=lambda r: r["mean_score"])
    avg_budget = float(np.mean(winner["budgets"]))

    out_path = args.out
    if out_path is None:
        base = os.path.splitext(os.path.basename(args.eval_results_csv))[0]
        out_dir = "anchors"
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"anchor_{base}_{avg_budget:.0f}.txt")
    else:
        out_dir = os.path.dirname(out_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

    np.savetxt(out_path, [winner["budgets"]], fmt="%d")

    print(f"{len(rows)} total rows ({len(rows) - len(shaped)} uniform, {len(shaped)} shaped)")
    print(f"Winner: arch {winner['arch']}, mean_score {winner['mean_score']:.2f}, "
          f"avg_budget {avg_budget:.1f}")
    print(f"Budgets: {winner['budgets']}")
    print(f"Anchor written to {out_path}")


if __name__ == "__main__":
    main()
