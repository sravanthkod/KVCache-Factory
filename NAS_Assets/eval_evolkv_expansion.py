"""
EvolKV "search once, expand" ablation: take the B128 EvolKV reproduction's
`completed_budgets` and expand them to larger targets by EvolKV's KV Budget
Completion rule (proportional rescaling, no further optimization — Yu & Chai,
EMNLP Findings 2025, Sec. 3.2 / Fig. 4b), then score on full data exactly as
eval_evolkv_repro_full_data.py does.

Expansion: b_i = k_i * T / A (A = sum k, T = target * num_layers), largest-
remainder rounding so the layer mean equals the target exactly, clipped to
[64, 4096] (neither bound binds for B256-B1024 from a 67-214 source).

Writes only under <CATEGORY>/snapkv_evolkv_expanded/B<T>/ (never touches
snapkv_evolkv_repro/). A (category, target) whose full_data_eval_result.json
exists is skipped, so a killed run can be relaunched.

Usage (from NAS_Assets/, PYTHONPATH must include the repo root):
  python3 eval_evolkv_expansion.py --category CODE --targets 256,512,1024 [--dry_run]
"""

import argparse
import json
import os

import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--category", required=True, choices=["CODE", "SINGLE_DOCUMENT_QA"])
parser.add_argument("--targets", default="256,512,1024")
parser.add_argument("--source_budget", type=int, default=128)
parser.add_argument("--dry_run", action="store_true")
args = parser.parse_args()

MIN_B, MAX_B, METHOD = 64, 4096, "snapkv"
src_path = os.path.join(args.category, f"{METHOD}_evolkv_repro", f"B{args.source_budget}", "result.json")
src = json.load(open(src_path))
k = np.asarray(src["completed_budgets"], dtype=float)
L = len(k)


def expand(target):
    T = target * L
    raw = k * T / k.sum()
    out = np.floor(raw).astype(int)
    for i in np.argsort(-(raw - out), kind="stable")[: int(T - out.sum())]:
        out[i] += 1
    out = np.clip(out, MIN_B, MAX_B)
    assert out.sum() == T, (target, out.sum(), T)
    return out.tolist()


targets = [int(t) for t in args.targets.split(",")]
print(f"[source] {src_path}: {L} layers, mean={k.mean():.4f}, range {int(k.min())}-{int(k.max())}")
for t in targets:
    b = expand(t)
    print(f"[plan] {args.category} B{t}: mean={np.mean(b):.4f} range {min(b)}-{max(b)} budgets={b}")
if args.dry_run:
    raise SystemExit(0)

import run_longbench_lamp as rll  # noqa: E402
from run_longbench_lamp import _ensure_model_loaded  # noqa: E402

datasets = rll.load_data_clustering()[args.category]
model, tokenizer = _ensure_model_loaded(rll.NAS_MODEL_PATH, METHOD, rll.NAS_ATTN_IMPL)

for t in targets:
    out_dir = os.path.join(args.category, f"{METHOD}_evolkv_expanded", f"B{t}")
    out_path = os.path.join(out_dir, "full_data_eval_result.json")
    if os.path.isfile(out_path):
        print(f"[skip] {out_path} exists")
        continue
    budgets = expand(t)
    print(f"\n=== {args.category} B{t} (EvolKV B{args.source_budget} expanded) ===\n    budgets: {budgets}", flush=True)
    scores = {}
    for ds in datasets:
        _, score = rll.run_dataset_calibration_with_scoring(
            model=model, tokenizer=tokenizer, dataset=ds,
            data_dir=rll.NAS_DATA_DIR, model_path=rll.NAS_MODEL_PATH,
            max_capacity_prompts=budgets, sample_ratio=1.0, seed=rll.NAS_SEED, method=METHOD,
            save_predictions_path=os.path.join(out_dir, "full_data_predictions", f"{ds}.jsonl"),
        )
        scores[ds] = score
    mean = float(np.mean(list(scores.values())))
    print(f"    -> full-data mean score: {mean:.2f}", flush=True)
    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"category": args.category, "budget": t, "method": METHOD,
                   "source": f"B{args.source_budget} completed_budgets, proportional expansion",
                   "source_path": src_path, "completed_avg_budget": float(np.mean(budgets)),
                   "budgets": budgets, "per_dataset_scores": scores,
                   "full_data_mean_score": mean}, f, indent=2)

print("\nALL EVOLKV EXPANSION EVALS DONE")
