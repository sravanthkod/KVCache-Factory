#!/bin/bash
# Wait for the H2O uniform RULER baseline extension (1536+2048, running on
# GPU 2) to finish, then launch the SnapKV Step-3 fixed-budget eval
# (64/128/256/512, full 500 samples) on the now-free GPU 2.
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

WAIT_PID="${1:?usage: wait_and_launch_snapkv_fixed_budgets.sh <wrapper_pid>}"
DATE=$(date +%d_%m_%Y)

echo "[$(date)] waiting for pid ${WAIT_PID} (H2O uniform extension) to exit..."
while kill -0 "$WAIT_PID" 2>/dev/null; do sleep 300; done
echo "[$(date)] pid ${WAIT_PID} gone; verifying GPU 2 is free..."
sleep 30

export PYTHONNOUSERSITE=1
export PYTHONPATH="/home/snap_nas/sravanth/LLM/Token_Eviction/Dynamic_Methods/KVCache-Factory:${PYTHONPATH:-}"
PYTHON_BIN="/home/test/miniconda/envs/cakekv/bin/python"

echo "[$(date)] launching SnapKV fixed-budget eval (64,128,256,512) on GPU 2"
"$PYTHON_BIN" eval_fixed_budgets_from_anchor.py anchor_1756_budgets.txt \
    --method snapkv --targets 64,128,256,512 --gpu 2 \
    > "sravanth_logs/EVAL_RULER_FIXED_BUDGETS_snapkv_${DATE}.log" 2>&1
echo "[$(date)] SnapKV fixed-budget eval finished, exit code $?"
