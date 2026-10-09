#!/usr/bin/env python3
"""Three-way view of every evaluated cell: uniform, rescaled Stage 2 winner, and BO = best configuration found by the
Stage 4 search (its initial design of heuristic shapes and LHS points plus its guided proposals). Shared by
make_appendix.py and the main-text summary. Run directly to print the summary numbers used in the paper."""
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parents[1] / "ICLR_Final_Results"
SEARCH = {"heuristic", "random", "bo", "LHS seed", "BO"}


def _put(cells, key, typ, score, floor):
    c = cells.setdefault(key, {"floor": floor})
    slot = "uniform" if typ == "uniform" else "winner" if typ == "winner" else "bo" if typ in SEARCH else None
    if slot and (slot not in c or score > c[slot]):
        c[slot] = score


def load():
    """{(method, benchmark, category, budget): {'uniform', 'winner', 'bo', 'floor'}} (missing slots absent)."""
    cells, step3 = {}, {}
    for r in csv.DictReader(open(RES / "analysis_outputs" / "cells.csv")):  # SnapKV, H2O (five_way / slice_eval / step3)
        key = ({"snapkv": "SnapKV", "h2o": "H2O"}[r["method"]], r["benchmark"], r["category"], int(r["budget"]))
        if r["source"] == "step3":  # rescale-only runs; used only to fill a searched cell's missing winner
            if r["label"] == "winner":
                step3[key] = (float(r["full_score"]), int(r["era"]))
            continue
        _put(cells, key, r["label"], float(r["full_score"]), int(r["era"]))
    for key, (score, era) in step3.items():
        # a search not launched with the anchor has a heuristic at row 6 (relabelled in cells.csv); its winner is the
        # Stage 3 rescale, if one exists at the same floor
        if key in cells and "winner" not in cells[key] and era == cells[key]["floor"]:
            cells[key]["winner"] = score
    ada = RES / "ADAKV_RESULTS" / "data"
    amap = {"Uniform": "uniform", "Winner (rescaled anchor)": "winner", "Best heuristic": "heuristic",
            "Best random": "random", "Best BO": "bo"}
    for r in csv.DictReader(open(ada / "longbench_slices_step3_4.csv")):
        _put(cells, ("AdaKV", "longbench", r["category"], int(r["target_budget"])), amap[r["arch_name"]], float(r["mean_score"]), 64)
    for r in csv.DictReader(open(ada / "ruler_all_results.csv")):
        if r["stage"] == "step3_4_slice":
            b = int(r["target_budget"])
            _put(cells, ("AdaKV", "ruler", "RULER_ALL", b), amap[r["arch_name"]], float(r["mean_score"]), 16 if b >= 1024 else 64)
    l2 = RES / "LLAMA_L2NORM_RESULTS"
    lmap = ["uniform", "heuristic", "winner", "random", "bo"]
    for cat in ["SINGLE_DOCUMENT_QA", "MULTI_DOCUMENT_QA", "CODE", "SUMMARIZATION", "RULER_ALL"]:
        for d in (l2 / cat).glob("B*"):
            rows = list(csv.DictReader(open(d / "eval_results.csv")))
            if len(rows) != 5:
                continue
            bench = "ruler" if cat == "RULER_ALL" else "longbench"
            for r in rows:
                _put(cells, ("L2Norm", bench, cat, int(d.name[1:])), lmap[int(r["arch"]) - 1], float(r["mean_score"]), 64)
    return {k: v for k, v in cells.items() if "uniform" in v and ("bo" in v or "winner" in v)}


def summary(cells):
    """Per (method group, benchmark): cells, winner/BO wins over uniform and mean gains, BO >= winner."""
    groups = {"SnapKV + H2O": ("SnapKV", "H2O"), "AdaKV": ("AdaKV",), "L2Norm": ("L2Norm",)}
    out = []
    for g, ms in groups.items():
        for bench in ("longbench", "ruler"):
            ks = [k for k in cells if k[0] in ms and k[1] == bench]
            w = [cells[k]["winner"] - cells[k]["uniform"] for k in ks if "winner" in cells[k]]
            b = [cells[k]["bo"] - cells[k]["uniform"] for k in ks if "bo" in cells[k]]
            bw = [cells[k]["bo"] >= cells[k]["winner"] for k in ks if "bo" in cells[k] and "winner" in cells[k]]
            out.append((g, bench, len(ks), sum(x > 0 for x in w), len(w), sum(w) / len(w) if w else None,
                        sum(x > 0 for x in b), len(b), sum(b) / len(b) if b else None, sum(bw), len(bw)))
    return out


if __name__ == "__main__":
    c = load()
    print(f"{len(c)} cells")
    for g, bench, n, ww, wn, wm, bwin, bn, bm, bgw, bgn in summary(c):
        print(f"{g:13s} {bench:9s} n={n:2d}  winner>U {ww}/{wn} mean {wm:+.2f}  BO>U {bwin}/{bn} mean {bm:+.2f}  BO>=winner {bgw}/{bgn}")
    best = sum(max(v.get("winner", -1e9), v.get("bo", -1e9)) > v["uniform"] for v in c.values())
    print(f"max(winner,BO) > uniform: {best}/{len(c)}")
