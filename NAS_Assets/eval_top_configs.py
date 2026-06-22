#!/usr/bin/env python3
"""
Evaluate top NAS configurations on the FULL dataset — with multi-GPU support.

Usage:
    # Single GPU (backward compatible)
    python eval_top_configs.py SUMMARIZATION --top-n 5

    # Multi-GPU: run 3 configs in parallel on 3 GPUs
    python eval_top_configs.py SUMMARIZATION --top-n 5 --num-gpus 3

    # Multi-GPU: specific GPUs
    CUDA_VISIBLE_DEVICES=0,1,2 python eval_top_configs.py SUMMARIZATION --top-n 5 --num-gpus 3

    # Specific config indices
    python eval_top_configs.py SINGLE_DOCUMENT_QA --config-indices 0 2 5 --num-gpus 3

This script:
1. Reads the Pareto-optimal (rank 1) configs from <TASK>/output.txt
2. Converts [0,1] vectors to per-layer budgets using BUDGET_OPTIONS
3. Distributes configs across GPUs for parallel evaluation
4. Runs full evaluation (100% data) on each dataset in the task category
5. Computes actual task metrics (rouge, f1, etc.) — not just evicted attention
6. Saves predictions + summary results
"""

import os
import sys
import csv
import json
import random
import argparse
import time
from datetime import datetime

import numpy as np
from tqdm import tqdm

import torch
import torch.multiprocessing as mp
from transformers import AutoModelForCausalLM, AutoTokenizer

# ─── Import from run_longbench_lamp.py ────────────────────────────────────────
from run_longbench_lamp import (
    BUDGET_OPTIONS,
    dataset2maxlen,
    model2prompt,
    model2maxlen,
    dataset2metric_fn,
    build_chat,
    set_seed,
    scorer,
    load_data_clustering,
    x_point_to_budgets,
    set_model_budgets,
)

# ─── Import ndsort for extracting rank-1 configs ──────────────────────────────
from ndsort import rank_one


# ═══════════════════════════════════════════════════════════════════════════════
#  Extract rank-1 (Pareto-optimal) configurations from output.txt
# ═══════════════════════════════════════════════════════════════════════════════

def get_rank1_configs(task_name):
    """Read output.txt, do non-dominated sort, return rank-1 config rows."""
    output_file = os.path.join(task_name, 'output.txt')
    if not os.path.isfile(output_file):
        print(f"Error: {output_file} not found!")
        sys.exit(1)

    # Read all rows
    all_rows = []
    with open(output_file, 'r') as f:
        reader = csv.reader(f, delimiter=' ')
        for row in reader:
            all_rows.append([float(x) for x in row])

    if len(all_rows) == 0:
        print(f"Error: No rows found in {output_file}")
        sys.exit(1)

    # Extract objectives (last 2 columns): penalty (avg_budget), score (evicted_attn)
    # Both are to be MINIMIZED
    rank_input = []
    seen = []
    row_index_map = {}  # maps tuple(objectives) -> row index in all_rows
    for i, row in enumerate(all_rows):
        obj = [row[-2], row[-1]]
        if obj not in seen:
            seen.append(obj)
            row_index_map[tuple(obj)] = i
            rank_input.append(obj)

    # Non-dominated sort — get rank 1
    rank_inp = np.array(rank_input)
    rank_out = rank_one(rank_inp)

    # Extract indices of rank-1 points
    indices = []
    for val in rank_out[0]:
        indices.append(row_index_map[tuple(val)])

    # Get the full config rows for rank-1
    rank1_configs = [all_rows[i] for i in indices]

    print(f"rank1_configs are {rank1_configs}")

    print(f"Found {len(rank1_configs)} rank-1 (Pareto-optimal) configs out of {len(all_rows)} total")

    return rank1_configs


def select_configs(rank1_configs, top_n=None, config_indices=None):
    """Select a subset of rank-1 configs to evaluate.

    If config_indices is given, select those specific indices after sorting by penalty (avg_budget) ascending.
    Otherwise, if top_n is given, select top_n configs sorted by penalty (avg_budget) ascending.
    Otherwise, return all rank-1 configs.
    """
    # Sort configs by penalty (avg_budget) ascending — cheaper configs first
    sorted_configs = sorted(rank1_configs, key=lambda x: x[-2])

    if config_indices is not None:
        selected = []
        for idx in config_indices:
            if idx < 0 or idx >= len(sorted_configs):
                print(f"Warning: config index {idx} out of range [0, {len(sorted_configs)-1}], skipping")
                continue
            selected.append(sorted_configs[idx])
        return selected

    if top_n is not None and top_n < len(sorted_configs):
        # Pick evenly spaced configs from the Pareto front
        indices = np.linspace(0, len(sorted_configs) - 1, top_n, dtype=int)
        selected = [sorted_configs[i] for i in indices]
        print(f"Selected {len(selected)} configs (evenly spaced from Pareto front)")
    else:
        selected = sorted_configs

    return selected


# ═══════════════════════════════════════════════════════════════════════════════
#  Full evaluation on a single dataset
# ═══════════════════════════════════════════════════════════════════════════════

def evaluate_dataset(model, tokenizer, dataset, data_dir, model_path,
                     max_capacity_prompts, method="snapkv", eval_batch_size=1,
                     device="cuda"):
    """
    Run FULL evaluation on a single dataset with the given per-layer budgets.
    Returns list of predictions and list of answers for scoring.
    """
    model_path_lower = model_path.lower()
    model_max_len = 3950
    for key in model2maxlen:
        if key in model_path_lower:
            model_max_len = model2maxlen[key]
            break

    output_max_len = dataset2maxlen[dataset]

    # Load dataset
    data_file = os.path.join(data_dir, f"{dataset}.jsonl")
    if not os.path.exists(data_file):
        print(f"  [WARNING] Data file not found: {data_file}, skipping dataset '{dataset}'")
        return None, None, None

    test_data = []
    with open(data_file) as fp:
        for line in fp:
            example = json.loads(line)
            template = model2prompt.get(dataset, "{context}\n{input}")
            prompt = template.format(**example)
            if "llama2" in model_path_lower:
                prompt = build_chat(prompt)
            example["prompt"] = prompt
            test_data.append(example)

    # Set per-layer budgets on the model
    set_model_budgets(model, max_capacity_prompts, method=method)

    # Run inference on ALL data
    predictions = []
    answers = []
    all_classes_list = []

    for i in tqdm(range(0, len(test_data), eval_batch_size),
                  desc=f"  {dataset}", leave=False):
        batch = test_data[i:i + eval_batch_size]
        batch_prompts = [ex["prompt"] for ex in batch]

        tokenized_prompts = tokenizer(
            batch_prompts, padding="longest", return_tensors="pt",
            add_special_tokens=True
        ).to(device)
        batch_input_ids = tokenized_prompts.input_ids

        # Truncate if too long
        if len(batch_input_ids[0]) > model_max_len:
            half = int(model_max_len / 2)
            for j, prompt in enumerate(batch_prompts):
                truncated = tokenizer.decode(
                    batch_input_ids[j][:half], skip_special_tokens=True
                ) + tokenizer.decode(
                    batch_input_ids[j][-half:], skip_special_tokens=True
                )
                batch_prompts[j] = truncated
            tokenized_prompts = tokenizer(
                batch_prompts, padding="longest", return_tensors="pt",
                add_special_tokens=True
            ).to(device)
            batch_input_ids = tokenized_prompts.input_ids

        context_length = batch_input_ids.shape[-1]

        with torch.no_grad():
            output = model.generate(
                **tokenized_prompts,
                max_new_tokens=output_max_len,
                num_beams=1,
                do_sample=False,
                temperature=1.0,
                min_length=context_length + 1,
                eos_token_id=[tokenizer.eos_token_id]
            )

        for j in range(len(batch)):
            pred = tokenizer.decode(
                output[j][context_length:], skip_special_tokens=True
            )
            predictions.append(pred)
            answers.append(batch[j]["answers"])
            all_classes_list.append(batch[j].get("all_classes", ""))

        torch.cuda.empty_cache()

    return predictions, answers, all_classes_list


# ═══════════════════════════════════════════════════════════════════════════════
#  Single-config evaluation (used by both single-GPU and multi-GPU paths)
# ═══════════════════════════════════════════════════════════════════════════════

def evaluate_single_config(model, tokenizer, cfg_idx, cfg, num_layers,
                           datasets, data_dir, model_path, method,
                           eval_batch_size, results_dir, save_predictions,
                           device="cuda"):
    """Evaluate a single config on all datasets. Returns a result dict."""
    x_point = np.array(cfg[:-2])
    budgets = x_point_to_budgets(x_point, num_layers)
    avg_budget = cfg[-2]
    evicted_attn = cfg[-1]

    print(f"\n[GPU {device}] Config {cfg_idx}: "
          f"avg_budget={avg_budget:.1f}, evicted_attn={evicted_attn:.6f}")
    print(f"[GPU {device}] Per-layer budgets: {budgets}")

    config_start_time = time.time()

    config_results = {
        "config_idx": cfg_idx,
        "avg_budget": avg_budget,
        "evicted_attn": evicted_attn,
        "budgets": budgets,
        "dataset_scores": {},
        "avg_score": 0.0,
    }

    dataset_scores = []
    for dataset in datasets:
        print(f"[GPU {device}]   Evaluating: {dataset}")
        preds, answers, all_classes = evaluate_dataset(
            model=model,
            tokenizer=tokenizer,
            dataset=dataset,
            data_dir=data_dir,
            model_path=model_path,
            max_capacity_prompts=budgets,
            method=method,
            eval_batch_size=eval_batch_size,
            device=device,
        )

        if preds is None:
            continue

        score = scorer(dataset, preds, answers, all_classes)
        config_results["dataset_scores"][dataset] = score
        dataset_scores.append(score)
        print(f"[GPU {device}]   {dataset}: {score:.2f}")

        if save_predictions:
            pred_dir = os.path.join(results_dir, f"config_{cfg_idx}")
            os.makedirs(pred_dir, exist_ok=True)
            pred_file = os.path.join(pred_dir, f"{dataset}_predictions.jsonl")
            with open(pred_file, 'w') as f:
                for pred, ans, cls in zip(preds, answers, all_classes):
                    f.write(json.dumps({
                        "pred": pred, "answers": ans, "all_classes": cls
                    }) + "\n")

    if dataset_scores:
        config_results["avg_score"] = np.mean(dataset_scores)

    config_elapsed = time.time() - config_start_time
    config_results["eval_time_sec"] = config_elapsed

    print(f"[GPU {device}] Config {cfg_idx} done: avg_score={config_results['avg_score']:.2f}, "
          f"time={config_elapsed:.1f}s")

    return config_results


# ═══════════════════════════════════════════════════════════════════════════════
#  Multi-GPU worker process
# ═══════════════════════════════════════════════════════════════════════════════

def gpu_worker(gpu_id, config_queue, result_queue, shared_args):
    """
    Worker process that runs on a single GPU.
    Loads model once, then evaluates configs from the queue one by one.
    """
    device = f"cuda:{gpu_id}"
    model_path = shared_args["model_path"]
    method = shared_args["method"]
    attn_implementation = shared_args["attn_implementation"]
    num_layers = shared_args["num_layers"]
    datasets = shared_args["datasets"]
    data_dir = shared_args["data_dir"]
    eval_batch_size = shared_args["eval_batch_size"]
    results_dir = shared_args["results_dir"]
    save_predictions = shared_args["save_predictions"]

    # ─── Load model on this GPU ────────────────────────────────────────────────
    print(f"[GPU {device}] Loading model...")

    from pyramidkv.monkeypatch import replace_llama, replace_mistral
    replace_llama(method.lower())
    replace_mistral(method.lower())

    tokenizer = AutoTokenizer.from_pretrained(
        model_path, use_fast=True, padding_side="left"
    )
    tokenizer.padding_side = "left"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id

    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
        device_map=device,
        use_cache=True,
        attn_implementation=attn_implementation,
    )
    model.eval()
    print(f"[GPU {device}] Model loaded successfully.")

    # ─── Process configs from queue ────────────────────────────────────────────
    while True:
        try:
            item = config_queue.get(timeout=5)
        except Exception:
            # Check if we're done
            if config_queue.empty():
                break
            continue

        if item is None:  # Sentinel value — shutdown
            break

        cfg_idx, cfg = item
        try:
            result = evaluate_single_config(
                model=model,
                tokenizer=tokenizer,
                cfg_idx=cfg_idx,
                cfg=cfg,
                num_layers=num_layers,
                datasets=datasets,
                data_dir=data_dir,
                model_path=model_path,
                method=method,
                eval_batch_size=eval_batch_size,
                results_dir=results_dir,
                save_predictions=save_predictions,
                device=device,
            )
            result_queue.put(result)
        except Exception as e:
            print(f"[GPU {device}] ERROR evaluating config {cfg_idx}: {e}")
            import traceback
            traceback.print_exc()
            result_queue.put({
                "config_idx": cfg_idx,
                "avg_budget": cfg[-2],
                "evicted_attn": cfg[-1],
                "budgets": [],
                "dataset_scores": {},
                "avg_score": 0.0,
                "eval_time_sec": 0.0,
                "error": str(e),
            })

    # Cleanup
    del model
    torch.cuda.empty_cache()
    print(f"[GPU {device}] Worker finished.")


# ═══════════════════════════════════════════════════════════════════════════════
#  Multi-GPU evaluation orchestrator
# ═══════════════════════════════════════════════════════════════════════════════

def run_multi_gpu(selected_configs, num_gpus, shared_args):
    """
    Distribute configs across GPUs and run in parallel.
    Each GPU gets its own process with its own model copy.
    """
    # Use spawn method to avoid CUDA re-initialization issues
    mp.set_start_method('spawn', force=True)

    # Create queues
    config_queue = mp.Queue()
    result_queue = mp.Queue()

    # Fill config queue
    for cfg_idx, cfg in enumerate(selected_configs):
        config_queue.put((cfg_idx, cfg))

    # Add sentinel values for each worker
    for _ in range(num_gpus):
        config_queue.put(None)

    # Determine which GPUs to use
    cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    if cuda_visible:
        gpu_ids = list(range(len(cuda_visible.split(","))))
    else:
        gpu_ids = list(range(num_gpus))

    print(f"\nStarting multi-GPU evaluation with {len(gpu_ids)} GPUs: {gpu_ids}")
    print(f"Total configs to evaluate: {len(selected_configs)}")

    # Spawn workers
    workers = []
    for gpu_id in gpu_ids:
        p = mp.Process(
            target=gpu_worker,
            args=(gpu_id, config_queue, result_queue, shared_args),
        )
        p.start()
        workers.append(p)

    # Collect results
    all_results = []
    expected = len(selected_configs)
    with tqdm(total=expected, desc="Configs evaluated") as pbar:
        while len(all_results) < expected:
            try:
                result = result_queue.get(timeout=10)
                all_results.append(result)
                pbar.update(1)
            except Exception:
                # Check if any worker died
                if any(not p.is_alive() for p in workers):
                    print("WARNING: A worker process died unexpectedly!")
                    break

    # Wait for all workers to finish
    for p in workers:
        p.join(timeout=30)

    # Sort results by config_idx
    all_results.sort(key=lambda x: x["config_idx"] if isinstance(x["config_idx"], int) else -1)

    return all_results


# ═══════════════════════════════════════════════════════════════════════════════
#  Single-GPU evaluation (original path)
# ═══════════════════════════════════════════════════════════════════════════════

def run_single_gpu(selected_configs, args, model, tokenizer, num_layers, datasets, results_dir):
    """Original sequential evaluation on a single GPU."""
    all_results = []

    for cfg_idx, cfg in enumerate(selected_configs):
        result = evaluate_single_config(
            model=model,
            tokenizer=tokenizer,
            cfg_idx=cfg_idx,
            cfg=cfg,
            num_layers=num_layers,
            datasets=datasets,
            data_dir=args.data_dir,
            model_path=args.model_path,
            method=args.method,
            eval_batch_size=args.eval_batch_size,
            results_dir=results_dir,
            save_predictions=args.save_predictions,
            device="cuda",
        )
        all_results.append(result)

    return all_results


# ═══════════════════════════════════════════════════════════════════════════════
#  Save and print results
# ═══════════════════════════════════════════════════════════════════════════════

def load_existing_results(results_dir):
    """Load the most recent existing results from eval_results directory.
    Returns a list of result dicts, or empty list if none found.
    """
    if not os.path.isdir(results_dir):
        return []

    # Find all summary JSON files, sorted by timestamp (newest last)
    json_files = sorted(
        [f for f in os.listdir(results_dir) if f.startswith("summary_") and f.endswith(".json")],
    )

    if not json_files:
        return []

    # Load the most recent one
    latest = os.path.join(results_dir, json_files[-1])
    try:
        with open(latest, 'r') as f:
            results = json.load(f)
        print(f"Loaded {len(results)} existing results from {latest}")
        return results
    except Exception as e:
        print(f"Warning: Could not load existing results from {latest}: {e}")
        return []


def config_identity(cfg):
    """Return a hashable identity for a config (avg_budget, evicted_attn).
    This is used to match configs across runs.
    """
    return (round(cfg[-2], 4), round(cfg[-1], 6))


def filter_completed_configs(selected_configs, existing_results):
    """Filter out configs that have already been evaluated.
    Returns (pending_configs, completed_results).
    """
    if not existing_results:
        return selected_configs, []

    # Build set of already-evaluated config identities
    completed_ids = set()
    completed_results = []
    for res in existing_results:
        if isinstance(res.get("config_idx"), int):
            cfg_id = (round(res["avg_budget"], 4), round(res.get("evicted_attn", 0) or 0, 6))
            completed_ids.add(cfg_id)
            completed_results.append(res)

    # Filter pending configs
    pending = []
    for cfg in selected_configs:
        cid = config_identity(cfg)
        if cid not in completed_ids:
            pending.append(cfg)
        else:
            print(f"  Skipping already-evaluated config: avg_budget={cfg[-2]:.1f}, evicted_attn={cfg[-1]:.6f}")

    print(f"Already completed: {len(selected_configs) - len(pending)} configs")
    print(f"Remaining to evaluate: {len(pending)} configs")

    return pending, completed_results


def save_results(all_results, task_name, datasets, results_dir):
    """Save results to JSON and CSV, and print final comparison table."""

    # ─── Save summary results ─────────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = os.path.join(results_dir, f"summary_{timestamp}.json")
    with open(summary_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSummary saved to: {summary_file}")

    # ─── Print final comparison table ─────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"FINAL RESULTS — {task_name}")
    print(f"{'='*70}")
    print(f"{'Config':<10} {'Avg Budget':>12} {'Evicted Attn':>14} {'Avg Score':>12} {'Datasets':>30}")
    print(f"{'-'*10} {'-'*12} {'-'*14} {'-'*12} {'-'*30}")

    for res in all_results:
        idx_str = str(res["config_idx"])
        ds_scores_str = ", ".join(
            f"{k[:8]}:{v:.1f}" for k, v in res["dataset_scores"].items()
        )
        evicted_str = f"{res['evicted_attn']:.6f}" if res['evicted_attn'] is not None else "N/A"
        print(f"{idx_str:<10} {res['avg_budget']:>12.1f} {evicted_str:>14} "
              f"{res['avg_score']:>12.2f} {ds_scores_str:>30}")

    # ─── Also save as CSV for easy analysis ────────────────────────────────────
    csv_file = os.path.join(results_dir, f"summary_{timestamp}.csv")
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        # Header
        header = ['config_idx', 'avg_budget', 'evicted_attn', 'avg_score']
        header += [f"{ds}_score" for ds in datasets]
        header += ['budgets', 'eval_time_sec']
        writer.writerow(header)
        # Rows
        for res in all_results:
            row = [
                res['config_idx'],
                res['avg_budget'],
                res['evicted_attn'] if res['evicted_attn'] is not None else '',
                res['avg_score'],
            ]
            for ds in datasets:
                row.append(res['dataset_scores'].get(ds, ''))
            row.append(str(res['budgets']))
            row.append(res.get('eval_time_sec', ''))
            writer.writerow(row)

    print(f"CSV saved to: {csv_file}")
    print(f"\nDone!")


# ═══════════════════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate top NAS configs on the FULL dataset (multi-GPU supported)"
    )
    parser.add_argument("task_name", type=str,
                        help="Task category (e.g., SUMMARIZATION, SINGLE_DOCUMENT_QA)")
    parser.add_argument("--top-n", type=int, default=None,
                        help="Number of configs to evaluate (evenly spaced from Pareto front). Default: all rank-1 configs")
    parser.add_argument("--config-indices", type=int, nargs='+', default=None,
                        help="Specific rank-1 config indices to evaluate (0-based)")
    parser.add_argument("--model-path", type=str,
                        default=os.environ.get(
                            "NAS_MODEL_PATH",
                            "/home/snap_nas/sravanth/LLM/Token_Eviction/models/Llama-2-7b-chat-hf"
                        ),
                        help="Model path")
    parser.add_argument("--method", type=str,
                        default=os.environ.get("NAS_METHOD", "snapkv"),
                        help="KV eviction method")
    parser.add_argument("--attn-implementation", type=str,
                        default=os.environ.get("NAS_ATTN_IMPL", "flash_attention_2"),
                        help="Attention implementation")
    parser.add_argument("--data-dir", type=str,
                        default=os.environ.get(
                            "NAS_DATA_DIR",
                            "/home/snap_nas/sravanth/LLM/Token_Eviction/Dynamic_Methods/PyramidKV/data/LongBench"
                        ),
                        help="Data directory for LongBench datasets")
    parser.add_argument("--eval-batch-size", type=int, default=1,
                        help="Batch size for evaluation")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--save-predictions", action="store_true",
                        help="Save per-example predictions for each config")
    parser.add_argument("--baseline-budget", type=int, default=None,
                        help="Also evaluate a uniform baseline with this budget (e.g., 256)")
    parser.add_argument("--num-gpus", type=int, default=1,
                        help="Number of GPUs to use for parallel config evaluation. "
                             "Each GPU loads its own model copy and evaluates different configs.")

    args = parser.parse_args()

    # ─── Setup ──────────────────────────────────────────────────────────────────
    set_seed(args.seed)

    clustering = load_data_clustering()
    if args.task_name not in clustering:
        print(f"Error: Task '{args.task_name}' not in data_clustering.json")
        print(f"Available: {[k for k in clustering if k not in ['TOTAL_DATASETS', 'DATASET2METRIC']]}")
        sys.exit(1)

    datasets = clustering[args.task_name]
    print(f"\nTask: {args.task_name}")
    print(f"Datasets: {datasets}")
    print(f"Model: {args.model_path}")
    print(f"Method: {args.method}")
    print(f"Num GPUs: {args.num_gpus}")
    print(f"Config Indices: {args.config_indices}")

    # ─── Get rank-1 configs ────────────────────────────────────────────────────
    rank1_configs = get_rank1_configs(args.task_name)
    selected_configs = select_configs(rank1_configs, args.top_n, args.config_indices)

    print(f"\nWill evaluate {len(selected_configs)} configurations:")
    for i, cfg in enumerate(selected_configs):
        budgets = x_point_to_budgets(cfg[:-2], 32)  # 32 layers for Llama-2-7B
        print(f"  Config {i}: avg_budget={cfg[-2]:.1f}, evicted_attn={cfg[-1]:.6f}, "
              f"budgets={budgets}")

    # ─── Create output directory ───────────────────────────────────────────────
    results_dir = os.path.join(args.task_name, "top_configs")
    os.makedirs(results_dir, exist_ok=True)

    # ─── Determine num_layers (always needed) ──────────────────────────────────
    from transformers import AutoConfig
    config = AutoConfig.from_pretrained(args.model_path)
    num_layers = config.num_hidden_layers
    print(f"Model has {num_layers} layers")

    # ─── Load existing results and filter already-completed configs ────────────
    existing_results = load_existing_results(results_dir)
    pending_configs, completed_results = filter_completed_configs(selected_configs, existing_results)

    if not pending_configs:
        print("\nAll configs already evaluated! No new evaluation needed.")
        all_results = completed_results
    else:

        # ─── Evaluate pending configs ─────────────────────────────────────────
        if args.num_gpus > 1:
            # ─── Multi-GPU path ───────────────────────────────────────────────
            shared_args = {
                "model_path": args.model_path,
                "method": args.method,
                "attn_implementation": args.attn_implementation,
                "num_layers": num_layers,
                "datasets": datasets,
                "data_dir": args.data_dir,
                "eval_batch_size": args.eval_batch_size,
                "results_dir": results_dir,
                "save_predictions": args.save_predictions,
            }

            new_results = run_multi_gpu(pending_configs, args.num_gpus, shared_args)

        else:
            # ─── Single-GPU path (original) ───────────────────────────────────
            print(f"\nLoading model: {args.model_path}")

            from pyramidkv.monkeypatch import replace_llama, replace_mistral
            replace_llama(args.method.lower())
            replace_mistral(args.method.lower())

            tokenizer = AutoTokenizer.from_pretrained(
                args.model_path, use_fast=True, padding_side="left"
            )
            tokenizer.padding_side = "left"
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
                tokenizer.pad_token_id = tokenizer.eos_token_id

            model = AutoModelForCausalLM.from_pretrained(
                args.model_path,
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True,
                device_map="auto",
                use_cache=True,
                attn_implementation=args.attn_implementation,
            )
            model.eval()
            print(f"Model loaded: {num_layers} layers")

            new_results = run_single_gpu(
                pending_configs, args, model, tokenizer, num_layers, datasets, results_dir
            )

        # ─── Merge new + existing results ─────────────────────────────────────
        all_results = completed_results + new_results
        # Sort by config_idx (integers first, then strings like "baseline")
        all_results.sort(key=lambda x: x["config_idx"] if isinstance(x["config_idx"], int) else 9999)

    # ─── Optional: evaluate uniform baseline ───────────────────────────────────
    if args.baseline_budget is not None:
        uniform_budgets = [args.baseline_budget] * num_layers
        print(f"\n{'='*70}")
        print(f"BASELINE: Uniform budget = {args.baseline_budget} for all layers")
        print(f"{'='*70}")

        # For baseline, we need a model — load it if not already loaded
        if args.num_gpus > 1:
            # Load a fresh model for baseline on GPU 0
            from pyramidkv.monkeypatch import replace_llama, replace_mistral
            replace_llama(args.method.lower())
            replace_mistral(args.method.lower())

            tokenizer = AutoTokenizer.from_pretrained(
                args.model_path, use_fast=True, padding_side="left"
            )
            tokenizer.padding_side = "left"
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
                tokenizer.pad_token_id = tokenizer.eos_token_id

            model = AutoModelForCausalLM.from_pretrained(
                args.model_path,
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True,
                device_map="cuda:0",
                use_cache=True,
                attn_implementation=args.attn_implementation,
            )
            model.eval()

        baseline_results = {
            "config_idx": "baseline",
            "avg_budget": float(args.baseline_budget),
            "evicted_attn": None,
            "budgets": uniform_budgets,
            "dataset_scores": {},
            "avg_score": 0.0,
        }

        dataset_scores = []
        for dataset in datasets:
            print(f"\n  Evaluating dataset: {dataset}")
            preds, answers, all_classes = evaluate_dataset(
                model=model,
                tokenizer=tokenizer,
                dataset=dataset,
                data_dir=args.data_dir,
                model_path=args.model_path,
                max_capacity_prompts=uniform_budgets,
                method=args.method,
                eval_batch_size=args.eval_batch_size,
            )

            if preds is None:
                continue

            score = scorer(dataset, preds, answers, all_classes)
            baseline_results["dataset_scores"][dataset] = score
            dataset_scores.append(score)
            print(f"  {dataset}: {score:.2f}")

        if dataset_scores:
            baseline_results["avg_score"] = np.mean(dataset_scores)

        all_results.append(baseline_results)

    # ─── Save and print results ────────────────────────────────────────────────
    save_results(all_results, args.task_name, datasets, results_dir)


if __name__ == "__main__":
    main()
