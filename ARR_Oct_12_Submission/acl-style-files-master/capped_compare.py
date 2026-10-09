#!/usr/bin/env python3
"""Compute-matched EvolKV comparison: cap each SnapKV LongBench Stage 4 search at the GPU-hours EvolKV's direct search
used for the same cell, charging MOSAIC also for the full-data re-evaluation of the 3 candidates NAS-refined selects from
(best heuristic, best LHS point, best guided proposal). Reads cells.csv (row order = evaluation order), B1_search_cost.md,
the Stage 2 timing logs and the EvolKV full-data results. Run directly to print the table used in Appendix D."""
import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RES, NAS = ROOT / "ICLR_Final_Results", ROOT / "NAS_Assets"
INIT = 64          # Stage 4 initial design: rows 0-63 (uniform, heuristics, winner seed, LHS)
N_REEVAL = 3       # full-data re-evaluations needed to pick NAS-refined


def full_eval_hours():
    """Mean GPU-hours of one full-data evaluation, measured from the Stage 2 re-evaluation logs."""
    code = [float(t) for t in re.findall(r"time=([0-9.]+)s", (NAS / "eval_logs" / "CODE_22_07_2026.log").read_text())]
    sd = [float(r["eval_time_sec"]) for r in csv.DictReader(open(
        NAS / "SINGLE_DOCUMENT_QA" / "snapkv" / "top_configs" / "summary_20260722_143105.csv"))]
    return {"CODE": sum(code) / len(code) / 3600, "SINGLE_DOCUMENT_QA": sum(sd) / len(sd) / 3600}


def search_costs():
    """{(cat, B): (evolkv_gpuh, our_evals, our_gpuh)} from B1_search_cost.md."""
    out = {}
    for line in (RES / "analysis_outputs" / "B1_search_cost.md").read_text().splitlines():
        c = [x.strip() for x in line.strip("|").split("|")]
        if len(c) == 9 and c[0] in ("CODE", "SINGLE_DOCUMENT_QA"):
            num = lambda s: float(s.lstrip("~≈"))
            out[(c[0], int(c[1]))] = (num(c[4]), int(c[5]), num(c[7]))
    return out


def compute():
    fe, costs = full_eval_hours(), search_costs()
    cand = {}
    for r in csv.DictReader(open(RES / "analysis_outputs" / "cells.csv")):
        if r["method"] == "snapkv" and r["source"] == "five_way" and r["label"] in ("heuristic", "random", "bo"):
            cand.setdefault((r["category"], int(r["budget"])), []).append((int(r["row_idx"]), float(r["full_score"])))
    rows = []
    for (cat, b), (ev_h, n, our_h) in sorted(costs.items()):
        per = our_h / n
        evolkv = json.load(open(NAS / cat / "snapkv_evolkv_repro" / f"B{b}" / "full_data_eval_result.json"))["full_data_mean_score"]
        reeval = N_REEVAL * fe[cat]
        cap = int((ev_h - reeval) / per)
        assert cap >= INIT, (cat, b, cap)  # the initial design always fits, so heuristic/LHS picks are unaffected
        best_row, best = max(cand[(cat, b)], key=lambda x: x[1])
        kept = [s for i, s in cand[(cat, b)] if i < cap]
        capped = max(kept)
        lower = cap < n and best_row >= cap  # a guided pick inside the cap was never re-evaluated: score is a lower bound
        rows.append(dict(cat=cat, b=b, evolkv_h=ev_h, evolkv=evolkv, actual_evals=n, actual_h=our_h + reeval,
                         best_row=best_row + 1, full=best, cap=cap, capped_evals=min(n, cap),
                         capped_h=min(n, cap) * per + reeval, capped=capped, lower=lower))
    return rows


def compute_evals(max_evals=150):
    """Each Stage 4 run truncated to its first max_evals evaluations (in run order), plus the 3 full-data re-evaluations.
    The truncated NAS-refined is the best re-evaluated candidate within the cut; if the run's best guided proposal lies
    beyond it, the cut would re-evaluate a different guided proposal we never re-evaluated, so the score is a lower bound."""
    fe, costs = full_eval_hours(), search_costs()
    cand = {}
    for r in csv.DictReader(open(RES / "analysis_outputs" / "cells.csv")):
        if r["method"] == "snapkv" and r["source"] == "five_way" and r["label"] in ("heuristic", "random", "bo"):
            cand.setdefault((r["category"], int(r["budget"])), []).append((int(r["row_idx"]), r["label"], float(r["full_score"])))
    rows = []
    for (cat, b), (ev_h, n, our_h) in sorted(costs.items()):
        evolkv = json.load(open(NAS / cat / "snapkv_evolkv_repro" / f"B{b}" / "full_data_eval_result.json"))["full_data_mean_score"]
        k = min(n, max_evals)
        kept = [s for i, _, s in cand[(cat, b)] if i < k]
        bo_row = next(i for i, l, _ in cand[(cat, b)] if l == "bo")
        rows.append(dict(cat=cat, b=b, evolkv_h=ev_h, evolkv=evolkv, evals=k, h=k * our_h / n + N_REEVAL * fe[cat],
                         score=max(kept), lower=n > k and bo_row >= k))
    return rows


if __name__ == "__main__":
    rows = compute()
    for r in rows:
        print(f"{r['cat']:20s} B{r['b']:<5d} EvolKV {r['evolkv_h']:5.1f}h {r['evolkv']:.2f} | actual {r['actual_evals']:4d} evals "
              f"{r['actual_h']:5.1f}h best@{r['best_row']:3d} {r['full']:.2f} | cap {r['cap']:4d} -> {r['capped_evals']:4d} evals "
              f"{r['capped_h']:5.1f}h {r['capped']:.2f}{' (>=)' if r['lower'] else ''} delta {r['capped'] - r['evolkv']:+.2f}")
    print(f"totals: EvolKV {sum(r['evolkv_h'] for r in rows):.1f}h, actual {sum(r['actual_h'] for r in rows):.1f}h, "
          f"capped {sum(r['capped_h'] for r in rows):.1f}h, capped wins {sum(r['capped'] > r['evolkv'] for r in rows)}/6")
