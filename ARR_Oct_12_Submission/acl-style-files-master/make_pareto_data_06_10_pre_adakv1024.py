#!/usr/bin/env python3
"""Write figures/data/pareto_*.dat for figures/figure_pareto.tex (Stage 2 full-data Pareto configs vs uniform)."""
import csv
import glob
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
KV = HERE.parents[1]
NAS = KV / "NAS_Assets"
ANA = KV / "ICLR_Final_Results" / "analysis_outputs"
ADA = KV / "ICLR_Final_Results" / "ADAKV_RESULTS" / "data"
OUT = HERE / "figures" / "data"
CATS = ["SINGLE_DOCUMENT_QA", "MULTI_DOCUMENT_QA", "CODE", "SUMMARIZATION", "RULER_ALL"]

nas = {}   # (cat, method) -> [(budget, score)] shaped Stage 2 configs, full data
uni = {}   # (cat, method) -> {budget: score} uniform allocation, full data


def budgets(s):
    return [int(float(x)) for x in re.split(r"[,\s]+", s.strip("[] ")) if x]


def add_stage2(cat, m, path, score_col):
    for r in csv.DictReader(open(path)):
        b, s = float(r["avg_budget"]), float(r[score_col])
        if len(set(budgets(r["budgets"]))) == 1:
            uni.setdefault((cat, m), {})[round(b)] = s
        else:
            nas.setdefault((cat, m), []).append((b, s))


# SnapKV / H2O Stage 2 (latest summary per category; Code and RULER use eval_results)
for cat in ["SINGLE_DOCUMENT_QA", "MULTI_DOCUMENT_QA", "SUMMARIZATION"]:
    for m in ["snapkv", "h2o"]:
        add_stage2(cat, m, sorted(glob.glob(str(NAS / cat / m / "top_configs" / "summary_*.csv")))[-1], "avg_score")
for m in ["snapkv", "h2o"]:
    add_stage2("CODE", m, NAS / "CODE" / m / "top_configs" / "eval_results.csv", "mean_score")
add_stage2("RULER_ALL", "snapkv", NAS / "RULER_ALL" / "snapkv" / "top_configs" / "eval_results_all500.csv", "mean_score")
# H2O RULER: only 4 front configurations were re-evaluated on full data, so this panel plots the CALIBRATION scores of every
# shaped configuration on the Stage 1 Pareto front (the caption says so). Rows: 32 x-values, avg budget, -calibration score.
def _h2o_ruler_calibration_front():
    rows = []
    for l in open(NAS / "RULER_ALL" / "h2o" / "output.txt"):
        v = l.split()
        if len(v) == 34:
            try:
                rows.append([float(t) for t in v])
            except ValueError:
                pass
    pts = []
    for i, r in enumerate(rows):
        if len(set(r[:32])) == 1:  # uniform allocation: drawn as the dashed line instead
            continue
        if any(q[32] <= r[32] and q[33] <= r[33] and (q[32] < r[32] or q[33] < r[33]) for q in rows):
            continue  # dominated (higher budget or lower score than some other configuration)
        pts.append((r[32], -r[33]))
    return sorted(set(pts))
nas[("RULER_ALL", "h2o")] = _h2o_ruler_calibration_front()

# SnapKV / H2O uniform at fixed budgets (B2 winner-transfer table: Category | Method | ... | Budget | Floor | Uniform)
rows = [l for l in (ANA / "B2_winner_transfer.md").read_text().splitlines() if l.startswith("| longbench") or l.startswith("| ruler")]
for l in rows:
    c = [x.strip() for x in l.strip("|").split("|")]
    if len(c) == 9:
        uni.setdefault((c[1], c[2]), {})[int(c[4])] = float(c[6])

# uniform budgets missing from B2 (cells with no winner evaluation, e.g. H2O RULER B2048): take them from cells.csv;
# a uniform allocation is the same configuration whatever the floor
for r in csv.DictReader(open(ANA / "cells.csv")):
    if r["label"] == "uniform":
        uni.setdefault((r["category"], r["method"]), {}).setdefault(int(r["budget"]), float(r["full_score"]))

# H2O RULER uniform at B64/B256/B512 (not in cells.csv): raw H2O uniform runs
import sys; sys.path.insert(0, str(Path(__file__).resolve().parent))
import h2o_ruler_uniform as _hru
for _b, _u in _hru.uniform().items():
    uni.setdefault(("RULER_ALL", "h2o"), {}).setdefault(_b, _u)

# AdaKV Stage 2 + uniform
seen = set()
for r in csv.DictReader(open(ADA / "longbench_step2_pareto_full_eval.csv")):
    k = (r["category"], float(r["avg_budget"]))
    if k in seen:
        continue
    seen.add(k)
    if r["type"] == "uniform":
        uni.setdefault((r["category"], "adakv"), {})[round(k[1])] = float(r["avg_score"])
    else:
        nas.setdefault((r["category"], "adakv"), []).append((k[1], float(r["avg_score"])))
for r in csv.DictReader(open(ADA / "longbench_slices_step3_4.csv")):
    if r["arch_name"] == "Uniform":
        uni.setdefault((r["category"], "adakv"), {})[int(r["target_budget"])] = float(r["mean_score"])
for r in csv.DictReader(open(ADA / "ruler_all_results.csv")):
    if r["stage"].startswith("step2"):
        if r["arch_name"] == "uniform":
            uni.setdefault(("RULER_ALL", "adakv"), {})[round(float(r["avg_budget"]))] = float(r["mean_score"])
        else:
            nas.setdefault(("RULER_ALL", "adakv"), []).append((float(r["avg_budget"]), float(r["mean_score"])))
    elif r["arch_name"] == "Uniform":
        uni.setdefault(("RULER_ALL", "adakv"), {})[int(r["target_budget"])] = float(r["mean_score"])

# L2Norm (Llama): Stage 2 + every uniform run (B64, five-way arch 1, RULER B4096); LongBench B2048 is a rescaled winner, skipped
L2R = KV / "ICLR_Final_Results" / "LLAMA_L2NORM_RESULTS"
for cat in CATS:
    add_stage2(cat, "l2norm", L2R / cat / "unconstrained" / "eval_results.csv", "mean_score")
    for d in (L2R / cat).glob("B*"):
        for r in csv.DictReader(open(d / "eval_results.csv")):
            if len(set(budgets(r["budgets"]))) == 1:
                uni.setdefault((cat, "l2norm"), {})[int(d.name[1:])] = float(r["mean_score"])

# Winner anchor actually used downstream: natural avg budget (B2 table for SnapKV/H2O; ADAKV_RESULTS.md anchors for AdaKV)
WINNER = {(c[1], c[2]): float(c[3]) for c in
          ([x.strip() for x in l.strip("|").split("|")] for l in rows) if len(c) == 9}
# L2Norm: the winner is the full-data-best shaped Stage 2 config (verified: every fixed-budget winner traces to it)
WINNER.update({(c, "l2norm"): max(nas[(c, "l2norm")], key=lambda p: p[1])[0] for c in CATS})
WINNER.update({("SINGLE_DOCUMENT_QA", "adakv"): 464, ("MULTI_DOCUMENT_QA", "adakv"): 188,
               ("CODE", "adakv"): 482, ("RULER_ALL", "adakv"): 2536})

OUT.mkdir(parents=True, exist_ok=True)
for (cat, m), pts in sorted(nas.items()):
    with open(OUT / f"pareto_{cat}_{m}_nas.dat", "w") as f:
        f.write("budget score\n" + "".join(f"{b:.1f} {s:.3f}\n" for b, s in sorted(pts)))
    wb = WINNER[(cat, m)]
    w = min(pts, key=lambda p: abs(p[0] - wb))
    assert abs(w[0] - wb) < 1, (cat, m, wb, w)
    bb = max(pts, key=lambda p: p[1])
    if w != bb:
        print(f"  NOTE {cat} {m}: winner used {w[1]:.2f}@{w[0]:.0f} != full-data best {bb[1]:.2f}@{bb[0]:.0f}")
    with open(OUT / f"pareto_{cat}_{m}_best.dat", "w") as f:  # ring = full-data-best Stage 2 configuration
        f.write(f"budget score\n{bb[0]:.1f} {bb[1]:.3f}\n")
    u = uni.get((cat, m), {})
    with open(OUT / f"pareto_{cat}_{m}_uni.dat", "w") as f:
        f.write("budget score\n" + "".join(f"{b} {u[b]:.3f}\n" for b in sorted(u)))
    print(f"{cat:20s} {m:7s} nas={len(pts):2d} ({min(p[0] for p in pts):.0f}-{max(p[0] for p in pts):.0f})  uniform budgets={sorted(u)}")
