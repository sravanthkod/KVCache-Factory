"""
Grouped-CMA-ES ablation baseline (EvolKV-style) for the ARR October paper.

Reproduces the granularity + optimizer axis of EvolKV (Xu et al., EMNLP
Findings 2025, arXiv:2509.08315): instead of one independent search
dimension per layer (our full per-layer NAS), layers are grouped into
blocks of NAS_GROUP_SIZE (default 8, giving 4 groups for a 32-layer model)
and optimized with real CMA-ES (the `cma` PyPI package) instead of our
MLP-surrogate + differential-evolution search.

Zero changes to LAMP.py / HFF_mod.py / run_longbench_lamp.py /
run_ruler_lamp.py / ndsort.py: this script imports HFF_mod and calls
HFF_mod.call_HFF(...) directly, exactly like LAMP.py does, so decoding
(_decode_budgets), objective evaluation (get_objective_values) and
output.txt append-logging are all reused unmodified. Each CMA-ES candidate
(a D_group-dim vector) is expanded via np.repeat(..., NAS_GROUP_SIZE) into
a full 32-dim vector *before* being handed to call_HFF, so every logged
output.txt row is a normal 32-value-per-layer row -- fully compatible with
select_5way_snapshot.py / eval_top_configs_longbench.py /
eval_top_configs_ruler.py with no changes to those tools either.

NAS_METHOD is deliberately repurposed as the *output directory tag* here
(so runs land in e.g. CODE_B128/snapkv_cmaes_grouped/output.txt without
colliding with the real per-layer search's CODE_B128/snapkv/output.txt).
The actual eviction method used for model patching is NAS_REAL_METHOD
(default: same as NAS_METHOD_TAG's base, e.g. "snapkv"), applied by
monkeypatching the run_longbench_lamp/run_ruler_lamp module's NAS_METHOD
global after import -- see "monkeypatch the real method back" below.

Usage (from nas/, PYTHONPATH must include the repo root):
    NAS_BENCHMARK=longbench NAS_TASK_CATEGORY=CODE_B128 NAS_TARGET_BUDGET=128 \
    NAS_REAL_METHOD=snapkv NAS_METHOD_TAG=snapkv_cmaes_grouped \
    NAS_GROUP_SIZE=8 NAS_EVAL_BUDGET=120 NAS_CMAES_SIGMA0=0.3 NAS_SEED=42 \
    python3 run_grouped_cmaes.py

Smoke test: set NAS_EVAL_BUDGET low (e.g. 16) first and confirm the
decoded budgets in the resulting output.txt are contiguous per-group
(layers 0-7 identical, 8-15 identical, etc.), not cyclic.
"""

import os
import sys

import numpy as np

NAS_BENCHMARK = os.environ.get("NAS_BENCHMARK", "longbench").lower()
NAS_TARGET_BUDGET = int(os.environ.get("NAS_TARGET_BUDGET", "0"))
NAS_GROUP_SIZE = int(os.environ.get("NAS_GROUP_SIZE", "8"))
NAS_REAL_METHOD = os.environ.get("NAS_REAL_METHOD", "snapkv")
NAS_METHOD_TAG = os.environ.get("NAS_METHOD_TAG", f"{NAS_REAL_METHOD}_cmaes_grouped")
NAS_EVAL_BUDGET = int(os.environ.get("NAS_EVAL_BUDGET", "120"))
NAS_CMAES_SIGMA0 = float(os.environ.get("NAS_CMAES_SIGMA0", "0.3"))
NAS_SEED = int(os.environ.get("NAS_SEED", "42"))

if NAS_TARGET_BUDGET <= 0:
    raise SystemExit(
        "NAS_TARGET_BUDGET must be set (>0) -- this ablation runs in slice "
        "mode only, matching avg budget against the full per-layer NAS."
    )

# HFF_mod builds its output directory (NAS_TASK_CATEGORY/NAS_METHOD/) at
# import time from the NAS_METHOD env var -- set it to the *tag* before
# importing so runs land in their own directory, not the real method's.
os.environ["NAS_METHOD"] = NAS_METHOD_TAG
os.environ["NAS_BENCHMARK"] = NAS_BENCHMARK

import HFF_mod  # noqa: E402  (import after env setup, by design)

if NAS_BENCHMARK == "ruler":
    import run_ruler_lamp as rll  # noqa: E402
else:
    import run_longbench_lamp as rll  # noqa: E402

# Monkeypatch the real method back: HFF_mod's import above also caused
# rll's module-level NAS_METHOD to pick up NAS_METHOD_TAG (same env var) --
# get_objective_values reads rll.NAS_METHOD at call time to decide which
# eviction method to patch onto the model, so fix it here to the real one.
rll.NAS_METHOD = NAS_REAL_METHOD
# Same story for NAS_TARGET_BUDGET: override directly rather than relying
# on env-var-at-import-time, so this script's own env var is authoritative.
rll.NAS_TARGET_BUDGET = NAS_TARGET_BUDGET

try:
    import cma
except ImportError:
    raise SystemExit(
        "The `cma` package is required for this ablation (pip install cma "
        "in the conda env used to launch this script)."
    )

num_layers = rll._get_num_layers()
if num_layers % NAS_GROUP_SIZE != 0:
    raise SystemExit(
        f"num_layers={num_layers} is not evenly divisible by "
        f"NAS_GROUP_SIZE={NAS_GROUP_SIZE}"
    )
D_group = num_layers // NAS_GROUP_SIZE

print(f"[grouped-cmaes] benchmark={NAS_BENCHMARK} category={rll.NAS_TASK_CATEGORY} "
      f"real_method={NAS_REAL_METHOD} method_tag={NAS_METHOD_TAG} "
      f"target_budget={NAS_TARGET_BUDGET} num_layers={num_layers} "
      f"group_size={NAS_GROUP_SIZE} D_group={D_group} "
      f"eval_budget={NAS_EVAL_BUDGET} sigma0={NAS_CMAES_SIGMA0} seed={NAS_SEED}")
print(f"[grouped-cmaes] output dir: {HFF_mod.NAS_OUTPUT_DIR}")

# HFF_mod.call_HFF references the module-global `final_rows`, normally set
# by call_init() (LAMP.py's resume-from-log bookkeeping). We bypass
# call_init() entirely (its D/N/M dimensioning is BO-specific and doesn't
# apply here), so set it directly -- 0 means "no resume", matching default.
HFF_mod.final_rows = 0

es = cma.CMAEvolutionStrategy(
    [0.5] * D_group,
    NAS_CMAES_SIGMA0,
    {"bounds": [0, 1], "seed": NAS_SEED, "verbose": -9},
)

popsize = es.popsize
max_generations = max(1, -(-NAS_EVAL_BUDGET // popsize))  # ceil division
print(f"[grouped-cmaes] popsize={popsize}, planned generations={max_generations} "
      f"(~{popsize * max_generations} total evals)")

eval_count = 0
best_f2 = None
best_x = None
generation = 0

while not es.stop() and generation < max_generations:
    generation += 1
    solutions = es.ask()
    X_group = np.clip(np.array(solutions), 0.0, 1.0)          # (n, D_group)
    X_expanded = np.repeat(X_group, NAS_GROUP_SIZE, axis=1)   # (n, num_layers)

    f = HFF_mod.call_HFF(X_expanded)  # (n, 2): f[:,0]=avg budget, f[:,1]=f2 (minimize)
    es.tell(solutions, list(f[:, 1]))
    eval_count += len(solutions)

    gen_best_idx = int(np.argmin(f[:, 1]))
    gen_best_f2 = float(f[gen_best_idx, 1])
    if best_f2 is None or gen_best_f2 < best_f2:
        best_f2 = gen_best_f2
        best_x = X_group[gen_best_idx].copy()

    print(f"[grouped-cmaes] gen={generation}/{max_generations} evals={eval_count} "
          f"gen_best_f2={gen_best_f2:.4f} overall_best_f2={best_f2:.4f}", flush=True)

print(f"[grouped-cmaes] DONE. total_evals={eval_count} best_f2={best_f2:.4f} "
      f"best_x_group={best_x}")
sys.exit(0)
