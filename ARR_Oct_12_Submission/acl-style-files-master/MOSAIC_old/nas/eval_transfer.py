"""
Transfer evals (C1 cross-category, C2 cross-method): evaluate a Step-2 winner
anchor's shape on a different LongBench category and/or under a different
eviction method, on full data, at fixed target budgets.

The shape is rescaled exactly as Step 3 / the Step-4 winner seed do
(x = 0.05 + 0.9 * b / max(b), then x_point_to_budgets_continuous at the target
with floor 64 / ceiling 4096), so results are directly comparable with the
native `winner` rows in results/llama3/snapkv_h2o_cells.csv.

Writes only under transfer_evals/<tag>/B<T>/ — never touches any existing
<CATEGORY>_B<T>/<method>/top_configs/eval_results.csv. A (job, budget) whose
result.json already exists is skipped, so a killed run can simply be relaunched.

All jobs in one invocation share one eviction method (one model load).

Usage (from nas/, PYTHONPATH must include the repo root):
  python3 eval_transfer.py --method snapkv --budgets 128,512,1024 \
      --job anchors/anchor_longbench_CODE_snapkv.txt,SINGLE_DOCUMENT_QA,C1_CODEshape_on_SDQA_snapkv
  add --dry_run to print decoded budgets without loading the model.
"""

import argparse
import json
import os

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--method", required=True, help="eviction method to evaluate under (snapkv, h2o, ...)")
parser.add_argument("--budgets", default="128,512,1024")
parser.add_argument("--job", action="append", required=True, metavar="ANCHOR,TARGET_CATEGORY,TAG")
parser.add_argument("--min_budget", type=int, default=64)
parser.add_argument("--max_budget", type=int, default=4096)
parser.add_argument("--dry_run", action="store_true")
args = parser.parse_args()

os.environ["NAS_METHOD"] = args.method
os.environ.pop("NAS_TARGET_BUDGET", None)  # budgets are decoded explicitly below

import numpy as np  # noqa: E402

import run_longbench_lamp as rll  # noqa: E402
from run_longbench_lamp import x_point_to_budgets_continuous  # noqa: E402

rll.NAS_METHOD = args.method
NUM_LAYERS = 32
budgets_list = [int(b) for b in args.budgets.split(",")]
jobs = [tuple(j.split(",")) for j in args.job]
clustering = rll.load_data_clustering()


def decode(anchor_path, target):
    b = np.loadtxt(anchor_path)
    x = 0.05 + 0.9 * (b / b.max())
    return x_point_to_budgets_continuous(x, NUM_LAYERS, target, args.min_budget, args.max_budget)


for anchor, target_cat, tag in jobs:
    if target_cat not in clustering:
        raise SystemExit(f"unknown target category {target_cat}")
    for T in budgets_list:
        budgets = decode(anchor, T)
        assert abs(np.mean(budgets) - T) < 1e-6, (tag, T, np.mean(budgets))
        print(f"[plan] {tag} B{T}: avg={np.mean(budgets):.1f} budgets={budgets}")
if args.dry_run:
    raise SystemExit(0)

from run_longbench_lamp import _ensure_model_loaded  # noqa: E402

model, tokenizer = _ensure_model_loaded(rll.NAS_MODEL_PATH, args.method, rll.NAS_ATTN_IMPL)

for anchor, target_cat, tag in jobs:
    datasets = clustering[target_cat]
    for T in budgets_list:
        out_dir = os.path.join("transfer_evals", tag, f"B{T}")
        out_path = os.path.join(out_dir, "result.json")
        if os.path.isfile(out_path):
            print(f"[skip] {out_path} exists")
            continue
        os.makedirs(out_dir, exist_ok=True)
        budgets = decode(anchor, T)
        print(f"\n=== {tag} B{T} ({args.method} on {target_cat}) ===\n    budgets: {budgets}", flush=True)
        scores = {}
        for ds in datasets:
            _, score = rll.run_dataset_calibration_with_scoring(
                model=model, tokenizer=tokenizer, dataset=ds,
                data_dir=rll.NAS_DATA_DIR, model_path=rll.NAS_MODEL_PATH,
                max_capacity_prompts=budgets, sample_ratio=1.0, seed=rll.NAS_SEED,
                method=args.method,
                save_predictions_path=os.path.join(out_dir, "predictions", f"{ds}.jsonl"),
            )
            scores[ds] = score
        mean = float(np.mean(list(scores.values())))
        print(f"    -> full-data mean: {mean:.2f}", flush=True)
        with open(out_path, "w") as f:
            json.dump({"tag": tag, "anchor": anchor, "target_category": target_cat,
                       "method": args.method, "budget": T, "budgets": budgets,
                       "per_dataset_scores": scores, "full_data_mean_score": mean}, f, indent=2)

print("\nALL TRANSFER JOBS DONE")
