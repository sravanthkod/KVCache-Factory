#!/bin/bash
# Wait for the SnapKV fixed-budget eval on GPU 2 to finish, then launch H2O's
# B2048 constrained slice there (B1024/B1536 are already running on GPU 0/1),
# and once all 3 H2O slices are confirmed running, launch watch_slices_and_eval.sh
# (NAS_METHOD=h2o) to manage them to completion.
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

WAIT_PID="${1:?usage: wait_and_launch_h2o_b2048.sh <gpu2_pid>}"
ANCHOR="${SCRIPT_DIR}/anchors/anchor_h2o_2180.txt"
DATE=$(date +%d_%m_%Y)

export PYTHONNOUSERSITE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="/home/snap_nas/sravanth/LLM/Token_Eviction/Dynamic_Methods/KVCache-Factory:${PYTHONPATH:-}"

echo "[$(date)] waiting for pid ${WAIT_PID} (SnapKV fixed-budget eval) to free GPU 2..."
while kill -0 "$WAIT_PID" 2>/dev/null; do sleep 300; done
echo "[$(date)] pid ${WAIT_PID} gone; verifying GPU 2 is free..."
sleep 30

CUDA_VISIBLE_DEVICES=2 NAS_GPUS=2 NAS_TARGET_BUDGET=2048 NAS_TASK_CATEGORY=RULER_ALL_B2048 \
    NAS_METHOD=h2o NAS_SAMPLE_RATIO=0.1 NAS_SEED=42 NAS_ANCHOR_FILE="$ANCHOR" \
    nohup bash run_nas_ruler.sh > "sravanth_logs/NAS_RULER_B2048_h2o_${DATE}.log" 2>&1 &
echo "[$(date)] H2O slice B2048 launched on GPU2 (pid $!)"
sleep 60

# Confirm all 3 H2O slices are actually running before starting the watcher —
# watch_slices_and_eval.sh treats a missing LAMP pid as "died" and would
# otherwise prematurely try to stop/evaluate a slice that never started.
for T in 1024 1536 2048; do
    found=""
    for p in $(pgrep -f "[L]AMP.py"); do
        env_text=$(tr '\0' '\n' < "/proc/$p/environ" 2>/dev/null)
        echo "$env_text" | grep -q "^NAS_METHOD=h2o$" && \
            echo "$env_text" | grep -q "^NAS_TARGET_BUDGET=${T}$" && found=$p
    done
    if [ -z "$found" ]; then
        echo "[$(date)] ABORT: H2O slice B${T} is not running — not starting watcher."
        exit 1
    fi
    echo "[$(date)] confirmed: H2O slice B${T} running (pid ${found})"
done

echo "[$(date)] all 3 H2O slices confirmed running — launching watch_slices_and_eval.sh"
NAS_METHOD=h2o nohup bash watch_slices_and_eval.sh > "sravanth_logs/WATCH_SLICES_h2o_${DATE}.log" 2>&1 &
echo "[$(date)] watcher launched (pid $!) -> sravanth_logs/WATCH_SLICES_h2o_${DATE}.log"
