#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
#  NAS for Per-Layer KV Cache Budget Optimization
#  Uses LAMP (Learning-Assisted Multi-objective Optimization) to find Pareto-optimal
#  per-layer budget configurations that trade off memory (f1) vs evicted attention (f2).
#
#  Pipeline: LAMP.py → HFF_mod.py → run_longbench_lamp.py → pyramidkv_utils.py
#
#  Two objectives to MINIMIZE:
#    f1 = average_budget         (avg KV cache budget across 32 layers — minimize memory)
#    f2 = evicted_attn_sum       (attention on evicted tokens — lower = evicting unimportant tokens)
#
#  D = 32 dimensions (one per layer for Llama-3-8B's 32 layers)
#  Budget options per layer: [64, 128, 256, 512, 1024, 2048, 4096]
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# GPU: override via NAS_GPUS, e.g. NAS_GPUS=2 bash run_nas.sh (matches run_nas_ruler.sh's pattern)
export NAS_GPUS="${NAS_GPUS:-1}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-$NAS_GPUS}"

# Explicit for clarity/robustness — HFF_mod.py defaults to "longbench" when unset,
# but this run_nas.sh has always relied on that implicit default until now.
export NAS_BENCHMARK="longbench"

# Python interpreter: bare `python3` can resolve to a broken environment
# (transformers incompatibility) — set PYTHON_BIN to the env with requirements.txt installed.
PYTHON_BIN="${PYTHON_BIN:-python}"
export PYTHONNOUSERSITE=1

# ─── Configuration (override via environment variables) ──────────────────────

# Model path
export NAS_MODEL_PATH="${NAS_MODEL_PATH:-meta-llama/Meta-Llama-3-8B-Instruct}"

# Eviction method: snapkv, pyramidkv, h2o, cam, streamingllm, l2norm, adakv, headkv
# export NAS_METHOD="${NAS_METHOD:-snapkv}"
# export NAS_METHOD="${NAS_METHOD:-h2o}"
# export NAS_METHOD="${NAS_METHOD:-adakv}"
export NAS_METHOD="${NAS_METHOD:-streamingllm}"

# Attention implementation: flash_attention_2, sdpa, eager
export NAS_ATTN_IMPL="${NAS_ATTN_IMPL:-flash_attention_2}"

# Data directory for LongBench datasets
export NAS_DATA_DIR="${NAS_DATA_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/data/LongBench}"

# Fraction of data to use for calibration (0.1 = 10%)
# export NAS_SAMPLE_RATIO="${NAS_SAMPLE_RATIO:-0.3}"
export NAS_SAMPLE_RATIO="${NAS_SAMPLE_RATIO:-1.0}"

# Random seed for reproducibility
export NAS_SEED="${NAS_SEED:-42}"

# Task category from data_clustering.json
# Options: SINGLE_DOCUMENT_QA, MULTI_DOCUMENT_QA, SUMMARIZATION,
#          FEW_SHOT_LEARNING, SYNTHETIC, CODE
# export NAS_TASK_CATEGORY="${NAS_TASK_CATEGORY:-SINGLE_DOCUMENT_QA}"
# export NAS_TASK_CATEGORY="${NAS_TASK_CATEGORY:-SUMMARIZATION}"
export NAS_TASK_CATEGORY="${NAS_TASK_CATEGORY:-MULTI_DOCUMENT_QA}"
# export NAS_TASK_CATEGORY="${NAS_TASK_CATEGORY:-CODE}"

# f2 metric: "evicted_attn" (default, fast) or "task_score" (slower but more accurate)
# - evicted_attn: f2 = sum of attention on evicted tokens (lower = evicting unimportant tokens)
# - task_score:   f2 = -1 * avg task score on calibration data (minimize negative = maximize score)
# export NAS_F2_METRIC="${NAS_F2_METRIC:-evicted_attn}"
export NAS_F2_METRIC="${NAS_F2_METRIC:-task_score}"

# ─── Print configuration ─────────────────────────────────────────────────────

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  NAS for Per-Layer KV Cache Budget Optimization            ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Model:        ${NAS_MODEL_PATH##*/}"
echo "║  Method:        ${NAS_METHOD}"
echo "║  Task Category: ${NAS_TASK_CATEGORY}"
echo "║  f2 Metric:     ${NAS_F2_METRIC}"
echo "║  Sample Ratio:  ${NAS_SAMPLE_RATIO}"
echo "║  Attn Impl:     ${NAS_ATTN_IMPL}"
echo "║  Data Dir:      ${NAS_DATA_DIR}"
echo "╚══════════════════════════════════════════════════════════════╝"

# ─── Navigate to the nas/ directory ────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "[1/3] Adding PyramidKV to Python path..."
export PYTHONPATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd):${PYTHONPATH:-}"

echo "[2/3] Checking for required files..."
for f in LAMP.py HFF_mod.py run_longbench_lamp.py data_clustering.json ndsort.py; do
    if [ ! -f "$f" ]; then
        echo "  ERROR: Missing required file: $f"
        exit 1
    fi
done
echo "  All required files found."

echo "[3/3] Starting NAS optimization..."
echo ""

# ─── Run LAMP ────────────────────────────────────────────────────────────────
# LAMP.py is the main entry point.
# It calls HFF_mod.call_init() → D=32, N=64, M=2
# Then generates LHS initial points and calls HFF_mod.call_HFF()
# which calls get_objective_values() from run_longbench_lamp.py
# which runs calibration and returns (f1, f2) for each point.

LOG_FILE="${NAS_TASK_CATEGORY}/${NAS_METHOD}/nas_run.log"
mkdir -p "${NAS_TASK_CATEGORY}/${NAS_METHOD}"


"$PYTHON_BIN" LAMP.py 2>&1 | tee "$LOG_FILE"

echo ""
echo "══════════════════════════════════════════════════════════════"
echo "NAS optimization completed!"
echo ""
echo "Outputs saved in: ${NAS_TASK_CATEGORY}/${NAS_METHOD}/"
echo "  - ${NAS_TASK_CATEGORY}/${NAS_METHOD}/output.txt     : All evaluated points (D+M columns)"
echo "  - ${NAS_TASK_CATEGORY}/${NAS_METHOD}/run_files/*.png : Pareto front plots"
echo "  - ${LOG_FILE}                                        : Full log of the optimization run"
echo ""
echo "To analyze results:"
echo "  python3 -c \"import numpy as np; d=np.loadtxt('${NAS_TASK_CATEGORY}/${NAS_METHOD}/output.txt'); print('Points:', d.shape); print('f1 (avg_budget):', d[:,-2]); print('f2 (evicted_attn):', d[:,-1])\""

echo "══════════════════════════════════════════════════════════════"
