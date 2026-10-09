"""
A5 (calibration-vs-test gap) and B4 (where NAS does/doesn't beat uniform) from
analysis_outputs/cells.csv. Writes markdown tables to
analysis_outputs/A5_B4_tables.md and prints them.
"""

import csv
import os
from collections import defaultdict
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(HERE)), "ICLR_Final_Results", "analysis_outputs")
LABELS = ["uniform", "heuristic", "winner", "random", "bo"]


def kendall_tau(a, b):
    conc = disc = 0
    for i, j in combinations(range(len(a)), 2):
        s = (a[i] - a[j]) * (b[i] - b[j])
        conc += s > 0
        disc += s < 0
    n = conc + disc
    return (conc - disc) / n if n else float("nan")


def load_cells(with_step3_winner=False):
    """with_step3_winner: also include the supplementary floor-clean Step-3 winner rows that
    collect_cells.py adds to cells whose search row 6 was not a genuine winner seed (B4 only;
    they have no calibration score so A5 must not see them)."""
    rows = list(csv.DictReader(open(os.path.join(OUT_DIR, "cells.csv"))))
    five = {(r["benchmark"], r["category"], r["budget"], r["method"]) for r in rows if r["source"] != "step3"}
    cells = defaultdict(list)
    for r in rows:
        if r["source"] == "step3":
            if not (with_step3_winner and (r["benchmark"], r["category"], r["budget"], r["method"]) in five):
                continue
            r["calib_score"] = float("nan")
        else:
            r["calib_score"] = float(r["calib_score"])
        r["full_score"] = float(r["full_score"])
        cells[(r["benchmark"], r["category"], int(r["budget"]), r["method"], int(r["era"]))].append(r)
    return dict(sorted(cells.items()))


def a5(cells):
    out = ["## A5 — Calibration-vs-test gap\n",
           "Calibration = score during search (10% subsample, `NAS_SAMPLE_RATIO=0.1`); "
           "test = full-data (`sample_ratio=1.0`) re-eval of the same config.\n",
           "| Benchmark | Category | Budget | Method | Floor | Mean gap (calib − test) | "
           "Kendall τ (calib vs test ranking) | Calib-picked config | Its test score | "
           "Test-best config | Its test score | Regret |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    agg = defaultdict(lambda: {"gap": [], "tau": [], "hit": 0, "n": 0, "regret": []})
    for (bm, cat, b, meth, era), rs in cells.items():
        gaps = [r["calib_score"] - r["full_score"] for r in rs]
        tau = kendall_tau([r["calib_score"] for r in rs], [r["full_score"] for r in rs])
        by_calib = max(rs, key=lambda r: r["calib_score"])
        by_test = max(rs, key=lambda r: r["full_score"])
        regret = by_test["full_score"] - by_calib["full_score"]
        out.append(f"| {bm} | {cat} | {b} | {meth} | {era} | {sum(gaps)/len(gaps):+.2f} | "
                   f"{tau:+.2f} | {by_calib['label']} | {by_calib['full_score']:.2f} | "
                   f"{by_test['label']} | {by_test['full_score']:.2f} | {regret:.2f} |")
        a = agg[(bm, meth)]
        a["gap"] += gaps
        a["tau"].append(tau)
        a["hit"] += by_calib is by_test
        a["n"] += 1
        a["regret"].append(regret)
    out += ["", "**Aggregate**", "",
            "| Benchmark | Method | Cells | Mean gap | Mean Kendall τ | Calib picks test-best | Mean regret |",
            "|---|---|---|---|---|---|---|"]
    for (bm, meth), a in sorted(agg.items()):
        out.append(f"| {bm} | {meth} | {a['n']} | {sum(a['gap'])/len(a['gap']):+.2f} | "
                   f"{sum(a['tau'])/len(a['tau']):+.2f} | {a['hit']}/{a['n']} | "
                   f"{sum(a['regret'])/len(a['regret']):.2f} |")
    return out


def b4(cells):
    out = ["", "## B4 — NAS vs uniform, per cell (full-data scores)\n",
           "| Benchmark | Category | Budget | Method | Floor | Uniform | Best non-uniform | "
           "Best label | Δ vs uniform | NAS wins? |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    label_best = defaultdict(int)
    label_gain = defaultdict(list)
    bm_best = defaultdict(lambda: defaultdict(int))
    bm_gain = defaultdict(lambda: defaultdict(list))
    wins = losses = 0
    for (bm, cat, b, meth, era), rs in cells.items():
        uni = next((r for r in rs if r["label"] == "uniform"), None)
        if uni is None:
            continue
        others = [r for r in rs if r["label"] != "uniform"]
        best = max(others, key=lambda r: r["full_score"])
        d = best["full_score"] - uni["full_score"]
        wins += d > 0
        losses += d <= 0
        overall = max(rs, key=lambda r: r["full_score"])
        label_best[overall["label"]] += 1
        bm_best[bm][overall["label"]] += 1
        for r in others:
            label_gain[r["label"]].append(r["full_score"] - uni["full_score"])
            bm_gain[bm][r["label"]].append(r["full_score"] - uni["full_score"])
        out.append(f"| {bm} | {cat} | {b} | {meth} | {era} | {uni['full_score']:.2f} | "
                   f"{best['full_score']:.2f} | {best['label']} | {d:+.2f} | "
                   f"{'yes' if d > 0 else '**no**'} |")
    out += ["", f"**NAS beats uniform in {wins}/{wins + losses} cells.**", "",
            "**Which 5-way component is the overall best, and its mean gain over uniform**", "",
            "| Component | # cells where it is overall best | Mean Δ vs uniform (all cells it appears in) | # cells |",
            "|---|---|---|---|"]
    for lab in LABELS:
        g = label_gain.get(lab, [])
        mean = f"{sum(g)/len(g):+.2f}" if g else "—"
        out.append(f"| {lab} | {label_best.get(lab, 0)} | {mean} | {len(g) if g else '—'} |")
    for bm in sorted(bm_best):
        out += ["", f"**Same, {bm} only**", "",
                "| Component | # cells overall best | Mean Δ vs uniform | Median Δ vs uniform |",
                "|---|---|---|---|"]
        for lab in LABELS:
            g = sorted(bm_gain[bm].get(lab, []))
            mean = f"{sum(g)/len(g):+.2f}" if g else "—"
            med = f"{g[len(g)//2]:+.2f}" if g else "—"
            out.append(f"| {lab} | {bm_best[bm].get(lab, 0)} | {mean} | {med} |")
    return out


def main():
    cells = load_cells()
    lines = a5(cells) + b4(load_cells(with_step3_winner=True))
    path = os.path.join(OUT_DIR, "A5_B4_tables.md")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n-> {path}")


if __name__ == "__main__":
    main()
