"""
Collect every full-data-evaluated config into one tidy table.

For each <CATEGORY>_B<T>/<method>/top_configs/ that has an eval_results.csv
produced from a snapshot of that cell's own Step-4 output.txt (five_way_snapshot,
slice_eval_snapshot, bo_best_snapshot), match each evaluated row back to its
row index in output.txt and label it by position:
  0 uniform | 1-5 heuristic | 6 winner | 7-63 random | 64+ bo
Row 6 is only a genuine winner seed if the search was launched with NAS_ANCHOR_FILE; the
winner is whichever initial-design row (1-63) correlates (r > 0.9) with the cell's winner
anchor (row 9 in RULER SnapKV B128); row 6 without a match is labelled "heuristic". If no row
matches, the floor-64 rescaled winner is added as a source="step3" label="winner" row from
eval_results_winner_floor64.csv (else the floor-clean Step-3 backup), if available.
Rows are paired with their calibration score (-f2 in output.txt, computed at
NAS_SAMPLE_RATIO during search) and full-data score (eval_results.csv).

Cells whose eval_results.csv is a Step-3 fixed-budget eval (uniform + rescaled
winner only, no Step-4 output.txt rows) are also emitted with labels uniform /
winner and no calibration score.

Output: ICLR_Final_Results/analysis_outputs/cells.csv
"""

import csv
import datetime
import glob
import os
import re

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
NAS = os.path.dirname(HERE)
OUT_DIR = os.path.join(os.path.dirname(NAS), "ICLR_Final_Results", "analysis_outputs")
FLOOR_SWITCH = datetime.datetime(2026, 9, 1)  # last 16-floor file Aug 25, first 64-floor Sep 7
META_COLS = {"arch", "avg_budget", "nas_f2", "mean_score", "budgets"}


def label_for(idx):
    if idx == 0:
        return "uniform"
    if idx <= 5:
        return "heuristic"
    if idx == 6:
        return "winner"
    if idx <= 63:
        return "random"
    return "bo"


def anchor_for(benchmark, category, method):
    if benchmark == "longbench":
        p = os.path.join(NAS, "anchors", f"anchor_longbench_{category}_{method}.txt")
    else:
        p = os.path.join(NAS, "anchor_1756_budgets.txt" if method == "snapkv"
                         else os.path.join("anchors", "anchor_h2o_2180.txt"))
    return np.loadtxt(p) if os.path.isfile(p) else None


def parse_budgets(s):
    s = s.strip()
    import ast
    return np.array(ast.literal_eval(s) if s.startswith("[") else [int(v) for v in s.split()], float)


def era_of(path):
    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
    return 16 if mtime < FLOOR_SWITCH else 64


def read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    out_rows = []
    for tc in sorted(glob.glob(os.path.join(NAS, "*_B*", "*", "top_configs"))):
        cell_dir = os.path.dirname(tc)
        method = os.path.basename(cell_dir)
        cat_b = os.path.basename(os.path.dirname(cell_dir))
        m = re.match(r"(.+)_B(\d+)$", cat_b)
        if not m or "evolkv" in method:
            continue
        category, budget = m.group(1), int(m.group(2))
        benchmark = "ruler" if category.startswith("RULER") else "longbench"
        csv_path = os.path.join(tc, "eval_results.csv")
        if not os.path.isfile(csv_path):
            continue
        evals = read_csv(csv_path)
        datasets = [k for k in evals[0].keys() if k not in META_COLS]
        era = 64 if benchmark == "longbench" else era_of(csv_path)

        snap = None
        for name in ("five_way_snapshot.txt", "slice_eval_snapshot.txt"):
            p = os.path.join(tc, name)
            if os.path.isfile(p) and len(np.atleast_2d(np.loadtxt(p))) == len(evals):
                snap = p
                break
        out_txt = os.path.join(cell_dir, "output.txt")

        if snap and os.path.isfile(out_txt):
            source = os.path.basename(snap).replace("_snapshot.txt", "")
            srows = np.atleast_2d(np.loadtxt(snap))
            orows = np.atleast_2d(np.loadtxt(out_txt))
            row0_uniform = bool(np.allclose(orows[0, :-2], 0.5))
            anchor = anchor_for(benchmark, category, method)
            recs = []
            for ev, srow in zip(evals, srows):
                hits = np.where(np.all(np.isclose(orows, srow, atol=1e-9), axis=1))[0]
                idx = int(hits[0]) if len(hits) else -1
                r = None
                if anchor is not None and idx >= 0:
                    b = parse_budgets(ev["budgets"])
                    r = np.corrcoef(b, anchor)[0, 1] if b.std() > 0 else 0.0
                label = label_for(idx) if idx >= 0 else "unmatched"
                # The winner seed is whichever initial-design row (1-63) matches the anchor shape (r > 0.9);
                # usually row 6, but it was row 9 in RULER SnapKV B128. Row 6 without a match is a heuristic.
                if anchor is not None and 1 <= idx <= 63 and r is not None and r > 0.9 and label != "winner":
                    print(f"[winner-seed] {category} B{budget} {method}: row {idx} matches the anchor (r={r:+.2f}) "
                          f"-> labelled winner (was {label})")
                    label = "winner"
                elif label == "winner" and anchor is not None and not (r is not None and r > 0.9):
                    print(f"[winner-seed] {category} B{budget} {method}: row 6 r={r:+.2f} to anchor "
                          f"-> labelled heuristic (search launched without the anchor)")
                    label = "heuristic"
                recs.append((ev, srow, idx, label))
            winner_seed_ok = anchor is None or any(lab == "winner" for _, _, _, lab in recs)
            for ev, srow, idx, label in recs:
                out_rows.append(dict(
                    benchmark=benchmark, category=category, budget=budget, method=method,
                    source=source, era=era, output_rows=len(orows), row0_uniform=row0_uniform,
                    row_idx=idx, label=label,
                    calib_score=round(-float(srow[-1]), 4),
                    full_score=round(float(ev["mean_score"]), 4),
                    per_dataset=";".join(f"{d}={ev[d]}" for d in datasets),
                    budgets=ev["budgets"]))
            f64 = os.path.join(tc, "eval_results_winner_floor64.csv")
            bk = os.path.join(tc, "eval_results_PRE5WAY_step3_backup.csv")
            row6 = os.path.join(tc, "eval_results_winner_row6.csv")  # winner seed scored separately (old 4-way scheme skipped it)
            supp = next((x for x in (f64, row6, bk) if os.path.isfile(x)), bk)
            if not winner_seed_ok and os.path.isfile(supp):
                for ev in read_csv(supp):
                    b = parse_budgets(ev["budgets"])
                    if b.std() > 0 and b.min() >= 64:
                        out_rows.append(dict(
                            benchmark=benchmark, category=category, budget=budget, method=method,
                            source="step3", era=era, output_rows=0, row0_uniform="",
                            row_idx="", label="winner", calib_score="",
                            full_score=round(float(ev["mean_score"]), 4),
                            per_dataset=";".join(f"{d}={ev[d]}" for d in datasets),
                            budgets=ev["budgets"]))
                        print(f"[winner-seed] {category} B{budget} {method}: added floor-clean winner "
                              f"{float(ev['mean_score']):.2f} from {os.path.basename(supp)}")
                    elif b.std() > 0:
                        print(f"[winner-seed] {category} B{budget} {method}: Step-3 winner NOT floor-clean "
                              f"(min layer {int(b.min())}) -> no winner row for this cell")
            elif not winner_seed_ok:
                print(f"[winner-seed] {category} B{budget} {method}: no winner source -> no winner row")
        elif len(evals) <= 2:
            for i, ev in enumerate(evals):
                out_rows.append(dict(
                    benchmark=benchmark, category=category, budget=budget, method=method,
                    source="step3", era=era, output_rows=0, row0_uniform="",
                    row_idx="", label="uniform" if parse_budgets(ev["budgets"]).std() == 0 else "winner",
                    calib_score="", full_score=round(float(ev["mean_score"]), 4),
                    per_dataset=";".join(f"{d}={ev[d]}" for d in datasets),
                    budgets=ev["budgets"]))

    path = os.path.join(OUT_DIR, "cells.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)
    print(f"{len(out_rows)} rows -> {path}")


if __name__ == "__main__":
    main()
