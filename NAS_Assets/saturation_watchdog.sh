#!/bin/bash
# Watches the 3 concurrently-running LongBench slice-NAS category chains
# (SINGLE_DOCUMENT_QA/GPU0, MULTI_DOCUMENT_QA/GPU1, CODE/GPU2) and kills a
# target's LAMP.py process once its Pareto front stops improving, so the
# category's sequential for-loop (128->256->512->1024) moves on to the next
# target instead of running indefinitely.
#
# Saturation rule: best f2-so-far (f2 = -task_score, in output.txt's last
# column) hasn't improved in the last PATIENCE evaluated rows.
#
# v2 fixed a bug where a RESUMED target's pre-existing history could look
# "saturated" instantly (fixed via per-file baselines).
#
# v3 (this version) fixes a second, subtler bug found in production: state
# was keyed by "most recently modified output.txt", found via `ls -t`. When a
# target finishes and the loop launches the NEXT target, that new target's
# process needs time to load the model before writing its first row -- during
# that gap its output.txt doesn't exist yet, so `ls -t` kept reporting the
# OLD (now-frozen, already-past-patience) file as "active". Since that old
# file's baseline was already established and its score frozen (not
# improving, because nothing is writing to it anymore), the very next poll
# would immediately declare "SATURATED" again and kill whatever process is
# CURRENTLY on that GPU -- the brand-new next-target process -- often before
# it ever wrote a single row. Confirmed in production: CODE_B512 and
# CODE_B1024 were both killed this way, 0 rows each, total loss.
#
# Fix: key all state by the LAMP.py process's actual live NAS_TASK_CATEGORY
# (read from /proc/<pid>/environ), not by file mtime. A category change is
# detected the instant the new process exists, regardless of whether its
# output.txt has been created yet -- eliminating the race entirely.
#
# Usage: nohup bash saturation_watchdog.sh > sravanth_logs/SATURATION_WATCHDOG.log 2>&1 &

set -u
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# v5: PATIENCE=15/MIN_ROWS=20 (v1-v4) were far too tight for a 32-dim
# continuous BO search -- confirmed in production several targets were
# declared "saturated" and killed after essentially no real search:
# MULTI_DOCUMENT_QA_B1024 at 24 genuine BO rows, CODE_B512 at exactly 20 (the
# bare minimum), SINGLE_DOCUMENT_QA_B1024 at 30, MULTI_DOCUMENT_QA_B512 at 49.
# 15 non-improving iterations is not a meaningful convergence signal this
# early in a 32-dim space. Raised both thresholds ~3x so BO gets a real
# chance to explore/exploit before any saturation verdict is trusted.
PATIENCE="${PATIENCE:-40}"
MIN_ROWS="${MIN_ROWS:-60}"
CHECK_INTERVAL="${CHECK_INTERVAL:-90}"

# Every LAMP.py launch -- fresh OR a restart on a file that already has old
# rows in it -- unconditionally writes its OWN new INIT_BATCH_SIZE-row random
# batch (7 anchor shapes + LHS, HFF_mod.call_init(): N=2*D, D=32 -> N=64)
# before any real BO iteration runs. output.txt is append-only (HFF_mod.py
# opens it 'a'), so on a restart this new random batch lands NOT at row 0 but
# right after whatever was already in the file. v4's floor -- baseline =
# max(observed_at_attach, INIT_BATCH_SIZE) -- only accounted for the
# fresh-file case (observed starts at 0); for a restart on an existing file
# (observed_at_attach > INIT_BATCH_SIZE already) it left the floor exactly at
# observed_at_attach, so the freshly-injected random batch that follows
# (rows [observed_at_attach, observed_at_attach+64)) was wrongly treated as
# immediately-real BO data -- the same class of bug v4 was meant to fix, just
# relocated to the middle of the file by a restart. Confirmed live: the
# SINGLE_DOCUMENT_QA_B512/MULTI_DOCUMENT_QA_B512/CODE_B256 restarts launched
# this morning all had baselines sitting inside their own fresh random batch.
# v6 fix: baseline is ALWAYS observed_at_attach + INIT_BATCH_SIZE (never
# max()) -- unconditionally skips past whatever new random batch THIS launch
# is about to write, regardless of what was already in the file. Slightly
# conservative for a genuinely brand-new file (may skip a few extra
# already-real rows if the watchdog's poll lands mid-batch), but never
# undershoots -- and undershooting is the failure mode that actually costs
# real search data.
INIT_BATCH_SIZE="${INIT_BATCH_SIZE:-64}"

CATEGORIES=(SINGLE_DOCUMENT_QA MULTI_DOCUMENT_QA CODE)
GPUS=(0 1 2)

declare -A BASELINE_ROWS      # task_category -> row count when first observed
declare -A BASELINE_FILE      # task_category -> the output.txt path for that category (fixed once known)

echo "$(date '+%Y-%m-%d %H:%M:%S') watchdog v6 started: PATIENCE=$PATIENCE MIN_ROWS=$MIN_ROWS CHECK_INTERVAL=${CHECK_INTERVAL}s"

find_lamp_pid_and_category_for_gpu() {
    local gpu="$1"
    for pid in $(pgrep -f "LAMP\.py"); do
        if [ -r "/proc/$pid/environ" ]; then
            local env_dump
            env_dump=$(tr '\0' '\n' < "/proc/$pid/environ" 2>/dev/null)
            if echo "$env_dump" | grep -qx "CUDA_VISIBLE_DEVICES=$gpu"; then
                local cat
                cat=$(echo "$env_dump" | grep "^NAS_TASK_CATEGORY=" | cut -d= -f2-)
                echo "$pid|$cat"
                return
            fi
        fi
    done
}

while true; do
    for i in "${!CATEGORIES[@]}"; do
        CAT="${CATEGORIES[$i]}"
        GPU="${GPUS[$i]}"

        RESULT=$(find_lamp_pid_and_category_for_gpu "$GPU")
        [ -z "$RESULT" ] && continue   # no LAMP.py currently on this GPU (between targets, or chain finished)

        LAMP_PID="${RESULT%%|*}"
        TASK_CAT="${RESULT##*|}"
        [ -z "$TASK_CAT" ] && continue

        # New task category since we last looked? (Re)establish baseline fresh.
        if [ -z "${BASELINE_ROWS[$TASK_CAT]+x}" ]; then
            ACTIVE_FILE=$(ls -t ${TASK_CAT}/snapkv/output.txt 2>/dev/null | head -1)
            if [ -z "$ACTIVE_FILE" ]; then
                # Process exists (model loading) but hasn't written output.txt yet -- wait.
                continue
            fi
            TOTAL_ROWS=$(wc -l < "$ACTIVE_FILE" 2>/dev/null || echo 0)
            EFFECTIVE_BASELINE=$((TOTAL_ROWS + INIT_BATCH_SIZE))
            BASELINE_ROWS["$TASK_CAT"]=$EFFECTIVE_BASELINE
            BASELINE_FILE["$TASK_CAT"]="$ACTIVE_FILE"
            echo "$(date '+%Y-%m-%d %H:%M:%S') [$CAT/$TASK_CAT] new target attached (pid $LAMP_PID), file=$ACTIVE_FILE, observed=$TOTAL_ROWS rows, effective baseline=$EFFECTIVE_BASELINE (=observed+INIT_BATCH_SIZE=$INIT_BATCH_SIZE -- skips past this launch's own fresh random init batch, wherever in the file it lands)"
            continue
        fi

        ACTIVE_FILE="${BASELINE_FILE[$TASK_CAT]}"
        BASELINE=${BASELINE_ROWS[$TASK_CAT]}
        TOTAL_ROWS=$(wc -l < "$ACTIVE_FILE" 2>/dev/null || echo 0)
        NEW_ROWS=$((TOTAL_ROWS - BASELINE))
        if [ "$NEW_ROWS" -lt "$MIN_ROWS" ]; then
            continue
        fi

        VERDICT=$(python3 -c "
import numpy as np
d = np.loadtxt('$ACTIVE_FILE')
if d.ndim == 1:
    d = d.reshape(1, -1)
d = d[$BASELINE:]
n = len(d)
if n < $MIN_ROWS:
    print('TOO_EARLY')
else:
    f2 = d[:, -1]
    best_so_far = np.minimum.accumulate(f2)
    current_best = best_so_far[-1]
    ref_idx = max(0, n - 1 - $PATIENCE)
    reference_best = best_so_far[ref_idx]
    if current_best >= reference_best - 1e-9:
        print(f'SATURATED best={current_best:.4f} new_rows={n}')
    else:
        print(f'IMPROVING best={current_best:.4f} new_rows={n}')
" 2>&1)

        case "$VERDICT" in
            SATURATED*)
                echo "$(date '+%Y-%m-%d %H:%M:%S') [$CAT/$TASK_CAT] $VERDICT (baseline=$BASELINE) -- killing LAMP.py pid $LAMP_PID (moving to next target)"
                kill -TERM "$LAMP_PID" 2>/dev/null
                sleep 5
                kill -0 "$LAMP_PID" 2>/dev/null && kill -KILL "$LAMP_PID" 2>/dev/null
                unset "BASELINE_ROWS[$TASK_CAT]"
                unset "BASELINE_FILE[$TASK_CAT]"
                ;;
            IMPROVING*)
                echo "$(date '+%Y-%m-%d %H:%M:%S') [$CAT/$TASK_CAT] $VERDICT (baseline=$BASELINE) -- still improving, letting it continue"
                ;;
            TOO_EARLY)
                :
                ;;
            *)
                echo "$(date '+%Y-%m-%d %H:%M:%S') [$CAT/$TASK_CAT] WARN: could not evaluate saturation: $VERDICT"
                ;;
        esac
    done
    sleep "$CHECK_INTERVAL"
done
