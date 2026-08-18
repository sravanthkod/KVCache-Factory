#!/bin/bash
# Watch a RESUMED slice search (main watcher already marked this slice done).
# Same rule as watch_slices_and_eval.sh v2: stop after STABLE_EVALS guided evals
# without a new best (staleness counted from max(rows_at_best, 64)) or HARD_CAP
# rows. On stop: if BO found a config better than the already-evaluated best
# (the winner-shape anchor, fitness EVALUATED_BEST), run a TOP-UP eval of just
# the new best row on GPU; otherwise nothing left to evaluate.
#
# Defaults reproduce the original B1536/snapkv incident-recovery invocation
# unchanged. Override via env for any other slice/method, e.g.:
#   NAS_TARGET_BUDGET=1024 GPU=0 NAS_METHOD=h2o EVALUATED_BEST=91.46 \
#       bash watch_b1536_resume.sh
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="${PYTHON_BIN:-/home/test/miniconda/envs/cakekv/bin/python}"
export PYTHONNOUSERSITE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="/home/snap_nas/sravanth/LLM/Token_Eviction/Dynamic_Methods/KVCache-Factory:${PYTHONPATH:-}"

CHECK_INTERVAL="${CHECK_INTERVAL:-1800}"
STABLE_EVALS="${STABLE_EVALS:-40}"
HARD_CAP="${HARD_CAP:-160}"
T="${NAS_TARGET_BUDGET:-1536}"; GPU="${GPU:-1}"
METHOD="${NAS_METHOD:-snapkv}"
DIR="RULER_ALL_B${T}/${METHOD}"
DATE=$(date +%d_%m_%Y)
# Fitness score of the winner-shape anchor, already fully evaluated.
EVALUATED_BEST="${EVALUATED_BEST:-98.39}"

BEST=""; ROWS_AT_BEST=64
while true; do
    rows=$(awk 'NF>=34' "$DIR/output.txt" | wc -l)
    best=$(awk 'NF>=34 {print $NF}' "$DIR/output.txt" | sort -g | head -1)
    score=$(awk "BEGIN{printf \"%.2f\", -1*$best}")
    if [ "$BEST" != "$best" ]; then
        [ -n "$BEST" ] && echo "B${T}(resume): new best ${score} @ ${rows} evals"
        BEST="$best"; ROWS_AT_BEST=$rows
        [ "$ROWS_AT_BEST" -lt 64 ] && ROWS_AT_BEST=64
        sleep "$CHECK_INTERVAL"; continue
    fi
    stale=$((rows - ROWS_AT_BEST)); [ "$stale" -lt 0 ] && stale=0
    pid=""
    for p in $(pgrep -f "[L]AMP.py"); do
        env_text=$(tr '\0' '\n' < "/proc/$p/environ" 2>/dev/null)
        echo "$env_text" | grep -q "^NAS_TARGET_BUDGET=${T}$" && \
            echo "$env_text" | grep -q "^NAS_METHOD=${METHOD}$" && pid=$p
    done
    if [ "$stale" -ge "$STABLE_EVALS" ] || [ "$rows" -ge "$HARD_CAP" ] || [ -z "$pid" ]; then
        reason="stable ${stale}"; [ "$rows" -ge "$HARD_CAP" ] && reason="hard cap"
        [ -z "$pid" ] && reason="LAMP died"
        echo "B${T}(resume): stopping search (${reason}, ${rows} evals, best ${score})"
        [ -n "$pid" ] && kill "$pid" 2>/dev/null
        sleep 45
        improved=$(awk -v ref="$EVALUATED_BEST" 'NF>=34 && NR>64 && -$NF > ref+0.005 {print NR; exit}' "$DIR/output.txt")
        if [ -n "$improved" ]; then
            snap="$DIR/top_configs/bo_topup_snapshot.txt"
            awk 'NF>=34' "$DIR/output.txt" | sort -g -k34,34 | head -1 > "$snap"
            # eval_top_configs_ruler.py writes to top_configs/eval_results.csv —
            # preserve the completed 3-arch results before the top-up overwrites it.
            cp -n "$DIR/top_configs/eval_results.csv" "$DIR/top_configs/eval_results_init_archs.csv"
            echo "B${T}(resume): BO beat ${EVALUATED_BEST} — topping up eval of best row"
            CUDA_VISIBLE_DEVICES="$GPU" NAS_GPUS="" NAS_TARGET_BUDGET="$T" NAS_METHOD="$METHOD" \
                NAS_TASK_CATEGORY="RULER_ALL_B${T}" \
                setsid nohup "$PYTHON_BIN" eval_top_configs_ruler.py "RULER_ALL_B${T}" --method "$METHOD" \
                --all_rows --sample_ratio 1.0 --save_predictions --output_file "$snap" \
                > "sravanth_logs/EVAL_RULER_B${T}_${METHOD}_bo_topup_${DATE}.log" 2>&1 &
            echo "B${T}(resume): TOP-UP EVAL LAUNCHED on GPU ${GPU}"
        else
            echo "B${T}(resume): BO never beat winner shape (${EVALUATED_BEST}) — no top-up eval needed. DONE."
        fi
        exit 0
    fi
    sleep "$CHECK_INTERVAL"
done
