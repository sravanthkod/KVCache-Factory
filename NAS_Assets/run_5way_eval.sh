#!/bin/bash
# Build the 5-way Step-4 snapshot (uniform / best_heuristic / best_winner /
# best_random / best_bo) from an existing NAS output.txt and immediately
# full-data-evaluate it. Wraps select_5way_snapshot.py + eval_top_configs_ruler.py
# / eval_top_configs_longbench.py (auto-picked via NAS_BENCHMARK) into one call.
#
# Usage:
#   NAS_TASK_CATEGORY=RULER_ALL_B1024 NAS_METHOD=snapkv \
#       bash run_5way_eval.sh
#
#   NAS_BENCHMARK=longbench NAS_TASK_CATEGORY=SINGLE_DOCUMENT_QA_B512 \
#       NAS_METHOD=snapkv NAS_TARGET_BUDGET=512 CUDA_VISIBLE_DEVICES=0 \
#       bash run_5way_eval.sh
#
# Required env vars:
#   NAS_TASK_CATEGORY   e.g. RULER_ALL_B1024 (must match the dir the output.txt lives in)
#   NAS_METHOD          e.g. snapkv, h2o, l2norm (default: snapkv)
#
# Optional env vars:
#   NAS_BENCHMARK       "ruler" (default) or "longbench" -- picks which eval_top_configs_*.py to call
#   NAS_TARGET_BUDGET   only needed for Step-4 slice-mode runs (continuous budget decode) --
#                        set it to the SAME value used when the search was launched
#   CUDA_VISIBLE_DEVICES  which GPU to run the full-data eval on (default: 0)
#   DEDUPE              1 to pass --dedupe to select_5way_snapshot.py (default: 1)
#   SAMPLE_RATIO        eval sample ratio (default: 1.0 = full data)
#   PYTHON_BIN          python interpreter (default: matches run_nas.sh's cakekv env pin)

set -e

# Without this, Python checks ~/.local/lib/python3.10/site-packages BEFORE
# the cakekv conda env's own site-packages, and picks up whatever transformers
# version happens to be pip-installed there at the user level (found to be a
# broken transformers==5.9.0, vs. the correct 4.43.3 inside the conda env) --
# incompatible with this repo's monkeypatches (LlamaFlashAttention2/StaticCache
# don't exist the same way in 5.x), causing an immediate, silent-looking
# Bus error (core dumped) crash during model load. run_nas.sh already sets
# this; this script didn't, which is why eval_top_configs_*.py crashed here
# while LAMP.py (launched via run_nas.sh) kept working fine.
export PYTHONNOUSERSITE=1

# Needed so eval_top_configs_*.py can import the pyramidkv package (repo root,
# not NAS_Assets/) -- run_nas.sh sets this too; this script didn't.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$(cd "$SCRIPT_DIR/.." && pwd):${PYTHONPATH:-}"

NAS_METHOD="${NAS_METHOD:-snapkv}"
NAS_BENCHMARK="${NAS_BENCHMARK:-ruler}"
DEDUPE="${DEDUPE:-1}"
SAMPLE_RATIO="${SAMPLE_RATIO:-1.0}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
PYTHON_BIN="${PYTHON_BIN:-/home/test/miniconda/envs/cakekv/bin/python}"

if [ -z "${NAS_TASK_CATEGORY:-}" ]; then
    echo "Error: NAS_TASK_CATEGORY is required, e.g. NAS_TASK_CATEGORY=RULER_ALL_B1024 bash run_5way_eval.sh" >&2
    exit 1
fi

OUTPUT_TXT="${NAS_TASK_CATEGORY}/${NAS_METHOD}/output.txt"
SNAPSHOT="${NAS_TASK_CATEGORY}/${NAS_METHOD}/top_configs/five_way_snapshot.txt"

if [ ! -f "$OUTPUT_TXT" ]; then
    echo "Error: $OUTPUT_TXT not found -- run the NAS search first" >&2
    exit 1
fi

echo "[1/2] Building 5-way snapshot from $OUTPUT_TXT ..."
DEDUPE_FLAG=""
[ "$DEDUPE" = "1" ] && DEDUPE_FLAG="--dedupe"
"$PYTHON_BIN" select_5way_snapshot.py "$OUTPUT_TXT" --out "$SNAPSHOT" $DEDUPE_FLAG

echo
echo "[2/2] Full-data eval (sample_ratio=$SAMPLE_RATIO) on GPU $CUDA_VISIBLE_DEVICES ..."
if [ "$NAS_BENCHMARK" = "longbench" ]; then
    if [ -n "${NAS_TARGET_BUDGET:-}" ]; then
        export NAS_TARGET_BUDGET
    fi
    "$PYTHON_BIN" eval_top_configs_longbench.py "$NAS_TASK_CATEGORY" --method "$NAS_METHOD" \
        --all_rows --sample_ratio "$SAMPLE_RATIO" --output_file "$SNAPSHOT"
else
    if [ -n "${NAS_TARGET_BUDGET:-}" ]; then
        export NAS_TARGET_BUDGET
    fi
    "$PYTHON_BIN" eval_top_configs_ruler.py "$NAS_TASK_CATEGORY" --method "$NAS_METHOD" \
        --all_rows --sample_ratio "$SAMPLE_RATIO" --output_file "$SNAPSHOT"
fi

echo
echo "Done -> ${NAS_TASK_CATEGORY}/${NAS_METHOD}/top_configs/eval_results.csv"
