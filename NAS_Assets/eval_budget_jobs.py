"""
Generic LongBench evaluator for ablations: score explicit per-layer budget vectors.

Input is a jobs.json (list of {name, category, method, budgets[32], sample_ratio}) written by
ablation_plans.py. Each job is scored exactly as eval_evolkv_repro_full_data.py /
eval_evolkv_expansion.py do (rll.run_dataset_calibration_with_scoring, seed=rll.NAS_SEED,
the category's datasets) at the job's sample_ratio, and written to
<out_dir>/results/<name>.json. Jobs whose result file exists are skipped, so a killed run can
simply be relaunched. Never touches any <CAT>_B<T>/ cell directory (no clobbering of the 5-way
eval_results.csv / predictions).

Usage (from NAS_Assets/, PYTHONPATH must include the repo root):
  python3 eval_budget_jobs.py --jobs ablations/search_budget_curve/jobs.json \
      --out_dir ablations/search_budget_curve
"""

import argparse
import json
import os
import time

import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--jobs", required=True)
parser.add_argument("--out_dir", required=True)
parser.add_argument("--dry_run", action="store_true")
args = parser.parse_args()

jobs = json.load(open(args.jobs))
res_dir = os.path.join(args.out_dir, "results")
todo = [j for j in jobs if not os.path.isfile(os.path.join(res_dir, j["name"] + ".json"))]
print(f"{len(jobs)} jobs, {len(jobs) - len(todo)} already done, {len(todo)} to run")
for j in todo:
    assert len(j["budgets"]) == 32 and min(j["budgets"]) >= 16, j["name"]
    print(f"  todo {j['name']}: {j['category']} {j['method']} ratio={j['sample_ratio']} "
          f"mean={np.mean(j['budgets']):.1f} min={min(j['budgets'])}")
if args.dry_run or not todo:
    raise SystemExit(0)

import run_longbench_lamp as rll  # noqa: E402
from run_longbench_lamp import _ensure_model_loaded  # noqa: E402

os.makedirs(res_dir, exist_ok=True)
loaded = {}
for j in todo:
    method = j["method"]
    if method not in loaded:
        loaded[method] = _ensure_model_loaded(rll.NAS_MODEL_PATH, method, rll.NAS_ATTN_IMPL)
    model, tokenizer = loaded[method]
    datasets = rll.load_data_clustering()[j["category"]]
    t0 = time.time()
    print(f"\n=== {j['name']} ratio={j['sample_ratio']} budgets={j['budgets']}", flush=True)
    scores = {}
    for ds in datasets:
        _, score = rll.run_dataset_calibration_with_scoring(
            model=model, tokenizer=tokenizer, dataset=ds, data_dir=rll.NAS_DATA_DIR,
            model_path=rll.NAS_MODEL_PATH, max_capacity_prompts=j["budgets"],
            sample_ratio=j["sample_ratio"], seed=rll.NAS_SEED, method=method)
        scores[ds] = score
    mean = float(np.mean(list(scores.values())))
    print(f"    -> mean score {mean:.2f} ({time.time() - t0:.0f}s)", flush=True)
    with open(os.path.join(res_dir, j["name"] + ".json"), "w") as f:
        json.dump({**j, "avg_budget": float(np.mean(j["budgets"])), "per_dataset_scores": scores,
                   "mean_score": mean, "eval_seconds": time.time() - t0}, f, indent=2)
print("\nALL JOBS DONE")
