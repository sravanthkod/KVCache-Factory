#!/bin/bash
# Evaluate the best-BO config of B1536 and B2048 on full 500 samples (GPU 2),
# sequentially. eval_top_configs_ruler.py always writes top_configs/
# eval_results.csv, so back up the existing 3-arch CSV first and rename the
# BO result to eval_results_bo.csv afterwards.
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
PYTHON_BIN="${PYTHON_BIN:-/home/test/miniconda/envs/cakekv/bin/python}"
export PYTHONNOUSERSITE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="/home/snap_nas/sravanth/LLM/Token_Eviction/Dynamic_Methods/KVCache-Factory:${PYTHONPATH:-}"
DATE=$(date +%d_%m_%Y)

for T in 1536 2048; do
    dir="RULER_ALL_B${T}/snapkv/top_configs"
    cp -n "${dir}/eval_results.csv" "${dir}/eval_results_3archs.csv"
    echo "[$(date)] B${T}: evaluating best-BO config on full 500..."
    CUDA_VISIBLE_DEVICES=2 NAS_GPUS="" NAS_TARGET_BUDGET="$T" \
        NAS_TASK_CATEGORY="RULER_ALL_B${T}" \
        "$PYTHON_BIN" eval_top_configs_ruler.py "RULER_ALL_B${T}" --method snapkv \
        --all_rows --sample_ratio 1.0 \
        --output_file "${dir}/bo_best_snapshot.txt"
    mv "${dir}/eval_results.csv" "${dir}/eval_results_bo.csv"
    cp "${dir}/eval_results_3archs.csv" "${dir}/eval_results.csv"
    echo "[$(date)] B${T}: done -> ${dir}/eval_results_bo.csv"
done
echo "[$(date)] ALL BO EVALS DONE"
