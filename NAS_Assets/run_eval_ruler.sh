#!/bin/bash
# Post-NAS full evaluation of RULER Pareto-front configs (mirrors run_eval.sh).
# Run from NAS_Assets/ after the NAS has produced <category>/<method>/output.txt.
#
#   nohup bash run_eval_ruler.sh > ../sravanth_logs/EVAL_RULER_NIAH_SINGLE_snapkv_$(date +%d_%m_%Y).log 2>&1 &

export PYTHONPATH="/home/snap_nas/sravanth/LLM/Token_Eviction/Dynamic_Methods/KVCache-Factory:${PYTHONPATH:-}"

# cakekv env + no user site (broken ~/.local transformers shadow → bus error)
PYTHON_BIN="${PYTHON_BIN:-/home/test/miniconda/envs/cakekv/bin/python}"
export PYTHONNOUSERSITE=1

export NAS_BENCHMARK="ruler"

# export CUDA_VISIBLE_DEVICES=0
export CUDA_VISIBLE_DEVICES=1
# export CUDA_VISIBLE_DEVICES=2

"$PYTHON_BIN" eval_top_configs_ruler.py "RULER_NIAH_SINGLE" --method "snapkv" --save_predictions

# "$PYTHON_BIN" eval_top_configs_ruler.py "RULER_NIAH_MULTI" --method "snapkv" --save_predictions
# "$PYTHON_BIN" eval_top_configs_ruler.py "RULER_AGGREGATION" --method "snapkv" --save_predictions
# "$PYTHON_BIN" eval_top_configs_ruler.py "RULER_VT" --method "snapkv" --save_predictions
