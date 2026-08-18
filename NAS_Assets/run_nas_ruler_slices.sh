#!/bin/bash
# Design B: fixed-budget-slice NAS for a method (NAS_METHOD, default snapkv) on RULER — 3 slices, one per GPU.
# Each slice pins the MEAN per-layer budget (NAS_TARGET_BUDGET) and searches
# allocation shapes with continuous budgets (exact-total proportional decode).
# Anchors: uniform-at-target + ramp/triangle/alternating heuristics + the
# unconstrained run's winner shape (NAS_ANCHOR_FILE, e.g. from
# extract_winner_anchor.py -- defaults to SnapKV's anchor_1756_budgets.txt).
# The LHS init points double as the random-allocation-at-matched-budget control.
#
#   nohup bash run_nas_ruler_slices.sh > sravanth_logs/NAS_RULER_SLICES_launch_$(date +%d_%m_%Y).log 2>&1 &
#   NAS_METHOD=h2o NAS_ANCHOR_FILE=anchors/anchor_h2o_1234.txt \
#       nohup bash run_nas_ruler_slices.sh > sravanth_logs/NAS_RULER_SLICES_h2o_launch_$(date +%d_%m_%Y).log 2>&1 &
#
# Per slice: ~31 min/candidate (single GPU, ratio 0.1); N=64 init ≈ 33 h,
# then BO. Watch each slice's output.txt; stop when best score stops improving.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

DATE=$(date +%d_%m_%Y)
TARGETS=(1024 1536 2048)
GPUS=(0 1 2)
METHOD="${NAS_METHOD:-snapkv}"

for i in "${!TARGETS[@]}"; do
    T="${TARGETS[$i]}"
    CUDA_VISIBLE_DEVICES="${GPUS[$i]}" \
    NAS_GPUS="${GPUS[$i]}" \
    NAS_TARGET_BUDGET="$T" \
    NAS_TASK_CATEGORY="RULER_ALL_B${T}" \
    NAS_METHOD="$METHOD" \
    NAS_SAMPLE_RATIO="${NAS_SAMPLE_RATIO:-0.1}" \
    NAS_SEED="${NAS_SEED:-42}" \
    NAS_ANCHOR_FILE="${NAS_ANCHOR_FILE:-${SCRIPT_DIR}/anchor_1756_budgets.txt}" \
    nohup bash run_nas_ruler.sh > "sravanth_logs/NAS_RULER_B${T}_${METHOD}_${DATE}.log" 2>&1 &
    echo "slice B=${T} on GPU ${GPUS[$i]} (pid $!) -> sravanth_logs/NAS_RULER_B${T}_${METHOD}_${DATE}.log"
done
wait
