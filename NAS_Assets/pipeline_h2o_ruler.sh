#!/bin/bash
# Full remaining H2O RULER pipeline, chained end-to-end:
#
#   Phase 1: watch the unconstrained NAS (RULER_ALL/h2o) until it converges
#            (>= MIN_EVALS and best *shaped* (non-uniform) score stale for
#            STABLE_EVALS evals, or HARD_CAP rows) — mirrors SnapKV's
#            precedent (manually stopped at 198 evals).
#   Phase 2: extract the winner anchor (extract_winner_anchor.py) and
#            immediately launch Step 4 (budget-constrained slice NAS at
#            1024/1536/2048, 3 GPUs) — the expensive, highest-priority next
#            step, exactly as sequenced for SnapKV.
#   Phase 3: run watch_slices_and_eval.sh (NAS_METHOD=h2o) IN THE FOREGROUND
#            to manage those 3 slices to completion (auto full-500 eval per
#            slice on convergence, same as SnapKV).
#   Phase 4: once all 3 GPUs are free again, run the full-data Pareto-front
#            eval of RULER_ALL/h2o (Step 2 proper, sharded 3-way) and the
#            fixed-budget eval at 64/128/256/512 (Step 3), same order SnapKV
#            went through.
#
# Nothing here is auto-killed except the unconstrained LAMP.py once Phase 1
# decides it's converged.
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="${PYTHON_BIN:-/home/test/miniconda/envs/cakekv/bin/python}"
export PYTHONNOUSERSITE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="/home/snap_nas/sravanth/LLM/Token_Eviction/Dynamic_Methods/KVCache-Factory:${PYTHONPATH:-}"

METHOD="h2o"
OUT="RULER_ALL/${METHOD}/output.txt"
CHECK_INTERVAL="${CHECK_INTERVAL:-1800}"
MIN_EVALS="${MIN_EVALS:-198}"       # SnapKV precedent
STABLE_EVALS="${STABLE_EVALS:-40}"
HARD_CAP="${HARD_CAP:-350}"

echo "[$(date)] pipeline_h2o_ruler: watching ${OUT} (min ${MIN_EVALS}, stable ${STABLE_EVALS}, cap ${HARD_CAP})"

best_shaped_score() {
    "$PYTHON_BIN" - "$OUT" <<'EOF'
import sys
import numpy as np
from run_ruler_lamp import _decode_budgets
d = np.loadtxt(sys.argv[1])
d = d.reshape(1, -1) if d.ndim == 1 else d
best = None
for row in d:
    budgets = _decode_budgets(row[:-2], 32)
    if len(set(budgets)) == 1:
        continue
    score = -row[-1]
    if best is None or score > best:
        best = score
print(f"{best:.4f}" if best is not None else "NONE")
EOF
}

BEST=""; ROWS_AT_BEST=$MIN_EVALS
while true; do
    rows=$(awk 'NF>=34' "$OUT" 2>/dev/null | wc -l)
    if [ "$rows" -lt "$MIN_EVALS" ]; then
        sleep "$CHECK_INTERVAL"; continue
    fi
    best=$(best_shaped_score)
    if [ "$BEST" != "$best" ]; then
        [ -n "$BEST" ] && echo "[$(date)] H2O(unconstrained): new best shaped score ${best} @ ${rows} evals"
        BEST="$best"; ROWS_AT_BEST=$rows
        sleep "$CHECK_INTERVAL"; continue
    fi
    stale=$((rows - ROWS_AT_BEST)); [ "$stale" -lt 0 ] && stale=0
    pid=""
    for p in $(pgrep -f "[L]AMP.py"); do
        env_text=$(tr '\0' '\n' < "/proc/$p/environ" 2>/dev/null)
        echo "$env_text" | grep -q "^NAS_METHOD=${METHOD}$" && \
            echo "$env_text" | grep -q "^NAS_TARGET_BUDGET=0$" && pid=$p
    done
    if [ "$stale" -ge "$STABLE_EVALS" ] || [ "$rows" -ge "$HARD_CAP" ] || [ -z "$pid" ]; then
        reason="stable ${stale}"; [ "$rows" -ge "$HARD_CAP" ] && reason="hard cap"
        [ -z "$pid" ] && reason="LAMP died"
        echo "[$(date)] H2O(unconstrained): stopping (${reason}, ${rows} evals, best shaped score ${best})"
        for p in $(pgrep -f "[L]AMP.py"); do
            env_text=$(tr '\0' '\n' < "/proc/$p/environ" 2>/dev/null)
            echo "$env_text" | grep -q "^NAS_METHOD=${METHOD}$" && \
                echo "$env_text" | grep -q "^NAS_TARGET_BUDGET=0$" && kill "$p" 2>/dev/null
        done
        sleep 30
        break
    fi
    sleep "$CHECK_INTERVAL"
done

# ─── Phase 2: extract anchor + launch Step 4 ─────────────────────────────────
echo "[$(date)] extracting H2O winner anchor..."
"$PYTHON_BIN" extract_winner_anchor.py RULER_ALL --method "$METHOD" 2>&1 | tee "sravanth_logs/EXTRACT_ANCHOR_h2o_$(date +%d_%m_%Y).log"
ANCHOR_FILE=$(ls -t anchors/anchor_h2o_*.txt 2>/dev/null | head -1)
if [ -z "$ANCHOR_FILE" ]; then
    echo "[$(date)] ABORT: no anchor file produced for h2o"
    exit 1
fi
echo "[$(date)] using anchor ${ANCHOR_FILE}"

DATE=$(date +%d_%m_%Y)
NAS_METHOD="$METHOD" NAS_ANCHOR_FILE="${SCRIPT_DIR}/${ANCHOR_FILE}" \
    nohup bash run_nas_ruler_slices.sh > "sravanth_logs/NAS_RULER_SLICES_h2o_launch_${DATE}.log" 2>&1 &
echo "[$(date)] Step 4 (h2o slices 1024/1536/2048) launched -> sravanth_logs/NAS_RULER_SLICES_h2o_launch_${DATE}.log"
sleep 60

# ─── Phase 3: manage the 3 slices to completion (foreground, blocking) ──────
echo "[$(date)] launching watch_slices_and_eval.sh (NAS_METHOD=h2o) in foreground..."
NAS_METHOD="$METHOD" bash watch_slices_and_eval.sh 2>&1 | tee "sravanth_logs/WATCH_SLICES_h2o_${DATE}.log"
echo "[$(date)] all h2o slices searched and evaluated."

# ─── Phase 4: full-data Pareto eval (sharded 3-way) + fixed-budget eval ─────
echo "[$(date)] launching sharded full-data Pareto eval of RULER_ALL/h2o..."
for k in 0 1 2; do
    CUDA_VISIBLE_DEVICES="$k" "$PYTHON_BIN" eval_top_configs_ruler.py RULER_ALL --method "$METHOD" \
        --sample_ratio 1.0 --shard "${k}/3" \
        > "sravanth_logs/EVAL_RULER_ALL_h2o_shard${k}_${DATE}.log" 2>&1 &
done
wait
echo "[$(date)] full-data Pareto eval of RULER_ALL/h2o complete."

echo "[$(date)] launching fixed-budget eval (64,128,256,512) for h2o..."
"$PYTHON_BIN" eval_fixed_budgets_from_anchor.py "$ANCHOR_FILE" --method "$METHOD" \
    --targets 64,128,256,512 --gpu 0 \
    > "sravanth_logs/EVAL_RULER_FIXED_BUDGETS_h2o_${DATE}.log" 2>&1
echo "[$(date)] H2O RULER PIPELINE COMPLETE (Steps 1-4 done)."
