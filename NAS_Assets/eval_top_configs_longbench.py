"""
Evaluate the Pareto-front (rank-1) configs from a LongBench NAS run on full data.

Reads <TASK_CATEGORY>/<method>/output.txt (written by LAMP.py via HFF_mod.py),
extracts the non-dominated configs with ndsort.rank_one (same logic as
eval_top_configs_ruler.py's load_pareto_archs), then re-evaluates each config
on the category's datasets using the exact generation and scoring path of
run_longbench_lamp.py (run_dataset_calibration_with_scoring).

This is the LongBench analog of eval_top_configs_ruler.py — same CLI shape,
same output schema — so eval_fixed_budgets_from_anchor.py's --benchmark
longbench mode can drive it identically. It does NOT replace the older,
structurally different eval_top_configs.py (multiprocessing-based, no
--all_rows/--output_file support); this is a new, lean, purpose-built sibling.

Outputs under <TASK_CATEGORY>/<method>/top_configs/:
  - eval_results.csv                    : arch x dataset scores + avg budget
  - predictions/arch_<k>/<dataset>.jsonl : per-config predictions (if --save_predictions)

Usage (from NAS_Assets/, PYTHONPATH must include the repo root):
  python3 eval_top_configs_longbench.py SINGLE_DOCUMENT_QA --method snapkv
  python3 eval_top_configs_longbench.py SINGLE_DOCUMENT_QA --method snapkv --sample_ratio 1.0
"""

import argparse
import csv
import os
import re

import numpy as np

from ndsort import rank_one
import run_longbench_lamp as rll
from run_longbench_lamp import _ensure_model_loaded, _decode_budgets


def load_pareto_archs(output_file):
    """Return the rank-1 rows of output.txt (each row = D x-values + f1 + f2)."""
    rows = np.loadtxt(output_file)
    if rows.ndim == 1:
        rows = rows.reshape(1, -1)

    # Deduplicate objective pairs, remembering the first row for each pair.
    unique_objs = []
    pair_to_row = {}
    for row_idx, row in enumerate(rows):
        pair = (float(row[-2]), float(row[-1]))
        if pair not in pair_to_row:
            pair_to_row[pair] = row_idx
            unique_objs.append(list(pair))

    rank1 = rank_one(np.array(unique_objs))[0]
    arch_rows = [rows[pair_to_row[tuple(p)]] for p in rank1]
    return arch_rows


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("task_category", help="LongBench group from data_clustering.json, e.g. SINGLE_DOCUMENT_QA")
    parser.add_argument("--method", default="snapkv")
    parser.add_argument("--sample_ratio", type=float, default=1.0,
                        help="Fraction of each dataset to evaluate (default 1.0 = all samples)")
    parser.add_argument("--seed", type=int, default=rll.NAS_SEED)
    parser.add_argument("--save_predictions", action="store_true",
                        help="Also write per-config prediction jsonl files")
    parser.add_argument("--shard", default=None, metavar="K/N",
                        help="Evaluate only every N-th Pareto config starting at K "
                             "(e.g. 0/3, 1/3, 2/3 for a 3-GPU split)")
    parser.add_argument("--dry_run", action="store_true",
                        help="Print selected archs and budgets, then exit (no GPU)")
    parser.add_argument("--output_file", default=None,
                        help="Read NAS results from this file instead of "
                             "<category>/<method>/output.txt. Parallel shards MUST "
                             "all point at the same frozen snapshot so they compute "
                             "an identical Pareto front / arch numbering.")
    parser.add_argument("--all_rows", action="store_true",
                        help="Evaluate every row of the output file in order instead "
                             "of the Pareto rank-1 subset (use for slice-mode runs, "
                             "where f1 is constant and Pareto selection collapses to "
                             "a single row — this keeps control configs too)")
    args = parser.parse_args()

    output_file = args.output_file or os.path.join(args.task_category, args.method, "output.txt")
    if not os.path.isfile(output_file):
        raise SystemExit(f"Error: {output_file} not found — run the NAS first (run_nas.sh)")

    clustering = rll.load_data_clustering()
    # Slice-run categories carry a _B<target> suffix; datasets come from the base key.
    lookup_key = args.task_category if args.task_category in clustering \
        else re.sub(r"_B\d+$", "", args.task_category)
    if lookup_key not in clustering:
        raise SystemExit(f"'{args.task_category}' (lookup '{lookup_key}') not in "
                         f"data_clustering.json. Available: "
                         f"{[k for k in clustering if k not in ('DATASET2METRIC', 'TOTAL_DATASETS')]}")
    datasets = clustering[lookup_key]

    if args.all_rows:
        arch_rows = np.loadtxt(output_file)
        if arch_rows.ndim == 1:
            arch_rows = arch_rows.reshape(1, -1)
        arch_rows = list(arch_rows)
        print(f"Evaluating ALL {len(arch_rows)} rows of {output_file} (no Pareto selection)")
    else:
        arch_rows = load_pareto_archs(output_file)
        print(f"Found {len(arch_rows)} Pareto-front configs in {output_file}")

    # Shard selection: keep original arch numbering (1-based over the full front)
    selected = list(enumerate(arch_rows))
    shard_suffix = ""
    if args.shard:
        k, n = (int(x) for x in args.shard.split("/"))
        selected = selected[k::n]
        shard_suffix = f"_shard{k}"
        print(f"Shard {k}/{n}: evaluating archs {[i + 1 for i, _ in selected]}")

    print(f"Evaluating on {datasets}, sample_ratio={args.sample_ratio}")

    top_configs_dir = os.path.join(args.task_category, args.method, "top_configs")
    os.makedirs(top_configs_dir, exist_ok=True)

    if args.dry_run:
        for i, row in selected:
            budgets = _decode_budgets(np.array(row[:-2]), rll._get_num_layers())
            print(f"arch {i + 1}: avg_budget={np.mean(budgets):.1f} nas_f2={row[-1]:.4f}")
        return

    model, tokenizer = _ensure_model_loaded(rll.NAS_MODEL_PATH, args.method, rll.NAS_ATTN_IMPL)
    num_layers = len(model.model.layers)

    results = []
    for k, row in selected:
        X_point = np.array(row[:-2])
        nas_f1, nas_f2 = float(row[-2]), float(row[-1])
        budgets = _decode_budgets(X_point, num_layers)
        avg_budget = float(np.mean(budgets))
        print(f"\n=== Arch {k+1}/{len(arch_rows)}: avg_budget={avg_budget:.1f} "
              f"(NAS f1={nas_f1:.1f}, f2={nas_f2:.4f}) ===")
        print(f"    budgets: {budgets}")

        scores = {}
        for dataset in datasets:
            pred_path = None
            if args.save_predictions:
                pred_path = os.path.join(top_configs_dir, "predictions", f"arch_{k+1}",
                                         f"{dataset}.jsonl")
            _, score = rll.run_dataset_calibration_with_scoring(
                model=model,
                tokenizer=tokenizer,
                dataset=dataset,
                data_dir=rll.NAS_DATA_DIR,
                model_path=rll.NAS_MODEL_PATH,
                max_capacity_prompts=budgets,
                sample_ratio=args.sample_ratio,
                seed=args.seed,
                method=args.method,
                save_predictions_path=pred_path,
            )
            scores[dataset] = score

        mean_score = float(np.mean(list(scores.values())))
        print(f"    -> mean score: {mean_score:.2f}")
        results.append({
            "arch": k + 1,
            "avg_budget": avg_budget,
            "nas_f2": nas_f2,
            **scores,
            "mean_score": mean_score,
            "budgets": " ".join(str(b) for b in budgets),
        })

    csv_file = os.path.join(top_configs_dir, f"eval_results{shard_suffix}.csv")
    fieldnames = ["arch", "avg_budget", "nas_f2"] + datasets + ["mean_score", "budgets"]
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults written to {csv_file}")
    for r in results:
        print(f"  arch {r['arch']}: avg_budget={r['avg_budget']:.1f}, mean_score={r['mean_score']:.2f}")


if __name__ == "__main__":
    main()
