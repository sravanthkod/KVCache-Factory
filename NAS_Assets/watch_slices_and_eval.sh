#!/bin/bash
# Watch the 3 fixed-budget slice searches; when a slice's best score has been
# stable for STABLE_EVALS evaluations (or HARD_CAP rows reached), stop THAT
# slice's LAMP (identified via NAS_TARGET_BUDGET + NAS_METHOD in
# /proc/<pid>/environ) and launch its full-500 evaluation on the freed GPU.
# Evaluated configs per slice: uniform anchor + best heuristic anchor + best
# random (LHS) + best overall — the complete iso-budget paper row with
# controls.
#
# Method is generic via NAS_METHOD (default snapkv, unchanged behavior):
#   NAS_METHOD=h2o bash watch_slices_and_eval.sh
#
# Emits one line per notable event. No global pkill — per-slice PIDs only.

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="${PYTHON_BIN:-/home/test/miniconda/envs/cakekv/bin/python}"
export PYTHONNOUSERSITE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="/home/snap_nas/sravanth/LLM/Token_Eviction/Dynamic_Methods/KVCache-Factory:${PYTHONPATH:-}"

METHOD="${NAS_METHOD:-snapkv}"
CHECK_INTERVAL="${CHECK_INTERVAL:-1800}"
STABLE_EVALS="${STABLE_EVALS:-40}"
HARD_CAP="${HARD_CAP:-160}"
DATE=$(date +%d_%m_%Y)

TARGETS=(1024 1536 2048)
GPUS=(0 1 2)
declare -A STATE BEST ROWS_AT_BEST
for T in "${TARGETS[@]}"; do STATE[$T]="searching"; done

lamp_pid_for_target() {
    for pid in $(pgrep -f "[L]AMP.py"); do
        env_text=$(tr '\0' '\n' < "/proc/$pid/environ" 2>/dev/null)
        if echo "$env_text" | grep -q "^NAS_TARGET_BUDGET=$1$" && \
           echo "$env_text" | grep -q "^NAS_METHOD=${METHOD}$"; then
            echo "$pid"; return 0
        fi
    done
    return 1
}

build_snapshot_and_eval() {
    local T=$1 GPU=$2
    local dir="RULER_ALL_B${T}/${METHOD}"
    local snap="${dir}/top_configs/slice_eval_snapshot.txt"
    mkdir -p "${dir}/top_configs"
    # Freeze complete rows only (the killed LAMP may have left a truncated line)
    awk 'NF>=34' "$dir/output.txt" > "${dir}/top_configs/search_rows_frozen.txt"
    "$PYTHON_BIN" - "${dir}/top_configs/search_rows_frozen.txt" "$snap" <<'EOF'
import sys
import numpy as np
d = np.loadtxt(sys.argv[1])
d = d.reshape(1, -1) if d.ndim == 1 else d
f2 = d[:, -1]
picks = [0]                                   # row 0: uniform anchor
if len(d) > 1:
    picks.append(1 + int(np.argmin(f2[1:7])))     # best heuristic anchor (rows 1-6)
if len(d) > 7:
    picks.append(7 + int(np.argmin(f2[7:64])))    # best random LHS (rows 7-63)
picks.append(int(np.argmin(f2)))                  # best overall
seen, rows = set(), []
labels = ["uniform_anchor", "best_heuristic", "best_random", "best_overall"]
kept = []
for lbl, i in zip(labels, picks):
    if i not in seen:
        seen.add(i); rows.append(d[i]); kept.append(f"{lbl}=row{i+1}(score {-f2[i]:.2f})")
np.savetxt(sys.argv[2], np.array(rows))
print("snapshot picks: " + ", ".join(kept))
EOF
    # setsid: detach into its own session so the eval survives if this
    # watcher process (and its group) is killed/TaskStopped.
    CUDA_VISIBLE_DEVICES="$GPU" NAS_GPUS="" NAS_TARGET_BUDGET="$T" NAS_METHOD="$METHOD" \
        NAS_TASK_CATEGORY="RULER_ALL_B${T}" \
        setsid nohup "$PYTHON_BIN" eval_top_configs_ruler.py "RULER_ALL_B${T}" --method "$METHOD" \
        --all_rows --sample_ratio 1.0 --save_predictions --output_file "$snap" \
        > "sravanth_logs/EVAL_RULER_B${T}_${METHOD}_all500_${DATE}.log" 2>&1 &
    echo "B${T}: EVAL LAUNCHED on GPU ${GPU} (log sravanth_logs/EVAL_RULER_B${T}_${METHOD}_all500_${DATE}.log)"
}

check=0
while true; do
    done_count=0
    summary=""
    for i in "${!TARGETS[@]}"; do
        T="${TARGETS[$i]}"; GPU="${GPUS[$i]}"
        f="RULER_ALL_B${T}/${METHOD}/output.txt"
        case "${STATE[$T]}" in
        searching)
            [ -f "$f" ] || continue
            rows=$(awk 'NF>=34' "$f" | wc -l)
            best=$(awk 'NF>=34 {print $NF}' "$f" | sort -g | head -1)
            [ -z "$best" ] && continue
            score=$(awk "BEGIN{printf \"%.2f\", -1*$best}")
            summary="${summary}B${T}:${rows}ev/best ${score}  "
            if [ "${BEST[$T]:-}" != "$best" ]; then
                [ -n "${BEST[$T]:-}" ] && echo "B${T}: new best ${score} @ ${rows} evals"
                BEST[$T]="$best"; ROWS_AT_BEST[$T]=$rows
                continue
            fi
            # Staleness only counts AFTER the 64-point init phase: the guided
            # search must get at least STABLE_EVALS of its own evaluations.
            # (Anchors at evals 1-7 otherwise trip the trigger during the
            # random LHS phase, stopping the search before BO ever runs.)
            base=${ROWS_AT_BEST[$T]}
            [ "$base" -lt 64 ] && base=64
            stale=$((rows - base))
            [ "$stale" -lt 0 ] && stale=0
            pid=$(lamp_pid_for_target "$T" || true)
            if [ "$stale" -ge "$STABLE_EVALS" ] || [ "$rows" -ge "$HARD_CAP" ] || [ -z "$pid" ]; then
                reason="stable ${stale}"; [ "$rows" -ge "$HARD_CAP" ] && reason="hard cap"
                [ -z "$pid" ] && reason="LAMP died"
                echo "B${T}: stopping search (${reason}, ${rows} evals, best ${score})"
                [ -n "$pid" ] && kill "$pid" 2>/dev/null
                sleep 45
                build_snapshot_and_eval "$T" "$GPU"
                STATE[$T]="evaluating"
            fi
            ;;
        evaluating)
            log="sravanth_logs/EVAL_RULER_B${T}_${METHOD}_all500_${DATE}.log"
            if grep -q "Results written" "$log" 2>/dev/null; then
                echo "B${T}: EVAL COMPLETE — $(grep -E 'mean_score' "$log" | tail -4 | tr '\n' ' ')"
                STATE[$T]="done"
            elif grep -qE "Traceback|CUDA out of memory" "$log" 2>/dev/null; then
                echo "B${T}: EVAL FAILED — check ${log}"
                STATE[$T]="done"
            fi
            ;;
        done) done_count=$((done_count+1));;
        esac
    done
    [ "$done_count" -eq 3 ] && { echo "ALL SLICES SEARCHED AND EVALUATED"; exit 0; }
    [ $((check % 6)) -eq 0 ] && [ -n "$summary" ] && echo "heartbeat: ${summary}"
    check=$((check+1))
    sleep "$CHECK_INTERVAL"
done
