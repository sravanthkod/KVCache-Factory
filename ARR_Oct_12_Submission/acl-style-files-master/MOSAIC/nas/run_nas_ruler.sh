#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
#  NAS for Per-Layer KV Cache Budget Optimization — RULER benchmark
#  Same LAMP pipeline as run_nas.sh, but the objective is evaluated on RULER
#  subtasks (data/RULER/<ctx>/<subtask>.jsonl) via run_ruler_lamp.py.
#
#  Pipeline: LAMP.py → HFF_mod.py (NAS_BENCHMARK=ruler) → run_ruler_lamp.py → pyramidkv_utils.py
#
#  Two objectives to MINIMIZE:
#    f1 = average_budget       (avg KV cache budget across 32 layers — minimize memory)
#    f2 = -string_match_all    (negated RULER score — minimize = maximize score)
#
#  D = 32 dimensions (one per layer for Llama-3-8B), budgets [64..4096]
#
#  Launch (from nas/):
#    nohup bash run_nas_ruler.sh > ../logs/NAS_RULER_NIAH_SINGLE_snapkv_$(date +%d_%m_%Y).log 2>&1 &
#  Other groups (see ruler_clustering.json):
#    NAS_TASK_CATEGORY=RULER_NIAH_MULTI  nohup bash run_nas_ruler.sh > ../logs/NAS_RULER_NIAH_MULTI_snapkv_$(date +%d_%m_%Y).log 2>&1 &
#    NAS_TASK_CATEGORY=RULER_AGGREGATION nohup bash run_nas_ruler.sh > ../logs/NAS_RULER_AGGREGATION_snapkv_$(date +%d_%m_%Y).log 2>&1 &
#    NAS_TASK_CATEGORY=RULER_VT          nohup bash run_nas_ruler.sh > ../logs/NAS_RULER_VT_snapkv_$(date +%d_%m_%Y).log 2>&1 &
#
#  Cost (~3.4 s/sample at ctx 4096 on Llama-3-8B, ratio 0.3 → 150/500 samples per subtask):
#    RULER_NIAH_SINGLE (3 tasks) ≈ 25 min/candidate    RULER_NIAH_MULTI (5) ≈ 43 min/candidate
#    RULER_AGGREGATION (2)       ≈ 17 min/candidate    RULER_VT (1)         ≈  9 min/candidate
#  The 64-point init design alone is ≈27 h for NIAH_SINGLE. Kill the run once the
#  Pareto front stabilizes — output.txt is append-only, nothing is lost.
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# GPUs: NAS_GPUS="0,1,2" runs one worker process per GPU (subtasks split
# across workers each candidate — ~3x faster). A single id → sequential.
# Override per launch, e.g. NAS_GPUS=2 bash run_nas_ruler.sh
export NAS_GPUS="${NAS_GPUS:-0,1,2}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-$NAS_GPUS}"

# ─── Configuration (override via environment variables) ──────────────────────

# Python interpreter: set PYTHON_BIN to the env with requirements.txt installed.
# PYTHONNOUSERSITE=1 is REQUIRED — a broken transformers-5.x shadow install in
# ~/.local/lib/python3.10/site-packages otherwise takes precedence and crashes
# (bus error) on import.
PYTHON_BIN="${PYTHON_BIN:-python}"
export PYTHONNOUSERSITE=1

# Benchmark selector consumed by HFF_mod.py
export NAS_BENCHMARK="ruler"

# Model path
export NAS_MODEL_PATH="${NAS_MODEL_PATH:-meta-llama/Meta-Llama-3-8B-Instruct}"

# Eviction method: snapkv, pyramidkv, h2o, cam, streamingllm, l2norm, adakv, headkv
export NAS_METHOD="${NAS_METHOD:-snapkv}"

# Attention implementation: flash_attention_2, sdpa, eager
export NAS_ATTN_IMPL="${NAS_ATTN_IMPL:-flash_attention_2}"

# Data directory for RULER datasets (contains 4096/ 8192/ 16384/ subdirs)
export NAS_DATA_DIR="${NAS_DATA_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/data/RULER}"

# RULER context length: 4096, 8192 or 16384.
# NOTE: llama-3 prompts are middle-truncated to 7500 tokens, so 8192/16384
# destroy the needle — stick to 4096 unless model2maxlen is raised.
export NAS_CONTEXT_LENGTH="${NAS_CONTEXT_LENGTH:-4096}"

# Fraction of data to use per subtask (0.3 = 150 of 500 samples)
export NAS_SAMPLE_RATIO="${NAS_SAMPLE_RATIO:-0.3}"

# Random seed for reproducibility
export NAS_SEED="${NAS_SEED:-42}"

# Task group from ruler_clustering.json
# Options: RULER_NIAH_SINGLE, RULER_NIAH_MULTI, RULER_AGGREGATION, RULER_VT, RULER_ALL
export NAS_TASK_CATEGORY="${NAS_TASK_CATEGORY:-RULER_NIAH_SINGLE}"

# f2 metric: "task_score" (generation + string_match_all) or "evicted_attn" (prefill-only, fast)
export NAS_F2_METRIC="${NAS_F2_METRIC:-task_score}"

# Fixed-budget-slice mode ("Design B"): >0 pins mean budget, continuous decode.
# Unset/0 = original unconstrained grid search. See run_nas_ruler_slices.sh.
export NAS_TARGET_BUDGET="${NAS_TARGET_BUDGET:-0}"

# ─── Print configuration ─────────────────────────────────────────────────────

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  NAS for Per-Layer KV Cache Budgets — RULER                 ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Model:          ${NAS_MODEL_PATH##*/}"
echo "║  Method:         ${NAS_METHOD}"
echo "║  Task Category:  ${NAS_TASK_CATEGORY}"
echo "║  Context Length: ${NAS_CONTEXT_LENGTH}"
echo "║  f2 Metric:      ${NAS_F2_METRIC}"
echo "║  Sample Ratio:   ${NAS_SAMPLE_RATIO}"
echo "║  GPUs:           ${NAS_GPUS}"
echo "║  Target Budget:  ${NAS_TARGET_BUDGET} (0 = unconstrained)"
echo "║  Attn Impl:      ${NAS_ATTN_IMPL}"
echo "║  Data Dir:       ${NAS_DATA_DIR}"
echo "╚══════════════════════════════════════════════════════════════╝"

# ─── Navigate to the nas/ directory ────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "[1/3] Adding PyramidKV to Python path..."
export PYTHONPATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd):${PYTHONPATH:-}"

echo "[2/3] Checking for required files..."
for f in LAMP.py HFF_mod.py run_ruler_lamp.py run_longbench_lamp.py ruler_clustering.json ndsort.py; do
    if [ ! -f "$f" ]; then
        echo "  ERROR: Missing required file: $f"
        exit 1
    fi
done
if [ ! -d "${NAS_DATA_DIR}/${NAS_CONTEXT_LENGTH}" ]; then
    echo "  ERROR: Missing RULER data dir: ${NAS_DATA_DIR}/${NAS_CONTEXT_LENGTH}"
    exit 1
fi
echo "  All required files found."

echo "[3/3] Starting NAS optimization..."
echo ""

# ─── Run LAMP ────────────────────────────────────────────────────────────────
# LAMP.py calls HFF_mod.call_init() → D=32, N=64, M=2, then evaluates
# 7 uniform anchors + LHS init points and runs the BO loop; each candidate
# is scored by get_objective_values() from run_ruler_lamp.py.

LOG_FILE="${NAS_TASK_CATEGORY}/${NAS_METHOD}/nas_run.log"
mkdir -p "${NAS_TASK_CATEGORY}/${NAS_METHOD}"

"$PYTHON_BIN" LAMP.py 2>&1 | tee "$LOG_FILE"

echo ""
echo "══════════════════════════════════════════════════════════════"
echo "NAS optimization completed!"
echo ""
echo "Outputs saved in: ${NAS_TASK_CATEGORY}/${NAS_METHOD}/"
echo "  - ${NAS_TASK_CATEGORY}/${NAS_METHOD}/output.txt      : All evaluated points (D+M columns)"
echo "  - ${NAS_TASK_CATEGORY}/${NAS_METHOD}/run_files/*.png : Pareto front plots"
echo "  - ${LOG_FILE}                                         : Full log of the optimization run"
echo ""
echo "To analyze results:"
echo "  python3 get_top_configs.py ${NAS_TASK_CATEGORY} ${NAS_METHOD}"
echo "  bash run_eval_ruler.sh   # full-data evaluation of the Pareto-front configs"
echo "══════════════════════════════════════════════════════════════"
