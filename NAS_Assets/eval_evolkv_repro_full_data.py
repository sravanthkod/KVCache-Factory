"""
Full-data (sample_ratio=1.0) re-evaluation of the EvolKV grouped-CMA-ES
reproduction ablation's `completed_budgets` (TODOS #38).

Unlike eval_top_configs_longbench.py, this does NOT decode an x-vector --
run_evolkv_reproduction.py already stores real, final per-layer integer
budgets in result.json's "completed_budgets" field. This script just loads
each result.json, feeds its completed_budgets straight into the same
run_dataset_calibration_with_scoring path used everywhere else in this
project, at sample_ratio=1.0, and writes a comparable eval_results.csv next
to each run's result.json.

Usage (from NAS_Assets/, PYTHONPATH must include the repo root):
  python3 eval_evolkv_repro_full_data.py
"""

import json
import os

import numpy as np

import run_longbench_lamp as rll
from run_longbench_lamp import _ensure_model_loaded

RUNS = [
    ("CODE", 128, "snapkv"),
    ("CODE", 512, "snapkv"),
    ("CODE", 1024, "snapkv"),
    ("SINGLE_DOCUMENT_QA", 128, "snapkv"),
    ("SINGLE_DOCUMENT_QA", 512, "snapkv"),
    ("SINGLE_DOCUMENT_QA", 1024, "snapkv"),
]

clustering = rll.load_data_clustering()
model, tokenizer = _ensure_model_loaded(rll.NAS_MODEL_PATH, "snapkv", rll.NAS_ATTN_IMPL)

for category, budget, method in RUNS:
    run_dir = os.path.join(category, f"{method}_evolkv_repro", f"B{budget}")
    result_path = os.path.join(run_dir, "result.json")
    with open(result_path) as f:
        result = json.load(f)

    budgets = result["completed_budgets"]
    datasets = clustering[category]
    print(f"\n=== {category} B{budget} ({method}) — completed_avg_budget="
          f"{result['completed_avg_budget']:.2f} ===")
    print(f"    budgets: {budgets}")

    scores = {}
    for dataset in datasets:
        pred_path = os.path.join(run_dir, "full_data_predictions", f"{dataset}.jsonl")
        _, score = rll.run_dataset_calibration_with_scoring(
            model=model,
            tokenizer=tokenizer,
            dataset=dataset,
            data_dir=rll.NAS_DATA_DIR,
            model_path=rll.NAS_MODEL_PATH,
            max_capacity_prompts=budgets,
            sample_ratio=1.0,
            seed=rll.NAS_SEED,
            method=method,
            save_predictions_path=pred_path,
        )
        scores[dataset] = score

    mean_score = float(np.mean(list(scores.values())))
    print(f"    -> full-data mean score: {mean_score:.2f}")

    out = {
        "category": category, "budget": budget, "method": method,
        "completed_avg_budget": result["completed_avg_budget"],
        "budgets": budgets,
        "per_dataset_scores": scores,
        "full_data_mean_score": mean_score,
    }
    out_path = os.path.join(run_dir, "full_data_eval_result.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"    Written to {out_path}")

print("\nALL EVOLKV FULL-DATA RE-EVALS DONE")
