#!/bin/bash
# Wait for a slice's all-500 eval (pid passed as $1) to finish, then resume
# that slice's search from row 64 (init phase complete, BO continues from
# there). Env must match run_nas_ruler_slices.sh exactly so X_init
# regenerates identically and NAS_RESUME_ROWS replay lines up with output.txt.
#
# Defaults reproduce the original B1536/snapkv incident-recovery invocation
# unchanged. Override via env for any other slice/method, e.g.:
#   NAS_TARGET_BUDGET=1024 CUDA_VISIBLE_DEVICES=0 NAS_METHOD=h2o \
#       NAS_ANCHOR_FILE=anchors/anchor_h2o_1234.txt \
#       bash resume_b1536_after_eval.sh <eval_pid>
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

EVAL_PID="${1:?usage: resume_b1536_after_eval.sh <eval_pid>}"
DATE=$(date +%d_%m_%Y)

T="${NAS_TARGET_BUDGET:-1536}"
GPU="${CUDA_VISIBLE_DEVICES:-1}"
METHOD="${NAS_METHOD:-snapkv}"
ANCHOR_FILE="${NAS_ANCHOR_FILE:-${SCRIPT_DIR}/anchor_1756_budgets.txt}"

echo "[$(date)] waiting for eval pid ${EVAL_PID} to exit..."
while kill -0 "$EVAL_PID" 2>/dev/null; do sleep 300; done
echo "[$(date)] eval pid ${EVAL_PID} gone; verifying GPU ${GPU} is free..."
sleep 60

ROWS=$(awk 'NF>=34' "RULER_ALL_B${T}/${METHOD}/output.txt" | wc -l)
if [ "$ROWS" -ne 64 ]; then
    echo "[$(date)] ABORT: expected 64 complete rows in RULER_ALL_B${T}/${METHOD}/output.txt, found ${ROWS}"
    exit 1
fi

CUDA_VISIBLE_DEVICES="$GPU" \
NAS_GPUS="$GPU" \
NAS_TARGET_BUDGET="$T" \
NAS_TASK_CATEGORY="RULER_ALL_B${T}" \
NAS_METHOD="$METHOD" \
NAS_SAMPLE_RATIO=0.1 \
NAS_SEED=42 \
NAS_ANCHOR_FILE="$ANCHOR_FILE" \
NAS_RESUME_ROWS=64 \
setsid nohup bash run_nas_ruler.sh > "sravanth_logs/NAS_RULER_B${T}_${METHOD}_RESUME_${DATE}.log" 2>&1 &
echo "[$(date)] B${T} (${METHOD}) search RESUMED from row 64 (pid $!) -> sravanth_logs/NAS_RULER_B${T}_${METHOD}_RESUME_${DATE}.log"
