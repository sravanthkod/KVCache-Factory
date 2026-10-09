"""
Build the 5-way Step-4 snapshot (uniform / best_heuristic / best_winner /
best_random / best_bo) from any NAS output.txt file.

Row layout produced by LAMP.py's slice-mode init (see LAMP.py:170-207),
identical for every method/benchmark:
    row 0        uniform at the target budget
    rows 1-5     5 pure shape heuristics (ramp asc/desc, triangle mid/edge, alternating)
    row 6        winner-seed (the unconstrained-search winner's shape, rescaled
                 to this budget) -- only a genuine "winner" if NAS_ANCHOR_FILE
                 was set at launch, otherwise it's a 2nd alternating heuristic
    rows 7-63    57 LHS random-allocation points
    rows 64+     genuine adaptive BO-guided search iterations

`watch_slices_and_eval.sh`'s automated snapshot builder only produces a 4-way
split (uniform_anchor / best_heuristic=argmin(rows[1:7]) / best_random /
best_overall=argmin(ALL rows)) -- it lumps the winner-seed into "heuristic"
and doesn't isolate the BO phase (best_overall can coincide with the
uniform/heuristic/random pick if BO never improved on them, silently mislabeled
as "BO" in downstream tables). This script produces the correct isolated
5-way split, matching the manual analysis already done for AdaKV's RULER
results (see ICLR_Final_Results/RULER_Results.md) -- so the same treatment
can be applied consistently to any method/category/budget's output.txt,
without needing to redo any search or re-run any eval pipeline (this only
re-slices data that's already on disk).

Usage:
    python3 select_5way_snapshot.py <output_txt_path> [--out SNAPSHOT_PATH]

    # Then feed the snapshot into the existing full-data eval scripts:
    python3 eval_top_configs_ruler.py <TASK_CATEGORY> --method <method> \\
        --all_rows --sample_ratio 1.0 --output_file <SNAPSHOT_PATH>
    # or, for LongBench:
    python3 eval_top_configs_longbench.py <TASK_CATEGORY> --method <method> \\
        --all_rows --sample_ratio 1.0 --output_file <SNAPSHOT_PATH>

If <output_txt_path> has fewer than 65 rows (no BO phase yet) or fewer than
8 rows (no random phase yet), the corresponding label(s) are simply omitted
-- this is safe to run at any point during a search, not just after it's
fully converged.
"""

import argparse
import os

import numpy as np


def select_5way(rows):
    """Return a list of (label, row_index, score) for the 5-way split.

    `rows` is the full (N, D+2) output.txt array (D x-values + f1 + f2).
    Score reported is -f2 (i.e. the actual task score, since f2 = -score).
    Duplicate row indices are NOT collapsed here -- caller decides whether
    to dedupe (matches build_snapshot_and_eval's existing behavior of
    keeping first-seen only).
    """
    n = len(rows)
    f2 = rows[:, -1]
    picks = []

    picks.append(("uniform", 0))

    heuristic_end = min(6, n)  # rows 1-5
    if n > 1:
        i = 1 + int(np.argmin(f2[1:heuristic_end]))
        picks.append(("best_heuristic", i))

    if n > 6:
        picks.append(("best_winner", 6))

    random_end = min(64, n)  # rows 7-63
    if n > 7:
        i = 7 + int(np.argmin(f2[7:random_end]))
        picks.append(("best_random", i))

    if n > 64:
        i = 64 + int(np.argmin(f2[64:]))
        picks.append(("best_bo", i))

    return [(label, idx, float(-f2[idx])) for label, idx in picks]


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("output_txt", help="Path to a NAS output.txt file (any method/benchmark)")
    parser.add_argument("--out", default=None,
                         help="Where to write the snapshot (default: "
                              "<dir of output_txt>/top_configs/five_way_snapshot.txt)")
    parser.add_argument("--dedupe", action="store_true",
                         help="Drop rows that repeat an earlier pick's index "
                              "(e.g. if best_heuristic and best_winner are the "
                              "same row) -- matches build_snapshot_and_eval's "
                              "existing behavior. Default: keep all 5 rows even "
                              "if some indices repeat.")
    args = parser.parse_args()

    rows = np.loadtxt(args.output_txt)
    if rows.ndim == 1:
        rows = rows.reshape(1, -1)

    picks = select_5way(rows)

    print(f"{len(rows)} total rows in {args.output_txt}")
    seen = set()
    kept_rows = []
    kept_labels = []
    for label, idx, score in picks:
        dup = idx in seen
        seen.add(idx)
        tag = " (dup of earlier pick)" if dup and args.dedupe else ""
        print(f"  {label:15s} row {idx:4d} (1-based {idx+1:4d})  score={score:.4f}{tag}")
        if args.dedupe and dup:
            continue
        kept_rows.append(rows[idx])
        kept_labels.append(label)

    out_path = args.out
    if out_path is None:
        # output.txt lives at <category>/<method>/output.txt -- top_configs/
        # is a SIBLING of output.txt inside that same <method> dir, not one
        # level up (that would land in <category>/top_configs/, skipping the
        # method dir entirely -- confirmed as a real bug: eval scripts
        # expecting <category>/<method>/top_configs/five_way_snapshot.txt
        # couldn't find it because this used to write one directory too high).
        out_dir = os.path.join(os.path.dirname(os.path.abspath(args.output_txt)), "top_configs")
        out_dir = os.path.normpath(out_dir)
        out_path = os.path.join(out_dir, "five_way_snapshot.txt")

    # Always ensure the destination dir exists, whether --out was explicit
    # (e.g. run_5way_eval.sh always passes one) or defaulted above -- a
    # category that's never had an eval run yet won't have top_configs/ yet.
    out_dir = os.path.dirname(os.path.abspath(out_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    np.savetxt(out_path, np.array(kept_rows))
    print(f"\nWrote {len(kept_rows)} rows ({', '.join(kept_labels)}) -> {out_path}")
    print("Row order in the snapshot matches the label order printed above "
          "(minus any dedup drops) -- match eval_results.csv's 'arch' column "
          "back to these labels by position (arch 1 = first kept label, etc.)")


if __name__ == "__main__":
    main()
