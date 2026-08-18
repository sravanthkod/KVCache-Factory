import os
import sys
import json
import random
import argparse
import glob
import subprocess
import datetime as _datetime

import numpy as np
from tqdm import tqdm

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer
from pyramidkv.quantization import build_quantized_cache_config, patch_quantized_cache
from pyramidkv.eval_utils import str2bool, build_stop_token_ids

# ─── Dataset / metric / prompt configs ───────────────────────────────────────

dataset2maxlen = {
    "narrativeqa": 128,
    "qasper": 128,
    "multifieldqa_en": 64,
    "multifieldqa_zh": 64,
    "hotpotqa": 32,
    "2wikimqa": 32,
    "musique": 32,
    "dureader": 128,
    "gov_report": 512,
    "qmsum": 512,
    "multi_news": 512,
    "vcsum": 512,
    "trec": 64,
    "triviaqa": 32,
    "samsum": 128,
    "lsht": 64,
    "passage_count": 32,
    "passage_retrieval_en": 32,
    "passage_retrieval_zh": 32,
    "lcc": 64,
    "repobench-p": 64
}

model2prompt = {
    "narrativeqa": "You are given a story, which can be either a novel or a movie script, and a question. Answer the question asconcisely as you can, using a single phrase if possible. Do not provide any explanation.\n\nStory: {context}\n\nNow, answer the question based on the story asconcisely as you can, using a single phrase if possible. Do not provide any explanation.\n\nQuestion: {input}\n\nAnswer:",
    "qasper": "You are given a scientific article and a question. Answer the question as concisely as you can, using a single phrase or sentence if possible. If the question cannot be answered based on the information in the article, write \"unanswerable\". If the question is a yes/no question, answer \"yes\", \"no\", or \"unanswerable\". Do not provide any explanation.\n\nArticle: {context}\n\n Answer the question based on the above article as concisely as you can, using a single phrase or sentence if possible. If the question cannot be answered based on the information in the article, write \"unanswerable\". If the question is a yes/no question, answer \"yes\", \"no\", or \"unanswerable\". Do not provide any explanation.\n\nQuestion: {input}\n\nAnswer:",
    "multifieldqa_en": "Read the following text and answer briefly.\n\n{context}\n\nNow, answer the following question based on the above text, only give me the answer and do not output any other words.\n\nQuestion: {input}\nAnswer:",
    "multifieldqa_zh": "阅读以下文字并用中文简短回答：\n\n{context}\n\n现在请基于上面的文章回答下面的问题，只告诉我答案，不要输出任何其他字词。\n\n问题：{input}\n回答：",
    "hotpotqa": "Answer the question based on the given passages. Only give me the answer and do not output any other words.\n\nThe following are given passages.\n{context}\n\nAnswer the question based on the given passages. Only give me the answer and do not output any other words.\n\nQuestion: {input}\nAnswer:",
    "2wikimqa": "Answer the question based on the given passages. Only give me the answer and do not output any other words.\n\nThe following are given passages.\n{context}\n\nAnswer the question based on the given passages. Only give me the answer and do not output any other words.\n\nQuestion: {input}\nAnswer:",
    "musique": "Answer the question based on the given passages. Only give me the answer and do not output any other words.\n\nThe following are given passages.\n{context}\n\nAnswer the question based on the given passages. Only give me the answer and do not output any other words.\n\nQuestion: {input}\nAnswer:",
    "dureader": "请基于给定的文章回答下述问题。\n\n文章：{context}\n\n请基于上述文章回答下面的问题。\n\n问题：{input}\n回答：",
    "gov_report": "You are given a report by a government agency. Write a one-page summary of the report.\n\nReport:\n{context}\n\nNow, write a one-page summary of the report.\n\nSummary:",
    "qmsum": "You are given a meeting transcript and a query containing a question or instruction. Answer the query in one or more sentences.\n\nTranscript:\n{context}\n\nNow, answer the query based on the above meeting transcript in one or more sentences.\n\nQuery: {input}\nAnswer:",
    "multi_news": "You are given several news passages. Write a one-page summary of all news. \n\nNews:\n{context}\n\nNow, write a one-page summary of all the news.\n\nSummary:",
    "vcsum": "下面有一段会议记录，请你阅读后，写一段总结，总结会议的内容。\n会议记录：\n{context}\n\n会议总结：",
    "trec": "Please determine the type of the question below. Here are some examples of questions.\n\n{context}\n{input}",
    "triviaqa": "Answer the question based on the given passage. Only give me the answer and do not output any other words. The following are some examples.\n\n{context}\n\n{input}",
    "samsum": "Summarize the dialogue into a few short sentences. The following are some examples.\n\n{context}\n\n{input}",
    "lsht": "请判断给定新闻的类别，下面是一些例子。\n\n{context}\n{input}",
    "passage_count": "There are some paragraphs below sourced from Wikipedia. Some of them may be duplicates. Please carefully read these paragraphs and determine how many unique paragraphs there are after removing duplicates. In other words, how many non-repeating paragraphs are there in total?\n\n{context}\n\nPlease enter the final count of unique paragraphs after removing duplicates. The output format should only contain the number, such as 1, 2, 3, and so on.\n\nThe final answer is: ",
    "passage_retrieval_en": "Here are 30 paragraphs from Wikipedia, along with an abstract. Please determine which paragraph the abstract is from.\n\n{context}\n\nThe following is an abstract.\n\n{input}\n\nPlease enter the number of the paragraph that the abstract is from. The answer format must be like \"Paragraph 1\", \"Paragraph 2\", etc.\n\nThe answer is: ",
    "passage_retrieval_zh": "以下是若干段落文字，以及其中一个段落的摘要。请确定给定的摘要出自哪一段。\n\n{context}\n\n下面是一个摘要\n\n{input}\n\n请输入摘要所属段落的编号。答案格式必须是\"段落1\"，\"段落2\"等格式\n\n答案是：",
    "lcc": "Please complete the code given below. \n{context}Next line of code:\n",
    "repobench-p": "Please complete the code given below. \n{context}{input}Next line of code:\n"
}

model2maxlen = {
    "llama2": 3950,
    "llama-2": 3950,
    "llama3": 7500,
    "llama-3": 7500,
    "mistral": 31500
    # "mistral": 31500
}

datasets = ["narrativeqa", "qasper", "multifieldqa_en", "hotpotqa", "2wikimqa", "musique", \
            "gov_report", "qmsum", "multi_news", \
             "lcc", "repobench-p"]

# LongBench datasets that must NOT be wrapped with a chat template
# (few-shot / code completion tasks), matching official LongBench pred.py.
datasets_no_chat = ["trec", "triviaqa", "samsum", "lsht", "lcc", "repobench-p"]

# ─── Metric functions ────────────────────────────────────────────────────────

from metrics import (
    qa_f1_score,
    rouge_zh_score,
    qa_f1_zh_score,
    rouge_score,
    classification_score,
    retrieval_score,
    retrieval_zh_score,
    count_score,
    code_sim_score,
)

dataset2metric_fn = {
    "narrativeqa": qa_f1_score,
    "qasper": qa_f1_score,
    "multifieldqa_en": qa_f1_score,
    "multifieldqa_zh": qa_f1_zh_score,
    "hotpotqa": qa_f1_score,
    "2wikimqa": qa_f1_score,
    "musique": qa_f1_score,
    "dureader": rouge_zh_score,
    "gov_report": rouge_score,
    "qmsum": rouge_score,
    "multi_news": rouge_score,
    "vcsum": rouge_zh_score,
    "trec": classification_score,
    "triviaqa": qa_f1_score,
    "samsum": rouge_score,
    "lsht": classification_score,
    "passage_retrieval_en": retrieval_score,
    "passage_count": count_score,
    "passage_retrieval_zh": retrieval_zh_score,
    "lcc": code_sim_score,
    "repobench-p": code_sim_score,
}


# ─── Helper functions ────────────────────────────────────────────────────────

def set_seed(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.cuda.manual_seed_all(seed)

def build_chat(prompt):
    return f"[INST] {prompt} [/INST]"

def build_chat_llama3(prompt):
        prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        return prompt

def write_run_meta(save_dir, args):
    try:
        git_commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        git_commit = "unknown"
    meta = {
        "git_commit": git_commit,
        "args": vars(args),
        "transformers_version": transformers.__version__,
        "torch_version": torch.__version__,
        "timestamp": _datetime.datetime.now().isoformat(),
    }
    os.makedirs(save_dir, exist_ok=True)
    with open(os.path.join(save_dir, "run_meta.json"), "w") as f:
        json.dump(meta, f, ensure_ascii=False, indent=4, default=str)


# ─── Scorer (from eval.py) ──────────────────────────────────────────────────

def scorer(dataset, predictions, answers, all_classes_list):
    """Compute average score for a dataset given predictions and answers."""
    total_score = 0.0
    for (prediction, ground_truths, all_classes) in zip(predictions, answers, all_classes_list):
        score = 0.0
        if dataset in ["trec", "triviaqa", "samsum", "lsht"]:
            prediction = prediction.lstrip('\n').split('\n')[0]
        for ground_truth in ground_truths:
            score = max(score, dataset2metric_fn[dataset](prediction, ground_truth, all_classes=all_classes))
        total_score += score
    return round(100 * total_score / len(predictions), 2) if len(predictions) > 0 else 0.0


# ─── Load data_clustering.json ───────────────────────────────────────────────

def load_data_clustering(json_path=None):
    """Load dataset clustering info from data_clustering.json."""
    if json_path is None:
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_clustering.json")
    with open(json_path, 'r') as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════════════════════════
#  NAS: Discrete budget options per layer
# ═══════════════════════════════════════════════════════════════════════════════

BUDGET_OPTIONS = [64, 128, 256, 512, 1024]  # 5 discrete budget choices per layer

# Task categories from data_clustering.json
TASK_CATEGORIES = [
    "SINGLE_DOCUMENT_QA",
    "MULTI_DOCUMENT_QA",
    "SUMMARIZATION",
    "FEW_SHOT_LEARNING",
    "SYNTHETIC",
    "CODE",
]


def x_point_to_budgets(X_point, num_layers):
    """
    Convert X_point (D-dim vector in [0,1]) to per-layer budget list
    using discrete budget options.
    
    Each dimension of X_point is mapped to one of BUDGET_OPTIONS:
        [0.0, 0.2) → 64
        [0.2, 0.4) → 128
        [0.4, 0.6) → 256
        [0.6, 0.8) → 512
        [0.8, 1.0] → 1024
    
    D should equal num_layers (one dimension per layer).
    """
    D = len(X_point)
    budgets = []
    for i in range(num_layers):
        dim_idx = i % D  # cycle through X_point dimensions if D < num_layers
        # Map [0,1] to discrete budget index
        budget_idx = int(X_point[dim_idx] * len(BUDGET_OPTIONS))
        budget_idx = min(budget_idx, len(BUDGET_OPTIONS) - 1)  # clamp for edge case x=1.0
        budgets.append(BUDGET_OPTIONS[budget_idx])
    return budgets


# ─── Global model cache ──────────────────────────────────────────────────────

_GLOBAL_MODEL = None
_GLOBAL_TOKENIZER = None
_GLOBAL_MODEL_PATH = None
_GLOBAL_METHOD = None
_GLOBAL_ATTN_IMPL = None


def _ensure_model_loaded(model_path, method, attn_implementation="flash_attention_2"):
    """Load model and tokenizer once (globally cached)."""
    global _GLOBAL_MODEL, _GLOBAL_TOKENIZER, _GLOBAL_MODEL_PATH, _GLOBAL_METHOD, _GLOBAL_ATTN_IMPL

    if _GLOBAL_MODEL is not None and _GLOBAL_MODEL_PATH == model_path and _GLOBAL_METHOD == method:
        return _GLOBAL_MODEL, _GLOBAL_TOKENIZER

    print(f"[get_objective_values] Loading model: {model_path}")
    tokenizer = AutoTokenizer.from_pretrained(
        model_path, use_fast=True, padding_side="left"
    )
    tokenizer.padding_side = "left"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id

    from pyramidkv.monkeypatch import replace_llama, replace_mistral
    replace_llama(method.lower())
    replace_mistral(method.lower())

    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
        device_map="auto",
        use_cache=True,
        attn_implementation=attn_implementation,
    )
    model.eval()

    # Set pad_token_id on generation_config to suppress the repeated warning
    # "Setting pad_token_id to eos_token_id for open-end generation."
    if tokenizer.pad_token_id is not None:
        model.generation_config.pad_token_id = tokenizer.pad_token_id

    _GLOBAL_MODEL = model

    _GLOBAL_TOKENIZER = tokenizer
    _GLOBAL_MODEL_PATH = model_path
    _GLOBAL_METHOD = method
    _GLOBAL_ATTN_IMPL = attn_implementation

    return model, tokenizer


# ─── Set per-layer budgets on the model ──────────────────────────────────────

def set_model_budgets(model, max_capacity_prompts, method="snapkv", window_size=8,
                      kernel_size=7, pooling="maxpool", ratio=0.4, recent_size=32,
                      merge=None, floor=0.2):
    """Set per-layer KV cache budgets on the model.
    
    IMPORTANT: In HuggingFace transformers, all attention layers share the SAME 
    config object. Setting config.max_capacity_prompt per-layer overwrites the same 
    shared attribute, so only the last layer's value persists. To fix this, we:
    1. Store per-layer budgets as instance attributes on each self_attn module
    2. Delete kv_cluster to force recreation with updated values on next forward pass
    The init_* functions in pyramidkv_utils.py read instance attributes first via getattr().
    """
    layers = len(model.model.layers)

    if not isinstance(window_size, list):
        window_sizes = [window_size] * layers
    if not isinstance(max_capacity_prompts, list):
        max_capacity_prompts = [max_capacity_prompts] * layers
    if not isinstance(kernel_size, list):
        kernel_sizes = [kernel_size] * layers
    if not isinstance(ratio, list):
        ratio = [ratio] * layers
    if not isinstance(recent_size, list):
        recent_size = [recent_size] * layers

    for i in range(layers):
        attn_layer = model.model.layers[i].self_attn
        
        # 1. Update the shared config (for backward compatibility)
        attn_layer.config.window_size = window_sizes[i]
        attn_layer.config.max_capacity_prompt = max_capacity_prompts[i]
        attn_layer.config.kernel_size = kernel_sizes[i]
        attn_layer.config.pooling = pooling
        attn_layer.config.merge = merge
        attn_layer.config.floor = floor
        attn_layer.config.ratio = ratio[i]
        attn_layer.config.recent_size = recent_size[i]
        
        # 2. Store per-layer values as instance attributes on the attention module.
        # This is critical because all layers share the same config object,
        # so config.max_capacity_prompt gets overwritten by each iteration.
        # The init_* functions in pyramidkv_utils.py read these via getattr().
        attn_layer.window_size = window_sizes[i]
        attn_layer.max_capacity_prompt = max_capacity_prompts[i]
        attn_layer.kernel_size = kernel_sizes[i]
        attn_layer.pooling = pooling
        attn_layer.merge = merge
        attn_layer.ratio = ratio[i]
        attn_layer.recent_size = recent_size[i]

        # 3. Delete kv_cluster to force recreation on next forward pass.
        # The init_* functions always recreate kv_cluster, so this ensures
        # the new per-layer instance attributes are picked up.
        if hasattr(attn_layer, "kv_cluster"):
            delattr(attn_layer, "kv_cluster")
            
        print(f"Layer {i}: set per-layer max_capacity_prompt = {model.model.layers[i].self_attn.max_capacity_prompt}")

    return max_capacity_prompts



# ─── Compute evicted attention from model's kv_cluster ───────────────────────

def compute_evicted_attention(model, input_ids, max_capacity_prompts):
    """
    Run a forward pass through the model and collect evicted_attn_sum from
    each layer's kv_cluster object.
    
    The eviction algorithms (SnapKV, PyramidKV, H2O, CAM, etc.) now store
    `self.evicted_attn_sum` during their update_kv() call. This is the
    actual attention weight on evicted tokens as computed by the eviction
    algorithm itself — not an approximation.
    
    Returns:
        avg_evicted_attn (float): Average evicted attention across layers.
    """
    # Reset kv_seq_len for each layer (required for proper prefill behavior)
    for layer in model.model.layers:
        if hasattr(layer.self_attn, 'kv_seq_len'):
            layer.self_attn.kv_seq_len = 0
    
    with torch.no_grad():
        outputs = model(input_ids)
    
    # Collect evicted_attn_sum from each layer's kv_cluster
    evicted_attn_list = []
    total_attn_list = []

    for layer_idx, layer in enumerate(model.model.layers):
        if hasattr(layer.self_attn, 'kv_cluster') and hasattr(layer.self_attn.kv_cluster, 'evicted_attn_sum'):
            evicted_attn_list.append(layer.self_attn.kv_cluster.evicted_attn_sum)
            total_attn_list.append(layer.self_attn.kv_cluster.total_attn_sum)
            # print(f"Attention sums for layer: {layer_idx} are Total: {layer.self_attn.kv_cluster.total_attn_sum}; Evicted: {layer.self_attn.kv_cluster.evicted_attn_sum}; Budget: {layer.self_attn.kv_cluster.max_capacity_prompt}")
            # print(f"evicted attention sum for layer: {layer_idx} is {layer.self_attn.kv_cluster.evicted_attn_sum}")

    # print("===============================================================")
    
    if len(evicted_attn_list) == 0:
        return 0.0, 0.0
    
    avg_evicted_attn = np.mean(evicted_attn_list)
    avg_total_attn = np.mean(total_attn_list)
    return avg_evicted_attn, avg_total_attn


# ─── Run calibration on a single dataset ─────────────────────────────────────

def run_dataset_calibration(model, tokenizer, dataset, data_dir, model_path,
                            max_capacity_prompts, sample_ratio=0.1, seed=42,
                            eval_batch_size=1, method="snapkv"):
    """
    Run calibration on a single dataset with 10% random prompt sampling.
    Computes: (1) average budget across layers, (2) sum of attention on evicted tokens.
    
    This is similar to calibration in quantization — we use a small subset of data
    to measure how much attention is on the tokens being evicted.
    
    Returns:
        avg_budget (float): Average budget across layers.
        evicted_attn_sum (float): Sum of attention on evicted tokens (lower = better).
    """
    # Determine model max length
    model_path_lower = model_path.lower()
    model_max_len = 3950  # default
    for key in model2maxlen:
        if key in model_path_lower:
            model_max_len = model2maxlen[key]
            break

    set_model_budgets(model, max_capacity_prompts, method=method)
    # Load dataset
    data_file = os.path.join(data_dir, f"{dataset}.jsonl")
    if not os.path.exists(data_file):
        print(f"[WARNING] Data file not found: {data_file}, skipping dataset '{dataset}'")
        return None, None

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

    # Sample `sample_ratio` of prompts with fixed seed
    rng = random.Random(seed)
    num_samples = max(1, int(len(test_data) * sample_ratio))
    if len(test_data) > num_samples:
        sampled_data = rng.sample(test_data, num_samples)
    else:
        sampled_data = test_data

    # Set per-layer budgets on the model
    

    # print(f"check here is: {getattr(model.model.layers[0].self_attn, 'max_capacity_prompt', model.model.layers[0].self_attn.config.max_capacity_prompt)}")
    # print(f"check here is: {getattr(model.model.layers[1].self_attn, 'max_capacity_prompt', model.model.layers[1].self_attn.config.max_capacity_prompt)}")

    # Compute average budget across layers
    avg_budget = np.mean(max_capacity_prompts)

    # Run calibration: compute evicted attention for each prompt
    evicted_attn_list = []
    total_attn_list = []

    for i in range(0, len(sampled_data), eval_batch_size):
        batch = sampled_data[i:i + eval_batch_size]
        batch_prompts = [ex["prompt"] for ex in batch]

        tokenized_prompts = tokenizer(
            batch_prompts, padding="longest", return_tensors="pt", add_special_tokens=True
        ).to('cuda')
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
                batch_prompts, padding="longest", return_tensors="pt", add_special_tokens=True
            ).to('cuda')
            batch_input_ids = tokenized_prompts.input_ids

        # Compute evicted attention for this prompt
        evicted_attn,total_atn = compute_evicted_attention(model, batch_input_ids, max_capacity_prompts)
        evicted_attn_list.append(evicted_attn)
        total_attn_list.append(total_atn)

        torch.cuda.empty_cache()

    # Average evicted attention across all calibration prompts
    avg_evicted_attn = np.mean(evicted_attn_list) if evicted_attn_list else 0.0
    avg_total_attn = np.mean(total_attn_list)

    print(f"Average Attention for all calibration prompts Total: {avg_total_attn}; Evicted: {avg_evicted_attn}")

    return avg_budget, avg_evicted_attn


# ─── Run calibration with actual task scoring ─────────────────────────────────

def run_dataset_calibration_with_scoring(model, tokenizer, dataset, data_dir, model_path,
                                          max_capacity_prompts, sample_ratio=0.1, seed=42,
                                          eval_batch_size=1, method="snapkv",
                                          quant_method=None, nbits=8,
                                          quant_backend="hqq", quant_device="cuda",
                                          quant_residual_length=None,
                                          q_group_size=64, axis_key=None, axis_value=None):
    """
    Run calibration on a single dataset with generation + task scoring.
    This is slower than evicted attention but directly measures generation quality.
    
    Generation logic mirrors run_longbench.py main() exactly (chat templates,
    stop tokens, quantized cache, headinfer, etc.) so scores are identical.
    
    Returns:
        avg_budget (float): Average budget across layers.
        avg_score (float): Average task score across calibration prompts (higher = better).
    """
    model_path_lower = model_path.lower()
    model_max_len = 3950
    for key in model2maxlen:
        if key in model_path_lower:
            model_max_len = model2maxlen[key]
            break

    output_max_len = dataset2maxlen.get(dataset, 128)

    print("inside run_dataset_calibration_with_scoring")

    # Set per-layer budgets on the model
    set_model_budgets(model, max_capacity_prompts, method=method)

    # print(f"check here is: {getattr(model.model.layers[0].self_attn, 'max_capacity_prompt', model.model.layers[0].self_attn.config.max_capacity_prompt)}")
    # print(f"check here is: {getattr(model.model.layers[1].self_attn, 'max_capacity_prompt', model.model.layers[1].self_attn.config.max_capacity_prompt)}")

    # exit()

    # Build proper stop token IDs (Llama-3 has dual terminators, etc.)
    stop_token_ids = build_stop_token_ids(model, tokenizer)
    if dataset == "samsum":
        # Official LongBench stops samsum generations at the first newline.
        newline_token_id = tokenizer.encode("\n", add_special_tokens=False)[-1]
        if newline_token_id not in stop_token_ids:
            stop_token_ids.append(newline_token_id)

    # Determine chat format: llama2 → [INST], llama3 → <|begin_of_text|> header,
    # few-shot/code datasets → no chat wrapper (matching official LongBench pred.py).
    use_llama3_chat = ("llama-3" in model_path_lower or "llama3" in model_path_lower) \
        and dataset not in datasets_no_chat

    # Build quantized cache config (None when quant_method is None — same as run_longbench.py)
    cache_config = build_quantized_cache_config(
        quant_method,
        nbits=nbits,
        residual_length=quant_residual_length or output_max_len,
        device=quant_device,
        backend=quant_backend,
        q_group_size=q_group_size,
        axis_key=axis_key,
        axis_value=axis_value,
    )


    # Load dataset
    data_file = os.path.join(data_dir, f"{dataset}.jsonl")
    if not os.path.exists(data_file):
        print(f"[WARNING] Data file not found: {data_file}, skipping dataset '{dataset}'")
        return None, None

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

    # Sample `sample_ratio` of prompts with fixed seed
    rng = random.Random(seed)
    num_samples = max(1, int(len(test_data) * sample_ratio))
    if len(test_data) > num_samples:
        sampled_data = rng.sample(test_data, num_samples)
    else:
        sampled_data = test_data



    avg_budget = np.mean(max_capacity_prompts)

    # Run generation + scoring
    predictions = []
    answers = []
    all_classes_list = []

    for i in range(0, len(sampled_data), eval_batch_size):
        batch = sampled_data[i:i + eval_batch_size]
        batch_prompts = [ex["prompt"] for ex in batch]

        tokenized_prompts = tokenizer(
            batch_prompts, padding="longest", return_tensors="pt", add_special_tokens=True
        ).to('cuda')
        batch_input_ids = tokenized_prompts.input_ids

        # Truncate if too long, then apply Llama-3 chat wrapper if needed
        prompt = batch_prompts[0]
        truncated = False
        if len(batch_input_ids[0]) > model_max_len:
            half = int(model_max_len / 2)
            prompt = tokenizer.decode(
                batch_input_ids[0][:half], skip_special_tokens=True
            ) + tokenizer.decode(
                batch_input_ids[0][-half:], skip_special_tokens=True
            )
            truncated = True

        if use_llama3_chat:
            # Wrap the already-middle-truncated prompt, matching official LongBench pred.py.
            # add_special_tokens=False avoids a double BOS on top of <|begin_of_text|>.
            prompt = build_chat_llama3(prompt)
            tokenized_prompts = tokenizer(
                prompt, padding="longest", return_tensors="pt", add_special_tokens=False
            ).to('cuda')
            batch_input_ids = tokenized_prompts.input_ids
        elif truncated:
            tokenized_prompts = tokenizer(
                prompt, padding="longest", return_tensors="pt", add_special_tokens=True
            ).to('cuda')
            batch_input_ids = tokenized_prompts.input_ids

        context_length = batch_input_ids.shape[-1]

        # Build extra generation kwargs (headinfer needs explicit cache, matching run_longbench.py)
        extra_generation_kwargs = {}
        if method.lower() == "headinfer":
            from pyramidkv.headinfer import HeadwiseOffloadedCache
            extra_generation_kwargs["past_key_values"] = HeadwiseOffloadedCache()

        with torch.no_grad():
            if cache_config is None:
                output = model.generate(
                    **tokenized_prompts,
                    max_new_tokens=output_max_len,
                    num_beams=1,
                    do_sample=False,
                    temperature=1.0,
                    min_length=context_length + 1,
                    eos_token_id=stop_token_ids,
                    **extra_generation_kwargs,
                )
            else:
                output = model.generate(
                    **tokenized_prompts,
                    max_new_tokens=output_max_len,
                    num_beams=1,
                    do_sample=False,
                    temperature=1.0,
                    min_length=context_length + 1,
                    eos_token_id=stop_token_ids,
                    cache_implementation="quantized",
                    cache_config=cache_config,
                )

        # eval_batch_size is 1, so only sample 0 exists (matching run_longbench.py)
        pred = tokenizer.batch_decode([output[0][context_length:]], skip_special_tokens=True)[0]
        predictions.append(pred)
        answers.append(batch[0]["answers"])
        all_classes_list.append(batch[0].get("all_classes", ""))


        torch.cuda.empty_cache()

    # Compute task score
    score = scorer(dataset, predictions, answers, all_classes_list)
    print(f"  dataset: {dataset} → avg_budget={avg_budget:.1f}, task_score={score:.2f}")

    return avg_budget, score


# ═══════════════════════════════════════════════════════════════════════════════
#  get_objective_values: Called by HFF_mod.py → LAMP.py NAS optimization
#
#  Input:  X_point — D-dimensional numpy array in [0,1]
#          Each dimension maps to a discrete budget choice per layer.
#          Budget options: [64, 128, 256, 512, 1024]
#
#  Output: (f1, f2) — two objectives to MINIMIZE
#           f1 = average_budget  (avg KV cache budget across layers — minimize memory)
#           f2 = sum of attention on evicted tokens (lower = evicting unimportant tokens)
#
#  Uses task-wise categories from data_clustering.json (e.g., SINGLE_DOCUMENT_QA)
#  instead of TOTAL_DATASETS. Runs calibration on 10% of prompts per dataset.
# ═══════════════════════════════════════════════════════════════════════════════

# ─── NAS Configuration (override via environment variables) ──────────────────

NAS_MODEL_PATH = os.environ.get(
    "NAS_MODEL_PATH",
    "/data/sravanth/models/Meta-Llama-3-8B-Instruct"
)
NAS_METHOD = os.environ.get("NAS_METHOD", "snapkv")
NAS_ATTN_IMPL = os.environ.get("NAS_ATTN_IMPL", "flash_attention_2")
NAS_DATA_DIR = os.environ.get(
    "NAS_DATA_DIR",
    "/home/snap_nas/sravanth/LLM/Token_Eviction/Dynamic_Methods/KVCache-Factory/data/LongBench"
)
NAS_SAMPLE_RATIO = float(os.environ.get("NAS_SAMPLE_RATIO", "0.3"))
NAS_SEED = int(os.environ.get("NAS_SEED", "42"))
# Which task category to use from data_clustering.json
# Options: SINGLE_DOCUMENT_QA, MULTI_DOCUMENT_QA, SUMMARIZATION,
#          FEW_SHOT_LEARNING, SYNTHETIC, CODE
NAS_TASK_CATEGORY = os.environ.get("NAS_TASK_CATEGORY", "SINGLE_DOCUMENT_QA")
# f2 metric: "evicted_attn" (default, fast) or "task_score" (slower but more accurate)
# NAS_F2_METRIC = os.environ.get("NAS_F2_METRIC", "evicted_attn")
NAS_F2_METRIC = os.environ.get("NAS_F2_METRIC", "task_score")


def get_objective_values(X_point):
    """
    Evaluate the two NAS objectives for a given per-layer budget configuration.

    This is a calibration-based approach (similar to quantization calibration):
    - Uses 10% of prompts from each dataset in the selected task category
    - Runs a forward pass to measure attention on evicted tokens
    - Lower evicted attention = we're evicting unimportant tokens (good)

    Args:
        X_point: D-dimensional numpy array with values in [0, 1].
                 Each dimension is discretized to one of BUDGET_OPTIONS = [64, 128, 256, 512, 1024].
                 D = num_layers (one dimension per layer).

    Returns:
        (f1, f2): Tuple of two floats to MINIMIZE.
            f1 = average_budget  (avg KV cache budget across layers — minimize memory)
            f2 = evicted_attention_sum  (sum of attention on evicted tokens — minimize)
    """
    # Load dataset list from data_clustering.json — use task-wise category
    clustering = load_data_clustering()
    task_category = NAS_TASK_CATEGORY
    if task_category not in clustering:
        raise ValueError(
            f"Task category '{task_category}' not found in data_clustering.json. "
            f"Available: {[k for k in clustering if k != 'DATASET2METRIC' and k != 'TOTAL_DATASETS']}"
        )
    datasets = clustering[task_category]
    print(f"[get_objective_values] Task category: {task_category}, datasets: {datasets}")

    # Load model (cached globally after first call)
    model, tokenizer = _ensure_model_loaded(
        NAS_MODEL_PATH, NAS_METHOD, NAS_ATTN_IMPL
    )

    # Convert X_point to per-layer budgets (discrete)
    num_layers = len(model.model.layers)
    max_capacity_prompts = x_point_to_budgets(X_point, num_layers)

    print(f"[get_objective_values] X_point (first 5): {X_point[:5]}")
    print(f"[get_objective_values] Per-layer budgets: {max_capacity_prompts}")
    print(f"[get_objective_values] Avg budget: {np.mean(max_capacity_prompts):.1f}")

    # Run calibration on each dataset in the task category
    all_avg_budgets = []
    all_f2_values = []

    use_task_score = (NAS_F2_METRIC == "task_score")

    for idx, dataset in enumerate(datasets):
        print(f"[get_objective_values] Dataset {idx+1}/{len(datasets)}: {dataset}")

        if use_task_score:
            avg_budget, score = run_dataset_calibration_with_scoring(
                model=model,
                tokenizer=tokenizer,
                dataset=dataset,
                data_dir=NAS_DATA_DIR,
                model_path=NAS_MODEL_PATH,
                max_capacity_prompts=max_capacity_prompts,
                sample_ratio=NAS_SAMPLE_RATIO,
                seed=NAS_SEED,
                eval_batch_size=1,
                method=NAS_METHOD,
            )
            if avg_budget is not None:
                all_avg_budgets.append(avg_budget)
                all_f2_values.append(score)
                print(f"  dataset: {dataset} → avg_budget={avg_budget:.1f}, task_score={score:.2f}")
            else:
                print(f"  → SKIPPED (data not found)")
        else:
            avg_budget, evicted_attn = run_dataset_calibration(
                model=model,
                tokenizer=tokenizer,
                dataset=dataset,
                data_dir=NAS_DATA_DIR,
                model_path=NAS_MODEL_PATH,
                max_capacity_prompts=max_capacity_prompts,
                sample_ratio=NAS_SAMPLE_RATIO,
                seed=NAS_SEED,
                eval_batch_size=1,
                method=NAS_METHOD,
            )
            if avg_budget is not None:
                all_avg_budgets.append(avg_budget)
                all_f2_values.append(evicted_attn)
                print(f"  dataset: {dataset} → avg_budget={avg_budget:.1f}, evicted_attn={evicted_attn:.6f}")
            else:
                print(f"  → SKIPPED (data not found)")

    # Compute final objectives
    if len(all_avg_budgets) == 0:
        avg_budget = float(max(BUDGET_OPTIONS))
        f2_value = 1.0  # worst case
    else:
        avg_budget = np.mean(all_avg_budgets)
        f2_value = np.mean(all_f2_values)

    # Objectives to MINIMIZE:
    #   f1 = avg_budget         (minimize memory usage)
    #   f2 depends on NAS_F2_METRIC:
    #     "evicted_attn" → f2 = evicted_attn_sum (minimize attention on evicted tokens)
    #     "task_score"   → f2 = -1 * avg_score   (minimize negative score = maximize score)
    f1 = avg_budget
    if use_task_score:
        f2 = -1.0 * f2_value  # minimize negative score = maximize score
    else:
        f2 = f2_value  # minimize evicted attention

    metric_name = "task_score" if use_task_score else "evicted_attn"
    print(f"[get_objective_values] RESULT: avg_budget={avg_budget:.1f}, {metric_name}={f2_value:.6f}, f1={f1:.1f}, f2={f2:.6f}")

    return f1, f2


# ─── Original main() function (kept for standalone CLI usage) ────────────────

def main(args):

    print("Loading data...")

    test_data = []

    prompts = []
    inputs = []
    contexts = []
    answerss = []
    lengths = []
    datasets_list = []
    languages = []
    all_classess = []
    _ids = []

    input_max_len = 0

    model_path = args.model_path.lower()

    for key in model2maxlen:
        if key in model_path:
            model_max_len = model2maxlen[key]

    output_max_len = dataset2maxlen[args.dataset]

    with open(args.data_file) as fp:
        for line in fp:
            example = json.loads(line)

            length = example["length"]
            if length > input_max_len: input_max_len = length

            template = model2prompt[args.dataset]
            prompt = template.format(**example)

            if "llama2" in args.model_path.lower():
                prompt = build_chat(prompt)

            example["prompt"] = prompt

            test_data.append(example)

    print(f"Max Length is {input_max_len}")

    if args.max_num_examples and len(test_data) > args.max_num_examples:
        if args.sample_method == "random":
            test_data = random.sample(test_data, args.max_num_examples)
        elif args.sample_method == "topk":
            test_data = test_data[:args.max_num_examples]

    for example in test_data:
        prompts.append(example["prompt"])
        inputs.append(example["input"])
        contexts.append(example["context"])
        answerss.append(example["answers"])
        lengths.append(example["length"])
        datasets_list.append(example["dataset"])
        languages.append(example["language"])
        all_classess.append(example["all_classes"])
        _ids.append(example["_id"])

    print("Finish loading model and tokenizer")

    model_name = model_path.split("/")[-1]

    os.makedirs(os.path.join(args.save_dir, f"{model_name}_{args.max_capacity_prompts}", args.dataset), exist_ok=True)

    file_path = os.path.join(args.save_dir, f"{model_name}_{args.max_capacity_prompts}", args.dataset, f"{args.method}.json")

    start = 0

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        if len(prompts) == len(lines):
            print(f"Skipping {args.dataset}, already completely inferred.")
            return
        else:
            if (len(lines)):
                print(f"{args.dataset} is half cooked {len(lines)}/{len(prompts)}")
            start = len(lines)

    fout = open(os.path.join(args.save_dir, f"{model_name}_{args.max_capacity_prompts}", args.dataset, f"{args.method}.json"), "a")

    for i in tqdm(range(start, len(prompts), args.eval_batch_size)):

        batch_prompts = prompts[i:i+args.eval_batch_size]
        batch_inputs = inputs[i:i+args.eval_batch_size]
        batch_contexts = contexts[i:i+args.eval_batch_size]
        batch_answerss = answerss[i:i+args.eval_batch_size]
        batch_lengths = lengths[i:i+args.eval_batch_size]

        batch_datasets = datasets_list[i:i+args.eval_batch_size]
        batch_languages = languages[i:i+args.eval_batch_size]
        batch_all_classess = all_classess[i:i+args.eval_batch_size]
        batch__ids = _ids[i:i+args.eval_batch_size]

        use_llama3_chat = ("llama-3" in model_path or "llama3" in model_path) \
            and args.dataset not in datasets_no_chat

        tokenized_prompts = tokenizer(batch_prompts, padding="longest", return_tensors="pt", add_special_tokens=True).to('cuda')
        batch_input_ids = tokenized_prompts.input_ids
        attention_mask = tokenized_prompts.attention_mask

        prompt = batch_prompts[0]
        truncated = False
        if len(batch_input_ids[0]) > model_max_len:
            half = int(model_max_len/2)
            prompt = tokenizer.decode(batch_input_ids[0][:half], skip_special_tokens=True)+tokenizer.decode(batch_input_ids[0][-half:], skip_special_tokens=True)
            truncated = True

        if use_llama3_chat:
            # Wrap the already-middle-truncated prompt, matching official LongBench pred.py.
            # add_special_tokens=False avoids a double BOS on top of <|begin_of_text|>.
            prompt = build_chat_llama3(prompt)
            tokenized_prompts = tokenizer(prompt, padding="longest", return_tensors="pt", add_special_tokens=False).to('cuda')
            batch_input_ids = tokenized_prompts.input_ids
            attention_mask = tokenized_prompts.attention_mask
        elif truncated:
            tokenized_prompts = tokenizer(prompt, padding="longest", return_tensors="pt", add_special_tokens=True).to('cuda')
            batch_input_ids = tokenized_prompts.input_ids
            attention_mask = tokenized_prompts.attention_mask

        if args.max_capacity_prompts != -1:
            max_capacity_prompts = args.max_capacity_prompts
        elif args.max_capacity_prompts_ratio != -1:
            max_capacity_prompts = round(batch_input_ids.shape[1] * args.max_capacity_prompts_ratio)

        # HeadInfer is a lossless offloading method: it has no compression
        # budget/window to configure, so it skips this block entirely.
        if args.method != "FullKV" and args.method.lower() != "headinfer":
            if args.method.lower() in ["snapkv","pyramidkv","h2o","cam", "l2norm", "adakv", "headkv", "think"]:
                window_sizes = 8
            elif args.method.lower() in ["streamingllm"]:
                window_sizes = max_capacity_prompts - 4

            if args.method.lower() =='headkv':
                with open(args.head_path, 'r') as file:
                    head_list = json.loads(file.readline())
                head_score_list = [np.mean(l[1]) for l in head_list.items()]
                head_score_list = torch.tensor(head_score_list / sum(head_score_list))
                total_attention = head_score_list.reshape(model.config.num_hidden_layers, model.config.num_attention_heads)
                total_pool_capacity = (args.max_capacity_prompts // args.head_beta) * model.config.num_hidden_layers * model.config.num_attention_heads
                min_num = (args.max_capacity_prompts - args.max_capacity_prompts // args.head_beta)
                head_capacity = torch.round(total_attention * total_pool_capacity + min_num).int()
                model.model.config.head_capacity = head_capacity

            kernel_sizes = 7
            pooling = "maxpool"
            ratio = args.pruning_ratio
            recent_size = args.recent_size

            layers = len(model.model.layers)
            if not isinstance(window_sizes, list):
                window_sizes = [window_sizes] * layers
            if not isinstance(max_capacity_prompts, list):
                max_capacity_prompts = [max_capacity_prompts] * layers
            if not isinstance(kernel_sizes, list):
                kernel_sizes = [kernel_sizes] * layers
            if not isinstance(ratio, list):
                ratio = [ratio] * layers
            if not isinstance(recent_size, list):
                recent_size = [recent_size] * layers
            for i in range(layers):
                model.model.layers[i].self_attn.config.window_size = window_sizes[i]
                model.model.layers[i].self_attn.config.max_capacity_prompt = max_capacity_prompts[i]
                model.model.layers[i].self_attn.config.kernel_size = kernel_sizes[i]
                model.model.layers[i].self_attn.config.pooling = pooling
                model.model.layers[i].self_attn.config.merge = args.merge
                model.model.layers[i].self_attn.config.floor = args.floor
                model.model.layers[i].self_attn.config.ratio = ratio[i]
                model.model.layers[i].self_attn.config.recent_size = recent_size[i]
                model.model.layers[i].self_attn.config.kv_cache_granularity = args.kv_cache_granularity
                model.model.layers[i].self_attn.config.gqa_score_agg = args.gqa_score_agg

        context_length = batch_input_ids.shape[-1]
        eos_token_ids = list(stop_token_ids)
        if args.dataset == "samsum":
            # Official LongBench stops samsum generations at the first newline.
            newline_token_id = tokenizer.encode("\n", add_special_tokens=False)[-1]
            if newline_token_id not in eos_token_ids:
                eos_token_ids.append(newline_token_id)
        cache_config = build_quantized_cache_config(
            args.quant_method,
            nbits=args.nbits,
            residual_length=args.quant_residual_length or output_max_len,
            device=args.quant_device,
            backend=args.quant_backend,
            q_group_size=args.q_group_size,
            axis_key=args.axis_key,
            axis_value=args.axis_value,
        )
        extra_generation_kwargs = {}
        if args.method.lower() == "headinfer":
            from pyramidkv.headinfer import HeadwiseOffloadedCache
            # Fresh head-wise offloaded cache per sample; HeadInfer needs its
            # cache passed explicitly since generate() defaults to DynamicCache.
            extra_generation_kwargs["past_key_values"] = HeadwiseOffloadedCache()
        if cache_config is None:
            output = model.generate(
                **tokenized_prompts,
                output_attentions = args.output_attentions,
                max_new_tokens=output_max_len,
                num_beams=1,
                do_sample=False,
                temperature=1.0,
                min_length=context_length+1,
                eos_token_id=eos_token_ids,
                **extra_generation_kwargs
            )
        else:
            output = model.generate(
                **tokenized_prompts,
                output_attentions = args.output_attentions,
                max_new_tokens=output_max_len,
                num_beams=1,
                do_sample=False,
                temperature=1.0,
                min_length=context_length+1,
                eos_token_id=eos_token_ids,
                cache_implementation="quantized",
                cache_config=cache_config,
            )

        # eval_batch_size is validated to be 1 at startup, so only sample 0 exists.
        batch_generations = tokenizer.batch_decode([output[0][context_length:]], skip_special_tokens=True)

        torch.cuda.empty_cache()

        example = {}

        example["prompt"] = batch_prompts[0]
        example["input"] = batch_inputs[0]
        example["context"] = batch_contexts[0]
        example["answers"] = batch_answerss[0]
        example["pred"] = batch_generations[0]
        example["length"] = batch_lengths[0]

        example["dataset"] = batch_datasets[0]
        example["language"] = batch_languages[0]
        example["all_classes"] = batch_all_classess[0]
        example["_id"] = batch__ids[0]

        fout.write(json.dumps(example) + "\n")


# if __name__ == "__main__":

#     parser = argparse.ArgumentParser()
    
#     parser.add_argument("--seed", type=int, default=42, help="")
#     parser.add_argument("--base_dir", type=str, default="")
#     parser.add_argument("--dataset", type=str, default="", help="deprecated alias of --datasets, kept for backward compatibility.")
#     parser.add_argument("--datasets", type=str, default="", help="comma-separated LongBench datasets to evaluate; defaults to the full list.")
#     parser.add_argument("--data_file", type=str, default="")
#     parser.add_argument("--save_dir", type=str, default="")

#     parser.add_argument("--model_name", type=str, default=None, help="if specified, we will load the model to generate the predictions.")
#     parser.add_argument("--model_path", type=str, default=None, help="if specified, we will load the model to generate the predictions.")
#     parser.add_argument("--use_fast_tokenizer", type=str2bool, default=True, help="")
#     parser.add_argument("--output_attentions", type=str2bool, default=False, help="")
    
#     parser.add_argument("--max_num_examples", type=int, default=None, help="maximum number of examples to evaluate per task.")
#     parser.add_argument("--sample_method", type=str, default="topk", choices=["random", "topk"], help="how to sample the examples.")
    
#     parser.add_argument("--max_new_tokens", type=int, default=None, help="")
    
#     parser.add_argument("--eval_batch_size", type=int, default=1, help="batch size for evaluation.")
    
#     parser.add_argument("--use_cache", type=str2bool, default=True, help="")
#     parser.add_argument("--attn_implementation", type=str,  default="flash_attention_2", choices=["flash_attention_2", "sdpa", "eager"])
#     parser.add_argument("--dtype", type=str, default="float16", choices=["float16", "bfloat16", "auto"], help="torch dtype used to load the model.")
#     parser.add_argument("--method", type=str,  default=None)
#     parser.add_argument("--kv_cache_granularity", type=str, default="query_head", choices=["query_head", "kv_head"], help="Granularity of the compressed KV cache (see docs/gqa_cache_layout.md).")
#     parser.add_argument("--gqa_score_agg", type=str, default="mean", choices=["mean", "max", "sum"], help="How per-query-head scores are aggregated per KV head when kv_cache_granularity=kv_head.")
#     parser.add_argument("--quant_method",type=str,default=None,choices=["kivi","kvquant"])
#     parser.add_argument("--nbits", type=int, default=8, help="")
#     parser.add_argument("--quant_backend", type=str, default="hqq", choices=["hqq", "quanto"], help="Quantized cache backend.")
#     parser.add_argument("--quant_device", type=str, default="cuda", help="Device used by the quantized cache backend.")
#     parser.add_argument("--quant_residual_length", type=int, default=None, help="Full-precision residual window for quantized cache; defaults to max_new_tokens.")
#     parser.add_argument("--q_group_size", type=int, default=64, help="Quantization group size.")
#     parser.add_argument("--axis_key", type=int, default=None, choices=[0, 1], help="Override key quantization axis.")
#     parser.add_argument("--axis_value", type=int, default=None, choices=[0, 1], help="Override value quantization axis.")
#     parser.add_argument("--max_capacity_prompts", type=int, default=512, help="")
#     parser.add_argument("--max_capacity_prompts_ratio", type=float, default=-1, help="")
#     parser.add_argument("--steps", type=int, default=-1, help="maximum number of examples to evaluate per task.")
#     parser.add_argument("--merge", type=str, default=None, help="kv merge method(look-m)")
#     parser.add_argument('--floor', type=float, default=0.2, help='hyper-parameter used in AdaKV')
#     parser.add_argument('--head_path', type=str, default='./data/heads_score/Meta-Llama-3-8B-Instruct_retrieval_reasoning_heads.json', help='Path to head score (HeadKV)')
#     parser.add_argument('--head_beta', type=float, default=1.01, help='hyper-parameter used on HeadKV')
#     parser.add_argument("--recent_size", type=int, default=32, help="")
#     parser.add_argument("--pruning_ratio", type=float, default=0.4, help="pruning ratio of Key Cache")

#     parser.add_argument(
#         "--use_chat_format", 
#         action="store_true", 
#         help="If given, we will use the chat format for the prompts."
#     )
#     parser.add_argument(
#         "--chat_formatting_function", 
#         type=str, 
#         default="eval.templates.create_prompt_with_tulu_chat_format", 
#         help="The function to use to create the chat format. This function will be dynamically imported. Please see examples in `eval/templates.py`."
#     )
    
#     args = parser.parse_args()

#     if args.eval_batch_size != 1:
#         raise ValueError("eval_batch_size != 1 is not supported yet: truncation and decoding only handle sample 0, so batching silently corrupts predictions - see issue #46.")

#     if args.method is None:
#         raise ValueError("--method is required (e.g. FullKV, SnapKV, PyramidKV, H2O, StreamingLLM, CAM, L2Norm).")

#     if args.method.lower() == "think" and args.attn_implementation != "eager":
#         raise ValueError("method 'think' only patches the eager attention path; with --attn_implementation flash_attention_2/sdpa it silently runs stock HF attention. Use --attn_implementation eager.")

#     if args.method.lower() == "headinfer":
#         if args.attn_implementation != "flash_attention_2":
#             raise ValueError("method 'headinfer' only patches the flash_attention_2 path; with --attn_implementation sdpa/eager it silently runs stock HF attention. Use --attn_implementation flash_attention_2.")
#         if args.quant_method:
#             raise ValueError("method 'headinfer' keeps the full KV cache and streams it between CPU and GPU; it is not compatible with --quant_method.")

#     if args.kv_cache_granularity == "kv_head" and args.method.lower() not in ["snapkv", "pyramidkv", "h2o", "streamingllm", "cam", "l2norm", "adakv", "headkv"]:
#         raise ValueError(f"kv_cache_granularity='kv_head' is not supported for method {args.method!r}; supported methods: snapkv, pyramidkv, h2o, streamingllm, cam, l2norm, adakv, headkv.")

#     datasets_arg = args.datasets or args.dataset
#     if datasets_arg:
#         selected_datasets = [d.strip() for d in datasets_arg.split(",") if d.strip()]
#         invalid_datasets = [d for d in selected_datasets if d not in datasets]
#         if invalid_datasets:
#             raise ValueError(f"Unknown dataset(s) {invalid_datasets}; valid datasets: {datasets}")
#     else:
#         selected_datasets = list(datasets)

#     set_seed(args.seed)
#     patch_quantized_cache(args.quant_method)
#     tokenizer = AutoTokenizer.from_pretrained(
#         args.model_path,
#         use_fast=args.use_fast_tokenizer,
#         padding_side="left"
#     )


#     from pyramidkv.monkeypatch import replace_llama,replace_mistral
#     replace_llama(args.method.lower())
#     replace_mistral(args.method.lower())

#     dtype_map = {"float16": torch.float16, "bfloat16": torch.bfloat16, "auto": "auto"}

#     model = AutoModelForCausalLM.from_pretrained(
#         args.model_path,
#         torch_dtype=dtype_map[args.dtype],
#         low_cpu_mem_usage=True,
#         device_map="auto",
#         use_cache=args.use_cache,
#         attn_implementation=args.attn_implementation
#     )


#     tokenizer.padding_side = "left"
#     if tokenizer.pad_token is None:
#         tokenizer.pad_token = tokenizer.eos_token
#         tokenizer.pad_token_id = tokenizer.eos_token_id



#     model.eval()

#     stop_token_ids = build_stop_token_ids(model, tokenizer)

#     save_dir = args.save_dir


#     max_capacity_prompts = args.max_capacity_prompts

#     model_name = args.model_path.lower().split("/")[-1]
#     write_run_meta(os.path.join(args.save_dir, f"{model_name}_{args.max_capacity_prompts}"), args)

#     for idx, dataset in enumerate(selected_datasets):

#         print(f"Working on max_capacity_prompts {args.max_capacity_prompts} dataset {dataset} - {idx}/{len(selected_datasets)}")

#         args.dataset = dataset

#         args.data_file = f"data/LongBench/{args.dataset}.jsonl"

#         main(args)


# X_point = [0.5]*28
# X_point = [0.1]*5 + [0.3]*10 + [0.5]*8 + [0.7]*9

# get_objective_values(X_point)