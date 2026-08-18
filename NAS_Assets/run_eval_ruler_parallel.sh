#!/bin/bash
# Held-out evaluation of the RULER_ALL Pareto-front configs, sharded over 3 GPUs.
# Each shard evaluates every 3rd Pareto config on the 450 samples/subtask the
# NAS fitness never saw (complement of the ratio-0.1 seed-42 subsample), then
# the shard CSVs are merged into top_configs/eval_results_holdout.csv.
#
#   nohup bash run_eval_ruler_parallel.sh > sravanth_logs/EVAL_RULER_ALL_parallel_$(date +%d_%m_%Y).log 2>&1 &

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export PYTHONPATH="/home/snap_nas/sravanth/LLM/Token_Eviction/Dynamic_Methods/KVCache-Factory:${PYTHONPATH:-}"
PYTHON_BIN="${PYTHON_BIN:-/home/test/miniconda/envs/cakekv/bin/python}"
export PYTHONNOUSERSITE=1
# Line-buffer python stdout so shard logs show progress in real time
export PYTHONUNBUFFERED=1

export NAS_BENCHMARK="ruler"
# Must match the search so the holdout complement is exact:
export NAS_SAMPLE_RATIO="${NAS_SAMPLE_RATIO:-0.1}"
export NAS_SEED="${NAS_SEED:-42}"
# The eval workers are plain single-GPU processes:
unset NAS_GPUS

CATEGORY="${CATEGORY:-RULER_ALL}"
METHOD="${METHOD:-snapkv}"
# EVAL_GPUS="1 2" to use a subset; HOLDOUT=0 to evaluate on ALL samples
# (500/subtask) instead of the 450 the NAS never saw.
read -r -a GPUS <<< "${EVAL_GPUS:-0 1 2}"
HOLDOUT="${HOLDOUT:-1}"
if [ "$HOLDOUT" = "1" ]; then
    HOLDOUT_FLAG="--holdout"; SUFFIX="_holdout"; MERGED="eval_results_holdout.csv"
else
    HOLDOUT_FLAG=""; SUFFIX=""; MERGED="eval_results_all500.csv"
fi
DATE=$(date +%d_%m_%Y)

TOP_DIR="${CATEGORY}/${METHOD}/top_configs"
mkdir -p "$TOP_DIR"

# Freeze the NAS results ONCE before spawning shards. Every shard reads this
# snapshot, so all three compute the identical Pareto front and arch numbering
# even if the NAS process was still flushing rows to output.txt when killed.
# awk keeps only complete rows (34 columns) in case the last line was truncated.
SNAPSHOT="${TOP_DIR}/output_snapshot.txt"
awk 'NF==34' "${CATEGORY}/${METHOD}/output.txt" > "$SNAPSHOT"
echo "Snapshot: $(wc -l < "$SNAPSHOT") complete rows -> ${SNAPSHOT}"

# Remove stale shard CSVs so the merge can never pick up a previous run's files
rm -f "${TOP_DIR}/eval_results${SUFFIX}_shard"*.csv

echo "Launching ${#GPUS[@]} eval shards for ${CATEGORY}/${METHOD} (holdout=${HOLDOUT}, gpus=${GPUS[*]})"

PIDS=()
for k in "${!GPUS[@]}"; do
    LOG="sravanth_logs/EVAL_RULER_ALL${SUFFIX}_shard${k}_${DATE}.log"
    CUDA_VISIBLE_DEVICES="${GPUS[$k]}" NAS_GPUS="" \
        "$PYTHON_BIN" eval_top_configs_ruler.py "$CATEGORY" --method "$METHOD" \
        --shard "${k}/${#GPUS[@]}" $HOLDOUT_FLAG --sample_ratio 1.0 --save_predictions \
        --output_file "$SNAPSHOT" \
        > "$LOG" 2>&1 &
    PIDS+=($!)
    echo "  shard ${k} on GPU ${GPUS[$k]} (pid ${PIDS[$k]}, log ${LOG})"
done

FAIL=0
for pid in "${PIDS[@]}"; do
    wait "$pid" || FAIL=1
done

if [ "$FAIL" -ne 0 ]; then
    echo "ERROR: at least one eval shard failed — check the shard logs. Not merging."
    exit 1
fi

echo "All shards done, merging..."
"$PYTHON_BIN" - "$CATEGORY" "$METHOD" "$SUFFIX" "$MERGED" <<'EOF'
import csv, glob, os, sys
category, method, suffix, merged = sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "_holdout", sys.argv[4] if len(sys.argv) > 4 else "eval_results_holdout.csv"
top_dir = os.path.join(category, method, "top_configs")
rows, fieldnames = [], None
for path in sorted(glob.glob(os.path.join(top_dir, f"eval_results{suffix}_shard*.csv"))):
    with open(path) as f:
        reader = csv.DictReader(f)
        fieldnames = fieldnames or reader.fieldnames
        rows.extend(reader)
rows.sort(key=lambda r: int(r["arch"]))
out = os.path.join(top_dir, merged)
with open(out, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
print(f"Merged {len(rows)} configs -> {out}")
for r in rows:
    print(f"  arch {r['arch']}: avg_budget={float(r['avg_budget']):.1f}, mean_score={float(r['mean_score']):.2f}")
EOF

echo "EVAL COMPLETE"
