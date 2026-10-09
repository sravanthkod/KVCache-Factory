#!/bin/bash
# Design B: fixed-budget-slice NAS for a method (NAS_METHOD, default snapkv) on
# LongBench — one CATEGORY per GPU (not one budget per GPU, unlike RULER's
# run_nas_ruler_slices.sh), each looping sequentially over TARGETS.
# Each slice pins the MEAN per-layer budget (NAS_TARGET_BUDGET) and searches
# allocation shapes with continuous budgets (exact-total proportional decode).
# Anchors: uniform-at-target + ramp/triangle/alternating heuristics + the
# unconstrained run's winner shape (NAS_ANCHOR_FILE, per-category anchor from
# the existing top_configs/summary_*.csv winner extraction — see
# anchors/anchor_longbench_<category>_<method>.txt).
#
#   NAS_METHOD=snapkv nohup bash run_nas_longbench_slices.sh \
#       > logs/NAS_LONGBENCH_SLICES_snapkv_launch_$(date +%d_%m_%Y).log 2>&1 &
#
# Targets: 128/256/512/1024 (not RULER's 1024/1536/2048) — LongBench's
# completed Step-1 unconstrained search only explored budgets up to 1024
# (BUDGET_OPTIONS was [64,128,256,512,1024] at the time), so 1024 is the
# highest empirically-validated ceiling for this run; see the plan file for
# the per-category saturation evidence that justifies this cap for SnapKV.
# 128 added after Step 3 showed the naive rescaled-shape comparison losing to
# uniform at 64/128 for SINGLE/MULTI_DOCUMENT_QA — a real slice search (this
# script) optimizes the shape AT that budget instead of inheriting one found
# at a different operating point. 64 itself is skipped: with
# NAS_MIN_BUDGET=64 (the current default), target=64 is mathematically
# degenerate (floor == target forces pure uniform, nothing to search).

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

DATE=$(date +%d_%m_%Y)
TARGETS=(128 256 512 1024)
CATEGORIES=(SINGLE_DOCUMENT_QA MULTI_DOCUMENT_QA CODE)
GPUS=(0 1 2)
METHOD="${NAS_METHOD:-snapkv}"

for i in "${!CATEGORIES[@]}"; do
    CAT="${CATEGORIES[$i]}"
    GPU="${GPUS[$i]}"
    (
        for T in "${TARGETS[@]}"; do
            CUDA_VISIBLE_DEVICES="$GPU" \
            NAS_GPUS="$GPU" \
            NAS_BENCHMARK="longbench" \
            NAS_TARGET_BUDGET="$T" \
            NAS_TASK_CATEGORY="${CAT}_B${T}" \
            NAS_METHOD="$METHOD" \
            NAS_SAMPLE_RATIO="${NAS_SAMPLE_RATIO:-0.1}" \
            NAS_SEED="${NAS_SEED:-42}" \
            NAS_ANCHOR_FILE="${NAS_ANCHOR_FILE:-${SCRIPT_DIR}/anchors/anchor_longbench_${CAT}_${METHOD}.txt}" \
            bash run_nas.sh > "logs/NAS_LONGBENCH_${CAT}_B${T}_${METHOD}_${DATE}.log" 2>&1
        done
    ) &
    echo "category ${CAT} on GPU ${GPU} (pid $!), targets ${TARGETS[*]} sequentially"
done
wait
