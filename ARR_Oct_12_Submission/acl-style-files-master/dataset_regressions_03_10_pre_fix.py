#!/usr/bin/env python3
"""Dataset-level regressions hidden by LongBench category means: for every LongBench cell, compare MOSAIC's final
configuration (the better of Winner and NAS-refined on the category mean, as in three_way.py) with uniform on each
dataset of the category. Run directly to print the counts quoted in the paper."""
import csv
from pathlib import Path

import three_way as tw

RES = tw.RES
SEARCH = tw.SEARCH | {"winner"}


def parse(s):
    return {k: float(v) for k, v in (kv.split("=") for kv in s.split(";"))} if s else {}


def per_dataset():
    """{(method, category, budget): {'uniform': {ds: score}, 'final': {ds: score}, 'final_mean', 'uniform_mean'}}"""
    rows = {}  # key -> list of (label, mean, {ds: score})
    for r in csv.DictReader(open(RES / "analysis_outputs" / "cells.csv")):
        if r["benchmark"] != "longbench" or r["source"] == "step3":
            continue
        key = ({"snapkv": "SnapKV", "h2o": "H2O"}[r["method"]], r["category"], int(r["budget"]))
        rows.setdefault(key, []).append((r["label"], float(r["full_score"]), parse(r["per_dataset"])))
    ada = {}
    amap = {"Uniform": "uniform", "Winner (rescaled anchor)": "winner"}
    for r in csv.DictReader(open(RES / "ADAKV_RESULTS" / "data" / "longbench_slices_step3_4.csv")):
        k = ("AdaKV", r["category"], int(r["target_budget"]), r["arch_name"])
        ada.setdefault(k, [amap.get(r["arch_name"], "bo"), float(r["mean_score"]), {}])[2][r["dataset"]] = float(r["score"])
    for (m, c, b, _), v in ada.items():
        rows.setdefault((m, c, b), []).append(tuple(v))
    lmap = ["uniform", "heuristic", "winner", "random", "bo"]
    for cat in ["SINGLE_DOCUMENT_QA", "MULTI_DOCUMENT_QA", "CODE", "SUMMARIZATION"]:
        for d in (RES / "LLAMA_L2NORM_RESULTS" / cat).glob("B*"):
            rs = list(csv.DictReader(open(d / "eval_results.csv")))
            if len(rs) != 5:
                continue
            for r in rs:
                ds = {k: float(v) for k, v in r.items() if k not in ("arch", "avg_budget", "nas_f2", "mean_score", "budgets")}
                rows.setdefault(("L2Norm", cat, int(d.name[1:])), []).append((lmap[int(r["arch"]) - 1], float(r["mean_score"]), ds))
    out = {}
    for k, rs in rows.items():
        uni = [r for r in rs if r[0] == "uniform"]
        cand = [r for r in rs if r[0] in SEARCH]
        if not uni or not cand or not uni[0][2]:
            continue
        fin = max(cand, key=lambda r: r[1])
        out[k] = {"uniform": uni[0][2], "final": fin[2], "uniform_mean": uni[0][1], "final_mean": fin[1]}
    return out


if __name__ == "__main__":
    cells = per_dataset()
    n_reg, worst = 0, []
    for k, v in sorted(cells.items()):
        d = {ds: v["final"][ds] - v["uniform"][ds] for ds in v["uniform"] if ds in v["final"]}
        lo = min(d, key=d.get)
        if d[lo] < 0:
            n_reg += 1
            worst.append((d[lo], k, lo, v["final_mean"] - v["uniform_mean"]))
    print(f"{len(cells)} LongBench cells; final config below uniform on >=1 dataset in {n_reg}")
    print(f"  of which category mean still above uniform: {sum(m > 0 for _, _, _, m in worst)}")
    for w in sorted(worst)[:12]:
        print(f"  {w[0]:+6.2f} {w[1]} {w[2]} (category mean {w[3]:+.2f})")
