#!/bin/bash
# Watch the RULER_ALL NAS run; when the Pareto front stabilizes (no change for
# STABLE_EVALS consecutive evaluations) or HARD_CAP total evaluations is hit,
# stop LAMP and launch the parallel held-out evaluation of the front.
#
# Emits one line per notable event (front change, 3h heartbeat, trigger).
# Env overrides: CHECK_INTERVAL (s), STABLE_EVALS, HARD_CAP, WATCH_DRY_CHECKS
# (exit after N checks without ever killing/launching — for testing).

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="${PYTHON_BIN:-/home/test/miniconda/envs/cakekv/bin/python}"
export PYTHONNOUSERSITE=1
OUTPUT_TXT="RULER_ALL/snapkv/output.txt"
CHECK_INTERVAL="${CHECK_INTERVAL:-1800}"
STABLE_EVALS="${STABLE_EVALS:-40}"
HARD_CAP="${HARD_CAP:-350}"
WATCH_DRY_CHECKS="${WATCH_DRY_CHECKS:-}"

front_of() {
    "$PYTHON_BIN" -c "
import numpy as np
try:
    d = np.loadtxt('$OUTPUT_TXT')
except Exception:
    print('EMPTY'); raise SystemExit
d = d.reshape(1, -1) if d.ndim == 1 else d
f = d[:, -2:]
p = set()
for i, (b, s) in enumerate(f):
    if not any((f[j,0] <= b and f[j,1] < s) or (f[j,0] < b and f[j,1] <= s)
               for j in range(len(f)) if j != i):
        p.add((round(float(b), 1), round(float(s), 4)))
print(';'.join(f'{b}:{s}' for b, s in sorted(p)))
" 2>/dev/null || echo "EMPTY"
}

last_front=""
rows_at_change=0
check=0
trigger_reason=""

while true; do
    rows=$( (wc -l < "$OUTPUT_TXT") 2>/dev/null || echo 0)

    if ! pgrep -f "[L]AMP.py" >/dev/null; then
        echo "WARNING: LAMP process not running (rows=$rows) — proceeding to eval on current front"
        trigger_reason="lamp_died"
        break
    fi

    front=$(front_of)
    if [ "$front" != "$last_front" ]; then
        n_pts=$(echo "$front" | tr ';' '\n' | grep -c ':' || true)
        echo "front changed @ ${rows} evals (${n_pts} Pareto points)"
        last_front="$front"
        rows_at_change=$rows
    else
        stale=$((rows - rows_at_change))
        if [ $((check % 6)) -eq 0 ]; then
            echo "heartbeat: ${rows} evals, front stable for ${stale}"
        fi
        if [ "$stale" -ge "$STABLE_EVALS" ]; then
            echo "TRIGGER: front stable for ${stale} evals (${rows} total)"
            trigger_reason="stable"
            break
        fi
    fi

    if [ "$rows" -ge "$HARD_CAP" ]; then
        echo "TRIGGER: hard cap ${HARD_CAP} evaluations reached (${rows})"
        trigger_reason="hard_cap"
        break
    fi

    check=$((check + 1))
    if [ -n "$WATCH_DRY_CHECKS" ] && [ "$check" -ge "$WATCH_DRY_CHECKS" ]; then
        echo "dry run: ${check} checks done, exiting without action"
        exit 0
    fi
    sleep "$CHECK_INTERVAL"
done

if [ -n "$WATCH_DRY_CHECKS" ]; then
    echo "dry run: trigger (${trigger_reason}) reached, exiting without action"
    exit 0
fi

# ─── Act: stop the search, free GPUs, launch parallel held-out evals ─────────
pkill -f "[L]AMP.py" 2>/dev/null || true
sleep 20
for i in $(seq 1 30); do
    busy=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | awk '$1>2000{c++} END{print c+0}')
    [ "$busy" -eq 0 ] && break
    sleep 10
done

DATE=$(date +%d_%m_%Y)
nohup bash run_eval_ruler_parallel.sh > "sravanth_logs/EVAL_RULER_ALL_parallel_${DATE}.log" 2>&1 &
echo "EVAL LAUNCHED: search stopped (${trigger_reason}), 3 held-out shards running — log sravanth_logs/EVAL_RULER_ALL_parallel_${DATE}.log"
exit 0
