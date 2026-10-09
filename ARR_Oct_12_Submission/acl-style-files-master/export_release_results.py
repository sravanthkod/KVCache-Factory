#!/usr/bin/env python3
"""Export the cells reported in main.pdf (main text + appendix) to MOSAIC/results/cells.csv, one row per
(model, method, benchmark, task, budget), with the per-layer allocations behind each number.

Scores come from the same loaders as the paper's tables (three_way.load for Llama, mistral.load for Mistral, and
figures/data/stage3_rows.csv for the Llama cells that have only a rescaled winner), so the CSV cannot drift from the
paper. Allocations and sub-scores are looked up in the raw result files by matching the score."""
import ast
import csv
import sys
from pathlib import Path

import mistral
import three_way as tw

HERE = Path(__file__).resolve().parent
RES = next(d for d in (HERE.parents[0] / "ICLR_Final_Results", HERE.parents[1] / "ICLR_Final_Results") if (d / "analysis_outputs").exists())
tw.RES, mistral.ROOT = RES, RES  # the loaders hard-code the old location of the results folder
OUT = HERE / "MOSAIC" / "results" / "cells.csv"
SEARCH = {"heuristic", "random", "bo", "LHS seed", "BO"}
LAB = ["uniform", "heuristic", "winner", "random", "bo"]
NONDATA = {"arch", "avg_budget", "nas_f2", "mean_score", "budgets"}
vec = lambda s: [int(float(x)) for x in (ast.literal_eval(s) if s.strip().startswith("[") else s.split())]
parse_ds = lambda s: {kv.split("=")[0]: float(kv.split("=")[1]) for kv in s.split(";")} if s else {}


def eval_rows(path):
    """eval_results.csv with arch 1-5 = uniform, heuristic, winner, random, bo -> [(label, score, budgets, subscores)]."""
    out = []
    for r in csv.DictReader(open(path)):
        out.append((LAB[int(r["arch"]) - 1], float(r["mean_score"]), vec(r["budgets"]),
                    {k: float(v) for k, v in r.items() if k not in NONDATA and v not in ("", None)}))
    return out


# ---- candidate lookup: key -> [(label, score, budgets, subscores)] ----
cand = {}
step3 = {}
for r in csv.DictReader(open(RES / "analysis_outputs" / "cells.csv")):  # Llama SnapKV, H2O
    m = {"snapkv": "SnapKV", "h2o": "H2O"}[r["method"]]
    k = ("Llama-3-8B-Instruct", m, r["benchmark"], r["category"], int(r["budget"]))
    row = (r["label"], float(r["full_score"]), vec(r["budgets"]), parse_ds(r["per_dataset"]))
    (step3 if r["source"] == "step3" else cand).setdefault(k, []).append(row)
ada = RES / "ADAKV_RESULTS" / "data"
amap = {"Uniform": "uniform", "Winner (rescaled anchor)": "winner", "Best heuristic": "heuristic", "Best random": "random", "Best BO": "bo"}
_a = {}
for r in csv.DictReader(open(ada / "longbench_slices_step3_4.csv")):
    k = ("Llama-3-8B-Instruct", "AdaKV", "longbench", r["category"], int(r["target_budget"]))
    e = _a.setdefault((k, amap[r["arch_name"]]), [amap[r["arch_name"]], float(r["mean_score"]), vec(r["budgets"]), {}])
    e[3][r["dataset"]] = float(r["score"])
for r in csv.DictReader(open(ada / "ruler_all_results.csv")):
    if r["stage"] == "step3_4_slice":
        k = ("Llama-3-8B-Instruct", "AdaKV", "ruler", "RULER_ALL", int(r["target_budget"]))
        _a[(k, amap[r["arch_name"]])] = [amap[r["arch_name"]], float(r["mean_score"]), vec(r["budgets"]),
                                         {t: float(r[t]) for t in ("niah_single_1", "niah_single_2", "niah_single_3", "niah_multikey_1", "niah_multikey_2",
                                                                    "niah_multikey_3", "niah_multiquery", "niah_multivalue", "cwe", "fwe", "vt")}]
for (k, _), v in _a.items():
    cand.setdefault(k, []).append(tuple(v))
for cat in ["SINGLE_DOCUMENT_QA", "MULTI_DOCUMENT_QA", "CODE", "SUMMARIZATION", "RULER_ALL"]:  # Llama L2Norm
    for d in (RES / "LLAMA_L2NORM_RESULTS" / cat).glob("B*"):
        rows = eval_rows(d / "eval_results.csv")
        if len(rows) == 5:
            cand[("Llama-3-8B-Instruct", "L2Norm", "ruler" if cat == "RULER_ALL" else "longbench", cat, int(d.name[1:]))] = rows
FOLDER = {"SnapKV": "SNAPKV", "H2O": "H2O", "AdaKV": "ADAKV"}
for (name, cat, b) in mistral.load():  # Mistral
    m = name.replace(" (Mistral)", "")
    if m == "L2Norm":
        d = RES / "MISTRAL_L2NORM_RESULTS" / cat / f"B{b}"
    elif cat == "RULER_ALL":
        d = RES / "MISTRAL_RULER_RESULTS" / FOLDER[m] / "RULER_ALL" / f"B{b}"
    else:
        d = RES / "MISTRAL_LONGBENCH_RESULTS" / FOLDER[m] / cat / f"B{b}"
    cand[("Mistral-7B-Instruct-v0.2", m, "ruler" if cat == "RULER_ALL" else "longbench", cat, b)] = eval_rows(d / "eval_results.csv")


def pick(rows, labels, score):
    """The candidate with one of `labels` whose score matches (best-scoring one if none matches exactly)."""
    c = [r for r in rows if r[0] in labels]
    if not c:
        return None
    exact = [r for r in c if abs(r[1] - score) < 0.006]
    return (exact or [max(c, key=lambda r: r[1])])[0], bool(exact)


fmt = lambda b: " ".join(str(x) for x in b)
sub = lambda d: ";".join(f"{k}={v:g}" for k, v in d.items())
task = {"CODE": "Code", "MULTI_DOCUMENT_QA": "Multi-Doc QA", "SINGLE_DOCUMENT_QA": "Single-Doc QA", "SUMMARIZATION": "Summarization", "RULER_ALL": "RULER"}
out, warn = [], 0


def add(model, m, bench, cat, b, v, floor, searched):
    global warn
    rows = cand.get((model, m, bench, cat, b), []) + (step3.get((model, m, bench, cat, b), []) if "winner" in v else [])
    u = pick(rows, {"uniform"}, v["uniform"])
    w = pick([r for r in rows if r[0] == "winner"], {"winner"}, v["winner"]) if "winner" in v else None
    n = pick(rows, SEARCH, v["bo"]) if "bo" in v else None
    for nm, x in (("uniform", u), ("winner", w), ("nas", n)):
        if x and not x[1]:
            warn += 1
            print(f"  no exact match: {model[:6]} {m} {cat} B{b} {nm}: paper {v.get({'uniform':'uniform','winner':'winner','nas':'bo'}[nm]):.4f} vs raw {x[0][1]:.4f} ({x[0][0]})")
    win, nas = (w[0] if w else None), (n[0] if n else None)
    if win is None and "winner" in v:  # score only (no raw row on disk for this rescale-only cell)
        win = ("winner", v["winner"], [], {})
    fin = max([x for x in (win, nas) if x], key=lambda r: r[1])
    out.append({"model": model, "method": m, "benchmark": bench, "task": task[cat], "budget": b,
                "per_layer_floor": floor, "stage4_search": int(searched),
                "uniform": f"{v['uniform']:.2f}", "winner": f"{v['winner']:.2f}" if "winner" in v else "",
                "nas_refined": f"{v['bo']:.2f}" if "bo" in v else "", "mosaic": f"{fin[1]:.2f}",
                "mosaic_config": "winner" if fin is win else "nas_refined",
                "winner_allocation": fmt(win[2]) if win and win[2] else "", "nas_refined_allocation": fmt(nas[2]) if nas else "",
                "uniform_subscores": sub(u[0][3]) if u else "", "mosaic_subscores": sub(fin[3])})


for (m, bench, cat, b), v in sorted(tw.load().items()):
    add("Llama-3-8B-Instruct", m, bench, cat, b, v, v["floor"], True)
for (name, cat, b), v in sorted(mistral.load().items()):
    add("Mistral-7B-Instruct-v0.2", name.replace(" (Mistral)", ""), "ruler" if cat == "RULER_ALL" else "longbench", cat, b, v, v["floor"], True)
have = {(r["method"], r["benchmark"], r["task"], r["budget"]) for r in out if r["model"].startswith("Llama")}
for r in csv.DictReader(open(HERE / "figures" / "data" / "stage3_rows.csv")):  # Llama cells with only a rescaled winner (Stage 3)
    cat = {v: k for k, v in {"CODE": "Code", "MULTI_DOCUMENT_QA": "MultiDoc", "SINGLE_DOCUMENT_QA": "SingleDoc", "SUMMARIZATION": "Summ", "RULER_ALL": "RULER"}.items()}[r["category"]]
    bench = "ruler" if cat == "RULER_ALL" else "longbench"
    if (r["method"], bench, task[cat], int(r["budget"])) not in have and r["method"] in ("SnapKV", "H2O", "AdaKV", "L2Norm"):
        add("Llama-3-8B-Instruct", r["method"], bench, cat, int(r["budget"]), {"uniform": float(r["uniform"]), "winner": float(r["winner"])}, int(r["floor"]), False)
with open(HERE / "figures" / "data" / "mistral_summarization_uniform.csv") as f:  # Mistral Summarization: uniform only (Stage 1 only)
    for r in csv.DictReader(l for l in f if not l.startswith("#")):
        for m in ("SnapKV", "H2O", "AdaKV"):
            if int(r["budget"]) in (128, 256, 512, 1024):
                out.append({"model": "Mistral-7B-Instruct-v0.2", "method": m, "benchmark": "longbench", "task": "Summarization", "budget": int(r["budget"]),
                            "per_layer_floor": "", "stage4_search": 0, "uniform": r[m], "winner": "", "nas_refined": "", "mosaic": "", "mosaic_config": "",
                            "winner_allocation": "", "nas_refined_allocation": "", "uniform_subscores": "", "mosaic_subscores": ""})
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)
n4 = [r for r in out if r["stage4_search"]]
print(f"{len(out)} rows -> {OUT}; Stage 4 cells {len(n4)} (Llama {sum(r['model'].startswith('Llama') for r in n4)}, "
      f"Mistral {sum(r['model'].startswith('Mistral') for r in n4)}); score/allocation mismatches: {warn}")
