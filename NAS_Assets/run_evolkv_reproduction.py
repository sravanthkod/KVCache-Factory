"""
Faithful reproduction of EvolKV (Yu & Chai, EMNLP Findings 2025,
arXiv:2509.08315) -- the literal algorithm from the paper, not just its
grouping/optimizer family. This supersedes the earlier
`run_grouped_cmaes.py` (which ran one joint CMA-ES over 4 group-shared
values -- not what the paper does).

Reproduced exactly from the paper text (Section 3, Algorithm 1, Eq 1-2,
Section 4.1, Table 7):

- Objective (Eq 1), MAXIMIZED:
      S* = argmax_S  f(S) * (1 + lambda * CacheScore(S, c))
  where f(S) is the downstream task score of compression scheme S, and
  lambda = 0.3 (paper's Section 4.1 hyperparameter).

- CacheScore (Eq 2), with k_bar = mean per-layer budget, gamma = 0.2:
      k_bar > c:  max(0, 1 - (k_bar - c) / c)
      k_bar <= c: 1 - gamma * (1 - k_bar / c)

- Grouping: contiguous blocks of n_g=8 layers (J = ceil(L/n_g) groups; 4
  groups for a 32-layer model). Each group owns n_g INDEPENDENT per-layer
  budget variables -- grouping controls which layers are optimized
  *together in one CMA-ES call*, it does NOT force them to a shared value.

- Algorithm 1: sequential, bottom-up, one group at a time. All layers
  start at the target budget c. For each group (in order), a *fresh*
  CMA-ES instance searches only that group's n_g dimensions for M
  iterations, with already-optimized groups frozen at their best-found
  values and not-yet-optimized groups still at the uniform-c init. The
  running global best (G_best, F_best) is tracked across the *entire*
  procedure (not reset per group), exactly matching Algorithm 1's
  G*/F_best bookkeeping.

- CMA-ES settings (Section 4.1 + Table 7): sigma0 = 0.3, population size
  = 4 + floor(3 * ln(n_g)) = 10 for n_g=8. The paper does not state a
  domain/parameterization for the raw integer budgets under CMA-ES (whose
  sigma is inherently relative to its search-space scale) -- we search in
  NORMALIZED ratio space x_i = k_i / c (so sigma0=0.3 means an initial
  +/-30% spread around the target budget, a self-consistent reading of
  the stated sigma value), then map back via k_i = round(x_i * c),
  clipped to [NAS_MIN_BUDGET, NAS_MAX_BUDGET] as a sane engineering bound
  (not paper-specified -- the paper gives no explicit min/max).
  NAS_EVOLKV_M (iterations per group) is ALSO not given a number in the
  paper (Algorithm 1 lists M as a free parameter only) -- default here is
  our own choice, flagged as such.

- KV Budget Completion (post-search, one-time proportional rescale to
  hit the exact target average c):
      A = sum(G_best), T = c * L, delta = T - A
      b_i = ceil(k_i + (k_i / A) * delta), clipped to [min, max]

- Calibration: paper uses a small FIXED sample count (~30 total, e.g. one
  representative dataset or a handful of instances per sub-dataset), not
  a fraction of the full dataset like the rest of our pipeline's
  NAS_SAMPLE_RATIO convention. NAS_EVOLKV_CALIB_SAMPLES (default 30) is
  split evenly across the category's datasets and converted to a
  per-dataset sample_ratio at runtime (based on each dataset's actual
  line count) before calling the existing
  run_dataset_calibration_with_scoring / run_ruler_dataset_with_scoring.

Reuses (imports only, zero changes): _ensure_model_loaded,
load_data_clustering / load_ruler_clustering,
run_dataset_calibration_with_scoring / run_ruler_dataset_with_scoring,
_get_num_layers -- from run_longbench_lamp.py / run_ruler_lamp.py. Does
NOT go through HFF_mod/LAMP.py/_decode_budgets at all -- this algorithm's
parameterization (free integer budgets, soft penalty, sequential
per-group search) doesn't fit that machinery's conventions.

Usage (from NAS_Assets/, PYTHONPATH must include the repo root):
    NAS_BENCHMARK=longbench NAS_TASK_CATEGORY=CODE NAS_TARGET_BUDGET=128 \
    NAS_REAL_METHOD=snapkv NAS_GROUP_SIZE=8 NAS_EVOLKV_M=15 \
    NAS_EVOLKV_CALIB_SAMPLES=30 NAS_SEED=42 \
    python3 run_evolkv_reproduction.py
"""

import json
import math
import os
import random

import numpy as np

NAS_BENCHMARK = os.environ.get("NAS_BENCHMARK", "longbench").lower()
CATEGORY = os.environ["NAS_TASK_CATEGORY"]          # base category, e.g. "CODE" (no _B<n> suffix)
TARGET_BUDGET = float(os.environ["NAS_TARGET_BUDGET"])  # c
REAL_METHOD = os.environ.get("NAS_REAL_METHOD", "snapkv")
GROUP_SIZE = int(os.environ.get("NAS_GROUP_SIZE", "8"))          # n_g
LAMBDA = float(os.environ.get("NAS_EVOLKV_LAMBDA", "0.3"))       # paper: 0.3
GAMMA = float(os.environ.get("NAS_EVOLKV_GAMMA", "0.2"))         # paper: 0.2
SIGMA0 = float(os.environ.get("NAS_EVOLKV_SIGMA0", "0.3"))       # paper: 0.3 (our ratio-space reading)
M_ITERS = int(os.environ.get("NAS_EVOLKV_M", "15"))              # NOT given in paper -- our choice
CALIB_SAMPLES = int(os.environ.get("NAS_EVOLKV_CALIB_SAMPLES", "30"))  # paper: ~30 total
MIN_BUDGET = int(os.environ.get("NAS_MIN_BUDGET", "64"))
MAX_BUDGET = int(os.environ.get("NAS_MAX_BUDGET", "4096"))
SEED = int(os.environ.get("NAS_SEED", "42"))

os.environ["NAS_BENCHMARK"] = NAS_BENCHMARK
os.environ.setdefault("NAS_METHOD", REAL_METHOD)
os.environ.setdefault("NAS_TASK_CATEGORY", CATEGORY)

if NAS_BENCHMARK == "ruler":
    import run_ruler_lamp as rll
    from run_ruler_lamp import load_ruler_clustering as load_clustering
    from run_ruler_lamp import run_ruler_dataset_with_scoring as run_dataset_with_scoring
else:
    import run_longbench_lamp as rll
    from run_longbench_lamp import load_data_clustering as load_clustering
    from run_longbench_lamp import run_dataset_calibration_with_scoring as run_dataset_with_scoring

rll.NAS_METHOD = REAL_METHOD

try:
    import cma
except ImportError:
    raise SystemExit("The `cma` package is required (pip install cma).")


def popsize_formula(n):
    """Paper's empirical formula (Section 'Effect of Group Size'): 4 + floor(3*ln(n))."""
    return 4 + int(3 * math.log(n))


def cache_score(k_bar, c, gamma):
    """Eq 2."""
    if k_bar > c:
        return max(0.0, 1.0 - (k_bar - c) / c)
    return 1.0 - gamma * (1.0 - k_bar / c)


def count_lines(path):
    with open(path) as f:
        return sum(1 for _ in f)


model, tokenizer = rll._ensure_model_loaded(rll.NAS_MODEL_PATH, REAL_METHOD, rll.NAS_ATTN_IMPL)
num_layers = len(model.model.layers)
if num_layers % GROUP_SIZE != 0:
    raise SystemExit(f"num_layers={num_layers} not divisible by NAS_GROUP_SIZE={GROUP_SIZE}")
J = num_layers // GROUP_SIZE

clustering = load_clustering()
datasets = clustering[CATEGORY]

# Convert the paper's fixed absolute calibration-sample count into a
# per-dataset sample_ratio (run_dataset_with_scoring's native knob).
data_dir = rll.NAS_DATA_DIR
per_dataset_target = max(1, CALIB_SAMPLES // len(datasets))
sample_ratios = {}
for ds in datasets:
    fname = f"{ds}.jsonl" if NAS_BENCHMARK != "ruler" else f"{rll.NAS_CONTEXT_LENGTH}/{ds}.jsonl"
    fpath = os.path.join(data_dir, fname)
    n_lines = count_lines(fpath) if os.path.isfile(fpath) else per_dataset_target
    sample_ratios[ds] = min(1.0, per_dataset_target / max(1, n_lines))

print(f"[evolkv] benchmark={NAS_BENCHMARK} category={CATEGORY} real_method={REAL_METHOD} "
      f"target_budget={TARGET_BUDGET} num_layers={num_layers} group_size={GROUP_SIZE} J={J} "
      f"lambda={LAMBDA} gamma={GAMMA} sigma0={SIGMA0} M={M_ITERS} "
      f"calib_samples_total={CALIB_SAMPLES} (per-dataset ratios: {sample_ratios}) seed={SEED}")


def evaluate_fitness(full_budgets, group_budgets):
    """f(S) * (1 + lambda * CacheScore(group, c)) -- Eq 1, with CacheScore
    applied to the *group's own* mean (Algorithm 1 line 11: CacheScore(S_g, c)),
    not the full 32-layer vector's mean."""
    scores = []
    # set_model_budgets does `isinstance(x, list)` to decide whether to
    # broadcast a scalar vs. use per-layer values -- a numpy array fails
    # that check and gets broadcast as one giant "scalar", corrupting
    # every layer's budget. Must be a plain Python list of ints.
    full_budgets_list = [int(b) for b in full_budgets]
    for ds in datasets:
        _, score = run_dataset_with_scoring(
            model=model, tokenizer=tokenizer, dataset=ds, data_dir=data_dir,
            model_path=rll.NAS_MODEL_PATH, max_capacity_prompts=full_budgets_list,
            sample_ratio=sample_ratios[ds], seed=SEED, eval_batch_size=1, method=REAL_METHOD,
        )
        if score is not None:
            scores.append(score)
    f_S = float(np.mean(scores)) if scores else 0.0
    k_bar_group = float(np.mean(group_budgets))
    cs = cache_score(k_bar_group, TARGET_BUDGET, GAMMA)
    fitness = f_S * (1.0 + LAMBDA * cs)
    return fitness, f_S, cs


# Algorithm 1: G* <- G_init (uniform c), F_best <- -inf
G_best = np.full(num_layers, TARGET_BUDGET, dtype=float)
F_best = -math.inf

lo_ratio = MIN_BUDGET / TARGET_BUDGET
hi_ratio = MAX_BUDGET / TARGET_BUDGET

for j in range(J):
    lo, hi = j * GROUP_SIZE, min((j + 1) * GROUP_SIZE, num_layers)
    n = hi - lo
    popsize = popsize_formula(n)
    print(f"[evolkv] === Group {j+1}/{J} (layers {lo}-{hi-1}, n={n}, popsize={popsize}) ===", flush=True)

    es = cma.CMAEvolutionStrategy(
        [1.0] * n, SIGMA0,
        {"bounds": [lo_ratio, hi_ratio], "popsize": popsize, "seed": SEED + j, "verbose": -9},
    )

    for m in range(M_ITERS):
        solutions = es.ask()
        neg_fitnesses = []
        for x_ratio in solutions:
            group_budgets = np.round(np.clip(np.array(x_ratio) * TARGET_BUDGET, MIN_BUDGET, MAX_BUDGET)).astype(int)
            candidate = G_best.copy()
            candidate[lo:hi] = group_budgets
            fitness, f_S, cs = evaluate_fitness(candidate, group_budgets)
            neg_fitnesses.append(-fitness)
            if fitness > F_best:
                F_best = fitness
                G_best = candidate.copy()
                print(f"[evolkv]   gen={m+1}/{M_ITERS} NEW BEST fitness={fitness:.4f} "
                      f"f(S)={f_S:.4f} CacheScore={cs:.4f} group_budgets={list(group_budgets)}", flush=True)
        es.tell(solutions, neg_fitnesses)
        print(f"[evolkv]   gen={m+1}/{M_ITERS} done, running F_best={F_best:.4f}", flush=True)

print(f"[evolkv] Search complete. G_best avg={G_best.mean():.1f} F_best={F_best:.4f}")
print(f"[evolkv] G_best budgets: {list(G_best.astype(int))}")

# KV Budget Completion: proportional rescale to hit the exact target average.
A = float(G_best.sum())
T = TARGET_BUDGET * num_layers
delta = T - A
completed = np.array([math.ceil(k + (k / A) * delta) for k in G_best])
completed = np.clip(completed, MIN_BUDGET, MAX_BUDGET).astype(int)
print(f"[evolkv] KV Budget Completion: A={A:.1f} T={T:.1f} delta={delta:.1f}")
print(f"[evolkv] Completed budgets (avg={completed.mean():.2f}): {list(completed)}")

final_fitness, final_f_S, final_cs = evaluate_fitness(completed, completed)
print(f"[evolkv] FINAL (post-completion) f(S)={final_f_S:.4f} CacheScore={final_cs:.4f} "
      f"fitness={final_fitness:.4f}")

out_dir = os.path.join(CATEGORY, f"{REAL_METHOD}_evolkv_repro", f"B{int(TARGET_BUDGET)}")
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, "result.json"), "w") as f:
    json.dump({
        "category": CATEGORY, "method": REAL_METHOD, "target_budget": TARGET_BUDGET,
        "group_size": GROUP_SIZE, "lambda": LAMBDA, "gamma": GAMMA, "sigma0": SIGMA0,
        "M_iterations_per_group": M_ITERS, "calib_samples_total": CALIB_SAMPLES,
        "G_best_budgets": G_best.astype(int).tolist(), "G_best_fitness": F_best,
        "completed_budgets": completed.tolist(), "completed_avg_budget": float(completed.mean()),
        "final_task_score": final_f_S, "final_cache_score": final_cs, "final_fitness": final_fitness,
    }, f, indent=2)
print(f"[evolkv] Wrote {out_dir}/result.json")
