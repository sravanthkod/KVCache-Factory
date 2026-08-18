"""
RULER objective module for LAMP-NAS.

Mirrors run_longbench_lamp.py but evaluates candidates on the RULER benchmark
(data/RULER/<context_length>/<subtask>.jsonl). Selected by HFF_mod.py when
NAS_BENCHMARK=ruler.

Generation protocol matches run_ruler.py exactly (prompt = example["input"]
verbatim, no Llama-3 chat template, max_new_tokens=64, greedy) so scores are
directly comparable to the existing uniform-budget baselines in
<repo>/Meta-Llama-3-8B-Instruct/SNAP_KV_All_Budgets/results_ruler/.

Two objectives to MINIMIZE:
    f1 = average per-layer budget (memory)
    f2 = -string_match_all score (task_score) or evicted attention (evicted_attn)
"""

import os
import re
import json
import random

import numpy as np
import torch

# Reuse the NAS machinery from the LongBench objective module — budget
# decoding, per-layer budget injection (instance attrs + kv_cluster deletion)
# and the global model cache are benchmark-agnostic.
from run_longbench_lamp import (
    BUDGET_OPTIONS,
    x_point_to_budgets,
    set_model_budgets,
    _ensure_model_loaded,
    compute_evicted_attention,
)
from pyramidkv.eval_utils import build_stop_token_ids
from metrics import string_match_all

_NAS_ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_NAS_ASSETS_DIR)

# ─── RULER configs (mirroring run_ruler.py) ──────────────────────────────────

RULER_MAX_NEW_TOKENS = 64  # dataset2maxlen in run_ruler.py: 64 for all subtasks

model2maxlen = {
    "llama2": 3950,
    "llama-2": 3950,
    "llama3": 7500,
    "llama-3": 7500,
    "mistral": 31500,
}


def build_chat(prompt):
    # run_ruler.py applies this only for llama2 model paths
    return f"[INST] {prompt} [/INST]"


def load_ruler_clustering(json_path=None):
    """Load RULER subtask grouping from ruler_clustering.json."""
    if json_path is None:
        json_path = os.path.join(_NAS_ASSETS_DIR, "ruler_clustering.json")
    with open(json_path, "r") as f:
        return json.load(f)


def _load_ruler_dataset(dataset, data_dir, context_length, model_path_lower):
    """Load one RULER subtask jsonl. Returns list of examples or None if missing.

    RULER records: {"index", "input", "outputs", "length"} — the prompt is
    example["input"] verbatim (no template), gold answers are example["outputs"].
    """
    data_file = os.path.join(data_dir, str(context_length), f"{dataset}.jsonl")
    if not os.path.exists(data_file):
        print(f"[WARNING] Data file not found: {data_file}, skipping dataset '{dataset}'")
        return None

    test_data = []
    with open(data_file) as fp:
        for line in fp:
            example = json.loads(line)
            prompt = example["input"]
            if "llama2" in model_path_lower:
                prompt = build_chat(prompt)
            example["prompt"] = prompt
            test_data.append(example)
    return test_data


def _subsample(test_data, sample_ratio, seed):
    """Fixed-seed subsample — identical idiom to run_longbench_lamp.py."""
    rng = random.Random(seed)
    num_samples = max(1, int(len(test_data) * sample_ratio))
    if len(test_data) > num_samples:
        return rng.sample(test_data, num_samples)
    return test_data


def _holdout_complement(test_data, ratio, seed):
    """Return the examples the NAS fitness never saw.

    Reproduces the exact _subsample(test_data, ratio, seed) draw the search
    used, then excludes those examples (matched by their 'index' field).
    At ratio 0.1 on 500-sample RULER subtasks this returns 450 examples.
    """
    sampled = _subsample(test_data, ratio, seed)
    sampled_ids = {ex["index"] for ex in sampled}
    return [ex for ex in test_data if ex["index"] not in sampled_ids]


def _tokenize_and_truncate(tokenizer, prompt, model_max_len):
    """Tokenize; middle-truncate to model_max_len like run_ruler.py:157-163."""
    tokenized = tokenizer(
        prompt, padding="longest", return_tensors="pt", add_special_tokens=True
    ).to("cuda")
    input_ids = tokenized.input_ids
    if len(input_ids[0]) > model_max_len:
        half = int(model_max_len / 2)
        prompt = tokenizer.decode(
            input_ids[0][:half], skip_special_tokens=True
        ) + tokenizer.decode(
            input_ids[0][-half:], skip_special_tokens=True
        )
        tokenized = tokenizer(
            prompt, padding="longest", return_tensors="pt", add_special_tokens=True
        ).to("cuda")
    return tokenized


# ─── Run one RULER subtask with generation + scoring ─────────────────────────

def run_ruler_dataset_with_scoring(model, tokenizer, dataset, data_dir, model_path,
                                   max_capacity_prompts, context_length=4096,
                                   sample_ratio=0.3, seed=42, method="snapkv",
                                   save_predictions_path=None,
                                   holdout_of_ratio=None, holdout_seed=None):
    """
    Generate on a subsample of one RULER subtask and score with string_match_all.

    save_predictions_path: optional jsonl path; predictions are written in "w"
    mode (never append — run_ruler.py's append mode duplicates lines on re-runs).

    holdout_of_ratio / holdout_seed: when set, the data is first restricted to
    the complement of the NAS fitness subsample drawn with (ratio, seed) —
    i.e. only examples the search never saw. sample_ratio then applies to
    that complement (pass 1.0 to use all held-out examples).

    Returns:
        avg_budget (float), score (float 0-100) — or (None, None) if data missing.
    """
    model_path_lower = model_path.lower()
    model_max_len = 3950
    for key in model2maxlen:
        if key in model_path_lower:
            model_max_len = model2maxlen[key]
            break

    # Per-layer budget injection (instance attrs + kv_cluster deletion) —
    # run_ruler.py's shared-config write cannot express per-layer budgets.
    set_model_budgets(model, max_capacity_prompts, method=method)

    if method.lower() in ("adakv", "headkv"):
        for layer in model.model.layers:
            if hasattr(layer.self_attn, "kv_cluster"):
                delattr(layer.self_attn, "kv_cluster")

    stop_token_ids = build_stop_token_ids(model, tokenizer)

    test_data = _load_ruler_dataset(dataset, data_dir, context_length, model_path_lower)
    if test_data is None:
        return None, None
    if holdout_of_ratio is not None:
        test_data = _holdout_complement(test_data, holdout_of_ratio,
                                        holdout_seed if holdout_seed is not None else seed)
    sampled_data = _subsample(test_data, sample_ratio, seed)

    avg_budget = np.mean(max_capacity_prompts)

    predictions = []
    references = []

    for example in sampled_data:
        # AdaKV/HeadKV: prevent stale per-head cache metadata leaking across samples
        if method.lower() in ("adakv", "headkv"):
            for layer in model.model.layers:
                if hasattr(layer.self_attn, "kv_cluster"):
                    delattr(layer.self_attn, "kv_cluster")

        tokenized_prompts = _tokenize_and_truncate(tokenizer, example["prompt"], model_max_len)
        input_length = tokenized_prompts.input_ids.shape[-1]

        with torch.no_grad():
            output = model.generate(
                **tokenized_prompts,
                max_new_tokens=RULER_MAX_NEW_TOKENS,
                num_beams=1,
                do_sample=False,
                temperature=1.0,
                min_length=input_length + 1,
                eos_token_id=stop_token_ids,
            )

        pred = tokenizer.batch_decode(
            [output[0][input_length:]], skip_special_tokens=True
        )[0]
        predictions.append(pred)
        references.append(example["outputs"])

        torch.cuda.empty_cache()

    score = string_match_all(predictions, references)
    print(f"  dataset: {dataset} (ctx {context_length}, {len(sampled_data)} samples) "
          f"→ avg_budget={avg_budget:.1f}, string_match={score:.2f}")

    if save_predictions_path is not None:
        os.makedirs(os.path.dirname(save_predictions_path), exist_ok=True)
        with open(save_predictions_path, "w") as fout:
            for example, pred in zip(sampled_data, predictions):
                fout.write(json.dumps({
                    "index": example.get("index"),
                    "pred": pred,
                    "answers": example["outputs"],
                    "length": example.get("length"),
                }) + "\n")

    return avg_budget, score


# ─── Run one RULER subtask, prefill-only, harvesting evicted attention ───────

def run_ruler_dataset_calibration(model, tokenizer, dataset, data_dir, model_path,
                                  max_capacity_prompts, context_length=4096,
                                  sample_ratio=0.3, seed=42, method="snapkv"):
    """
    Cheap proxy objective: one prefill forward per sample, reading
    kv_cluster.evicted_attn_sum like run_longbench_lamp.run_dataset_calibration.

    Returns:
        avg_budget (float), avg_evicted_attn (float) — or (None, None) if data missing.
    """
    model_path_lower = model_path.lower()
    model_max_len = 3950
    for key in model2maxlen:
        if key in model_path_lower:
            model_max_len = model2maxlen[key]
            break

    set_model_budgets(model, max_capacity_prompts, method=method)

    test_data = _load_ruler_dataset(dataset, data_dir, context_length, model_path_lower)
    if test_data is None:
        return None, None
    sampled_data = _subsample(test_data, sample_ratio, seed)

    avg_budget = np.mean(max_capacity_prompts)

    evicted_attn_list = []
    total_attn_list = []

    for example in sampled_data:
        if method.lower() in ("adakv", "headkv"):
            for layer in model.model.layers:
                if hasattr(layer.self_attn, "kv_cluster"):
                    delattr(layer.self_attn, "kv_cluster")

        tokenized_prompts = _tokenize_and_truncate(tokenizer, example["prompt"], model_max_len)
        evicted_attn, total_attn = compute_evicted_attention(
            model, tokenized_prompts.input_ids, max_capacity_prompts
        )
        evicted_attn_list.append(evicted_attn)
        total_attn_list.append(total_attn)

        torch.cuda.empty_cache()

    avg_evicted_attn = np.mean(evicted_attn_list) if evicted_attn_list else 0.0
    avg_total_attn = np.mean(total_attn_list) if total_attn_list else 0.0
    print(f"  dataset: {dataset} → Average Attention Total: {avg_total_attn}; Evicted: {avg_evicted_attn}")

    return avg_budget, avg_evicted_attn


# ═══════════════════════════════════════════════════════════════════════════════
#  get_objective_values: called by HFF_mod.py → LAMP.py (NAS_BENCHMARK=ruler)
# ═══════════════════════════════════════════════════════════════════════════════

# ─── NAS Configuration (override via environment variables) ──────────────────

NAS_MODEL_PATH = os.environ.get(
    "NAS_MODEL_PATH",
    "/data/sravanth/models/Meta-Llama-3-8B-Instruct"
)
NAS_METHOD = os.environ.get("NAS_METHOD", "snapkv")
NAS_ATTN_IMPL = os.environ.get("NAS_ATTN_IMPL", "flash_attention_2")
NAS_DATA_DIR = os.environ.get("NAS_DATA_DIR", os.path.join(_REPO_ROOT, "data", "RULER"))
NAS_SAMPLE_RATIO = float(os.environ.get("NAS_SAMPLE_RATIO", "0.3"))
NAS_SEED = int(os.environ.get("NAS_SEED", "42"))
# RULER subtask group from ruler_clustering.json:
# RULER_NIAH_SINGLE, RULER_NIAH_MULTI, RULER_AGGREGATION, RULER_VT, RULER_ALL
NAS_TASK_CATEGORY = os.environ.get("NAS_TASK_CATEGORY", "RULER_NIAH_SINGLE")
# f2 metric: "task_score" (generation + string_match_all) or "evicted_attn" (prefill-only proxy)
NAS_F2_METRIC = os.environ.get("NAS_F2_METRIC", "task_score")
# RULER data exists for 4096 / 8192 / 16384. Note: llama-3 prompts are
# middle-truncated to 7500 tokens, so lengths beyond 4096 lose the needle.
NAS_CONTEXT_LENGTH = int(os.environ.get("NAS_CONTEXT_LENGTH", "4096"))
# NAS_GPUS="0,1,2" → one worker process per GPU (each with its own model
# replica); the group's subtasks are split across workers for every candidate.
# Unset / single GPU → sequential in-process evaluation (original behavior).
NAS_GPUS = [g for g in os.environ.get("NAS_GPUS", "").replace(" ", "").split(",") if g]

# ─── Fixed-budget-slice mode ("Design B") ─────────────────────────────────────
# NAS_TARGET_BUDGET > 0 pins every candidate's MEAN per-layer budget to the
# target: X is decoded as continuous proportional weights (any integer budgets,
# exact total) instead of the 7-option grid. Unset/0 → original unconstrained
# grid behavior, bit-for-bit.
NAS_TARGET_BUDGET = int(os.environ.get("NAS_TARGET_BUDGET", "0"))
NAS_MIN_BUDGET = int(os.environ.get("NAS_MIN_BUDGET", "16"))
NAS_MAX_BUDGET = int(os.environ.get("NAS_MAX_BUDGET", "4096"))


def x_point_to_budgets_continuous(X_point, num_layers, target_budget,
                                  min_budget=16, max_budget=4096):
    """Decode X in [0,1]^D to integer per-layer budgets whose SUM is exactly
    num_layers * target_budget (mean pinned to the target).

    Proportional split b_i = T * x_i / sum(x), clamped to [min_budget,
    max_budget] with the clamp residual redistributed over unclamped layers,
    then largest-remainder rounding on the unclamped layers for an exact
    total. Pure function of X (deterministic), so the surrogate can learn it.
    """
    T = int(target_budget) * num_layers
    w = np.clip(np.asarray(X_point, dtype=float)[:num_layers], 1e-6, None)
    if len(w) < num_layers:  # D < num_layers: cycle like the grid decoder
        w = np.array([w[i % len(w)] for i in range(num_layers)])

    # Iterative water-filling: fix over-max layers at max and redistribute the
    # surplus (which can lift under-min layers back above min), then fix
    # under-min layers at min. Converges in <= num_layers passes.
    budgets = np.zeros(num_layers)
    fixed = np.zeros(num_layers, dtype=bool)
    fixed_value = np.zeros(num_layers)
    for _ in range(num_layers):
        free = ~fixed
        if not free.any():
            break
        remaining = T - fixed_value[fixed].sum()
        budgets[free] = remaining * w[free] / w[free].sum()
        hi = (budgets > max_budget) & free
        if hi.any():
            fixed[hi] = True
            fixed_value[hi] = max_budget
            continue
        lo = (budgets < min_budget) & free
        if lo.any():
            fixed[lo] = True
            fixed_value[lo] = min_budget
            continue
        break
    budgets[fixed] = fixed_value[fixed]

    # Largest-remainder rounding on free layers → exact sum
    floors = np.floor(budgets)
    free = ~fixed
    shortfall = int(T - floors.sum())
    result = floors.astype(int)
    if shortfall > 0 and free.any():
        remainders = budgets - floors
        remainders[~free] = -1.0  # never bump clamped layers
        order = np.argsort(-remainders, kind="stable")
        for idx in order[:min(shortfall, int(free.sum()))]:
            result[idx] += 1
    # Residual only in the truly unreachable cases (target below min*L or
    # above max*L) — accepted; the f1 log column exposes any drift.
    result = np.clip(result, min_budget, max_budget)
    return [int(b) for b in result]


def _decode_budgets(X_point, num_layers):
    """Mode dispatcher: slice mode → continuous decode; else the original grid."""
    if NAS_TARGET_BUDGET > 0:
        return x_point_to_budgets_continuous(
            X_point, num_layers, NAS_TARGET_BUDGET, NAS_MIN_BUDGET, NAS_MAX_BUDGET)
    return x_point_to_budgets(X_point, num_layers)


# ─── Multi-GPU worker pool (used when len(NAS_GPUS) > 1) ─────────────────────

_WORKERS = None
_RESULT_Q = None
_NUM_LAYERS = None


def _worker_main(gpu_id, task_q, result_q):
    """Runs in a spawned subprocess pinned to one GPU.

    CUDA_VISIBLE_DEVICES must be set before the first CUDA call in this
    process; importing torch alone does not initialize CUDA, so overriding
    it here (post-import) is safe.
    """
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    while True:
        job = task_q.get()
        if job is None:
            break
        budgets, datasets, use_task_score = job
        try:
            model, tokenizer = _ensure_model_loaded(NAS_MODEL_PATH, NAS_METHOD, NAS_ATTN_IMPL)
            run_fn = run_ruler_dataset_with_scoring if use_task_score else run_ruler_dataset_calibration
            results = []
            for dataset in datasets:
                avg_budget, value = run_fn(
                    model=model,
                    tokenizer=tokenizer,
                    dataset=dataset,
                    data_dir=NAS_DATA_DIR,
                    model_path=NAS_MODEL_PATH,
                    max_capacity_prompts=budgets,
                    context_length=NAS_CONTEXT_LENGTH,
                    sample_ratio=NAS_SAMPLE_RATIO,
                    seed=NAS_SEED,
                    method=NAS_METHOD,
                )
                results.append((dataset, avg_budget, value))
            result_q.put(("ok", gpu_id, results))
        except Exception:
            import traceback
            result_q.put(("error", gpu_id, traceback.format_exc()))


def _ensure_workers():
    """Start one persistent worker per GPU in NAS_GPUS (forked once, reused).

    Uses fork, NOT spawn: spawn re-imports the parent's __main__ module and
    LAMP.py runs its whole optimization at module level (no __main__ guard),
    so spawned children would re-enter the NAS and deadlock. Fork is safe
    because the parent never initializes CUDA in parallel mode (num_layers
    comes from AutoConfig; all GPU work happens in the workers).
    """
    global _WORKERS, _RESULT_Q
    if _WORKERS is not None:
        return
    if torch.cuda.is_initialized():
        raise RuntimeError(
            "CUDA already initialized in the parent process — cannot fork GPU "
            "workers safely. Ensure nothing touches CUDA before the first "
            "get_objective_values call when NAS_GPUS is set."
        )
    import multiprocessing as mp
    ctx = mp.get_context("fork")
    _RESULT_Q = ctx.Queue()
    _WORKERS = []
    for gpu_id in NAS_GPUS:
        task_q = ctx.Queue()
        proc = ctx.Process(target=_worker_main, args=(gpu_id, task_q, _RESULT_Q), daemon=True)
        proc.start()
        _WORKERS.append((proc, task_q))
    print(f"[run_ruler_lamp] Started {len(_WORKERS)} GPU workers on GPUs {NAS_GPUS}")


def _get_num_layers():
    """num_hidden_layers without loading weights (parent stays CPU-only)."""
    global _NUM_LAYERS
    if _NUM_LAYERS is None:
        from transformers import AutoConfig
        _NUM_LAYERS = AutoConfig.from_pretrained(NAS_MODEL_PATH).num_hidden_layers
    return _NUM_LAYERS


def get_objective_values(X_point):
    """
    Evaluate the two NAS objectives on RULER for one per-layer budget config.

    Args:
        X_point: D-dim numpy array in [0,1]; each dim discretized to
                 BUDGET_OPTIONS = [64, 128, 256, 512, 1024, 2048, 4096].

    Returns:
        (f1, f2) to MINIMIZE:
            f1 = average per-layer budget
            f2 = -string_match_all score (task_score) or evicted attention
    """
    clustering = load_ruler_clustering()
    task_category = NAS_TASK_CATEGORY
    # Slice runs use suffixed category names (e.g. RULER_ALL_B1536) so their
    # outputs get their own directory; the datasets come from the base key.
    lookup_key = task_category if task_category in clustering \
        else re.sub(r"_B\d+$", "", task_category)
    if lookup_key not in clustering:
        raise ValueError(
            f"Task category '{task_category}' (lookup '{lookup_key}') not found in "
            f"ruler_clustering.json. Available: {list(clustering.keys())}"
        )
    datasets = clustering[lookup_key]
    mode = f"slice(target={NAS_TARGET_BUDGET})" if NAS_TARGET_BUDGET > 0 else "unconstrained"
    print(f"[get_objective_values/RULER] Task category: {task_category} ({mode}), "
          f"context length: {NAS_CONTEXT_LENGTH}, datasets: {datasets}")

    use_task_score = (NAS_F2_METRIC == "task_score")

    # ── Parallel path: split subtasks across one worker per GPU ──────────────
    if len(NAS_GPUS) > 1:
        num_layers = _get_num_layers()
        max_capacity_prompts = _decode_budgets(X_point, num_layers)
        print(f"[get_objective_values/RULER] X_point (first 5): {X_point[:5]}")
        print(f"[get_objective_values/RULER] Per-layer budgets: {max_capacity_prompts}")
        print(f"[get_objective_values/RULER] Avg budget: {np.mean(max_capacity_prompts):.1f}")

        _ensure_workers()
        chunks = [datasets[i::len(_WORKERS)] for i in range(len(_WORKERS))]
        active = 0
        for (proc, task_q), chunk in zip(_WORKERS, chunks):
            if chunk:
                task_q.put((max_capacity_prompts, chunk, use_task_score))
                active += 1

        all_avg_budgets = []
        all_f2_values = []
        for _ in range(active):
            status, gpu_id, payload = _RESULT_Q.get()
            if status == "error":
                raise RuntimeError(f"GPU {gpu_id} worker failed:\n{payload}")
            for dataset, avg_budget, value in payload:
                if avg_budget is not None:
                    all_avg_budgets.append(avg_budget)
                    all_f2_values.append(value)
                else:
                    print(f"  → {dataset} SKIPPED (data not found)")

        return _finalize_objectives(all_avg_budgets, all_f2_values, use_task_score)

    # ── Sequential path (single GPU / NAS_GPUS unset) ─────────────────────────
    model, tokenizer = _ensure_model_loaded(NAS_MODEL_PATH, NAS_METHOD, NAS_ATTN_IMPL)

    num_layers = len(model.model.layers)
    max_capacity_prompts = _decode_budgets(X_point, num_layers)

    print(f"[get_objective_values/RULER] X_point (first 5): {X_point[:5]}")
    print(f"[get_objective_values/RULER] Per-layer budgets: {max_capacity_prompts}")
    print(f"[get_objective_values/RULER] Avg budget: {np.mean(max_capacity_prompts):.1f}")

    all_avg_budgets = []
    all_f2_values = []

    for idx, dataset in enumerate(datasets):
        print(f"[get_objective_values/RULER] Dataset {idx+1}/{len(datasets)}: {dataset}")

        if use_task_score:
            avg_budget, f2_value = run_ruler_dataset_with_scoring(
                model=model,
                tokenizer=tokenizer,
                dataset=dataset,
                data_dir=NAS_DATA_DIR,
                model_path=NAS_MODEL_PATH,
                max_capacity_prompts=max_capacity_prompts,
                context_length=NAS_CONTEXT_LENGTH,
                sample_ratio=NAS_SAMPLE_RATIO,
                seed=NAS_SEED,
                method=NAS_METHOD,
            )
        else:
            avg_budget, f2_value = run_ruler_dataset_calibration(
                model=model,
                tokenizer=tokenizer,
                dataset=dataset,
                data_dir=NAS_DATA_DIR,
                model_path=NAS_MODEL_PATH,
                max_capacity_prompts=max_capacity_prompts,
                context_length=NAS_CONTEXT_LENGTH,
                sample_ratio=NAS_SAMPLE_RATIO,
                seed=NAS_SEED,
                method=NAS_METHOD,
            )

        if avg_budget is not None:
            all_avg_budgets.append(avg_budget)
            all_f2_values.append(f2_value)
        else:
            print("  → SKIPPED (data not found)")

    return _finalize_objectives(all_avg_budgets, all_f2_values, use_task_score)


def _finalize_objectives(all_avg_budgets, all_f2_values, use_task_score):
    if len(all_avg_budgets) == 0:
        avg_budget = float(max(BUDGET_OPTIONS))
        f2_value = 1.0  # worst case
    else:
        avg_budget = np.mean(all_avg_budgets)
        f2_value = np.mean(all_f2_values)

    f1 = avg_budget
    if use_task_score:
        f2 = -1.0 * f2_value  # minimize negative score = maximize score
    else:
        f2 = f2_value

    metric_name = "task_score" if use_task_score else "evicted_attn"
    print(f"[get_objective_values/RULER] RESULT: avg_budget={avg_budget:.1f}, "
          f"{metric_name}={f2_value:.6f}, f1={f1:.1f}, f2={f2:.6f}")

    return f1, f2
