"""
Step 3 of the RULER methodology: rescale a winner-shape anchor (from
extract_winner_anchor.py) to fixed target budgets and evaluate on the full
test set — the cheap "transform to budget-constrained value for an
apples-to-apples comparison" step, without running a new NAS search.

For each target budget T, builds two snapshot rows in the same X-space
eval_top_configs_ruler.py already understands (32 weights in [0,1] + 2 dummy
trailing columns, decoded via run_ruler_lamp._decode_budgets under
NAS_TARGET_BUDGET=T):
  - uniform:      x = [0.5]*32                        -> uniform allocation at T
  - winner shape: x = 0.05 + 0.9*(anchor / anchor.max())  -> same formula LAMP.py
                  uses to seed a slice search anchor (LAMP.py's shape_configs)

Writes the snapshot to <base_category>_B<T>/<method>/top_configs/
fixed_budget_snapshot.txt and shells out to eval_top_configs_ruler.py
(one subprocess per target, so each gets a correctly-scoped NAS_TARGET_BUDGET
env and a fresh model load — matches how eval_bo_configs_gpu2.sh drove the
same script for the B1536/B2048 slices).

Relies on the existing "_B<digits> suffix stripped for clustering lookup"
support in run_ruler_lamp.py — <base_category>_B<T> resolves to the same
subtask list as <base_category>, no new ruler_clustering.json entries needed.

Usage (from nas/, PYTHONPATH must include the repo root):
  python3 eval_fixed_budgets_from_anchor.py anchors/anchor_h2o_1234.txt \\
      --method h2o --targets 64,128,256,512

  # Sanity-check the decoded budgets (no GPU / no eval) before spending compute:
  python3 eval_fixed_budgets_from_anchor.py anchors/anchor_h2o_1234.txt \\
      --method h2o --targets 64,128,256,512 --dry_run

  # Pure uniform-budget baseline sweep — no anchor/winner shape needed at all
  # (e.g. for a brand-new method with no Step-1 winner yet):
  python3 eval_fixed_budgets_from_anchor.py --uniform_only --method l2norm \\
      --benchmark ruler --targets 64,128,256,512,1024,2048,4096
"""

import argparse
import os
import subprocess
import sys

import numpy as np


def build_snapshot_rows(anchor_budgets, target, num_layers):
    """Return (uniform_x, winner_x), each a 32-vector in [0,1]."""
    uniform_x = np.full(num_layers, 0.5)
    b = np.asarray(anchor_budgets, dtype=float)
    winner_x = 0.05 + 0.9 * (b / b.max())
    return uniform_x, winner_x


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("anchor_file", help="Winner-shape anchor (32 budgets), e.g. from extract_winner_anchor.py")
    parser.add_argument("--method", default="snapkv")
    parser.add_argument("--benchmark", default="ruler", choices=["ruler", "longbench"],
                        help="Which benchmark's decoder/eval script to use (default: ruler, "
                             "unchanged from prior behavior)")
    parser.add_argument("--targets", default="64,128,256,512",
                        help="Comma-separated target mean budgets to evaluate")
    parser.add_argument("--base_category", default=None,
                        help="Base group name in ruler_clustering.json / data_clustering.json "
                             "(output dirs are <base_category>_B<T>/<method>/). "
                             "Defaults to RULER_ALL for --benchmark ruler; required for --benchmark longbench "
                             "(e.g. SINGLE_DOCUMENT_QA, MULTI_DOCUMENT_QA, CODE)")
    parser.add_argument("--sample_ratio", type=float, default=1.0)
    parser.add_argument("--min_budget", type=int, default=64)
    parser.add_argument("--max_budget", type=int, default=4096)
    parser.add_argument("--gpu", default=None, help="CUDA_VISIBLE_DEVICES for the eval subprocess "
                                                     "(default: inherit current environment)")
    parser.add_argument("--python_bin", default=os.environ.get(
        "PYTHON_BIN", sys.executable))
    parser.add_argument("--dry_run", action="store_true",
                        help="Only print decoded budgets and sanity-check sums; no eval subprocess")
    parser.add_argument("--winner_only", action="store_true",
                        help="Skip the uniform row — use when a validated uniform score for this "
                             "method/target already exists elsewhere (e.g. a standalone budget "
                             "sweep, or a slice search's own row-1 anchor). Halves the eval cost.")
    args = parser.parse_args()

    if args.benchmark == "ruler":
        from run_ruler_lamp import x_point_to_budgets_continuous
        eval_script = "eval_top_configs_ruler.py"
        base_category = args.base_category or "RULER_ALL"
    else:
        from run_longbench_lamp import x_point_to_budgets_continuous
        eval_script = "eval_top_configs_longbench.py"
        if args.base_category is None:
            raise SystemExit("--base_category is required for --benchmark longbench "
                             "(e.g. SINGLE_DOCUMENT_QA, MULTI_DOCUMENT_QA, CODE)")
        base_category = args.base_category
    args.base_category = base_category

    anchor_budgets = np.loadtxt(args.anchor_file).reshape(-1)
    num_layers = len(anchor_budgets)
    targets = [int(t) for t in args.targets.split(",") if t]

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_dir = os.path.dirname(os.path.abspath(__file__))

    for T in targets:
        uniform_x, winner_x = build_snapshot_rows(anchor_budgets, T, num_layers)

        uniform_b = x_point_to_budgets_continuous(uniform_x, num_layers, T, args.min_budget, args.max_budget)
        winner_b = x_point_to_budgets_continuous(winner_x, num_layers, T, args.min_budget, args.max_budget)
        expected_sum = num_layers * T
        checks = (("winner", winner_b),) if args.winner_only else (("uniform", uniform_b), ("winner", winner_b))
        for label, b in checks:
            actual_sum = sum(b)
            status = "OK" if actual_sum == expected_sum else "MISMATCH"
            print(f"[B{T}] {label}: sum={actual_sum} (expected {expected_sum}) [{status}] budgets={b}")
            if actual_sum != expected_sum:
                raise SystemExit(f"Budget sum mismatch for target {T} ({label}) — "
                                  f"target likely unreachable given min/max clamps.")

        if args.dry_run:
            continue

        category = f"{args.base_category}_B{T}"
        top_configs_dir = os.path.join(category, args.method, "top_configs")
        os.makedirs(top_configs_dir, exist_ok=True)
        snapshot_path = os.path.join(top_configs_dir, "fixed_budget_snapshot.txt")

        row_list = [np.concatenate([winner_x, [0.0, 0.0]])] if args.winner_only else [
            np.concatenate([uniform_x, [0.0, 0.0]]),
            np.concatenate([winner_x, [0.0, 0.0]]),
        ]
        rows = np.vstack(row_list)
        np.savetxt(snapshot_path, rows)

        results_csv = os.path.join(top_configs_dir, "eval_results.csv")
        if os.path.isfile(results_csv):
            print(f"WARNING: {results_csv} already exists and will be overwritten by this run.")

        env = dict(os.environ)
        env["PYTHONNOUSERSITE"] = "1"
        env["PYTHONPATH"] = f"{repo_root}:{env.get('PYTHONPATH', '')}"
        env["NAS_TARGET_BUDGET"] = str(T)
        if args.gpu is not None:
            env["CUDA_VISIBLE_DEVICES"] = args.gpu

        cmd = [args.python_bin, eval_script, category,
               "--method", args.method, "--all_rows",
               "--sample_ratio", str(args.sample_ratio),
               "--output_file", snapshot_path,
               "--save_predictions"]
        print(f"[B{T}] running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=script_dir, env=env)
        if result.returncode != 0:
            raise SystemExit(f"{eval_script} failed for target {T} "
                              f"(exit code {result.returncode})")
        print(f"[B{T}] done -> {results_csv}")


if __name__ == "__main__":
    main()
