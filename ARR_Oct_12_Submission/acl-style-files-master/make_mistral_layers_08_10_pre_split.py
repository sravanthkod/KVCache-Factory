#!/usr/bin/env python3
"""Mistral-7B-Instruct-v0.2 counterpart of Figure 3 (all four methods), drawn by make_layers_data.py.
Builds figures/data/mistral_layer_importance.csv:
  panel (a) anchor rows      = the configuration each task's Stage 4 searches were seeded with: the shaped configuration
                               that, rescaled with the NAS decoder (floor 16 or 64, cap 4096), reproduces the cells' Winner
                               rows exactly. Taken from the Stage 2 full-data evaluation when it is there, otherwise
                               recovered from the Winner rows on the Stage 1 grid (scale from the Stage 1 log). If neither
                               works, the Winner at the largest target budget is shown (its number is that budget);
  panel (b) best_config rows = MOSAIC's final configuration per cell (best non-uniform candidate on full data), for the
                               cells of mistral.load().
Then runs make_layers_data.py with LAYERS_IN/LAYERS_OUT -> figures/figure_mistral_layers.tex; build with pdflatex."""
import ast
import csv
import glob
import os
import subprocess
import sys
from pathlib import Path

import ast as _ast

import numpy as np

import mistral

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "ICLR_Final_Results"
OUT_CSV = HERE / "figures" / "data" / "mistral_layer_importance.csv"
DISP = {"CODE": "Code", "MULTI_DOCUMENT_QA": "MultiDoc", "SINGLE_DOCUMENT_QA": "SingleDoc", "SUMMARIZATION": "Summ", "RULER_ALL": "RULER"}
LAB = ["uniform", "heuristic", "winner", "random", "bo"]  # eval_results.csv arch 1-5
FOLDER = {"SnapKV": "SNAPKV", "H2O": "H2O", "AdaKV": "ADAKV"}
vec = lambda s: [int(float(x)) for x in (ast.literal_eval(s) if s.strip().startswith("[") else s.split())]


def _decoder():
    """x_point_to_budgets_continuous from the NAS code, without importing its model dependencies."""
    src = (HERE.parents[1] / "NAS_Assets" / "run_longbench_lamp.py").read_text()
    fn = next(n for n in _ast.parse(src).body if isinstance(n, _ast.FunctionDef) and n.name == "x_point_to_budgets_continuous")
    ns = {"np": np}
    exec(compile(_ast.Module(body=[fn], type_ignores=[]), "decoder", "exec"), ns)
    return ns["x_point_to_budgets_continuous"]


DEC = _decoder()


def cell_dir(m, cat, b):
    if m == "L2Norm":
        return ROOT / "MISTRAL_L2NORM_RESULTS" / cat / f"B{b}"
    if cat == "RULER_ALL":
        return ROOT / "MISTRAL_RULER_RESULTS" / FOLDER[m] / "RULER_ALL" / f"B{b}"
    return ROOT / "MISTRAL_LONGBENCH_RESULTS" / FOLDER[m] / cat / f"B{b}"


def stage2(m, cat):
    """Shaped configurations of the Stage 2 full-data evaluation: [(avg budget, score, budgets)]."""
    if m == "L2Norm":
        files, sk = glob.glob(str(ROOT / "MISTRAL_L2NORM_RESULTS" / cat / "unconstrained" / "eval_results*.csv")), "mean_score"
    elif cat == "RULER_ALL":
        files, sk = [str(ROOT / "MISTRAL_RULER_RESULTS" / FOLDER[m] / "RULER_ALL" / "unconstrained" / "eval_results_all500.csv")], "mean_score"
    else:
        files, sk = sorted(glob.glob(str(ROOT / "MISTRAL_LONGBENCH_RESULTS" / FOLDER[m] / cat / "unconstrained" / "summary_*.csv")))[-1:], "avg_score"
    out = {}
    for f in files:
        for r in csv.DictReader(open(f)):
            b = vec(r["budgets"])
            if len(set(b)) > 1:
                out[tuple(b)] = (float(r["avg_budget"]), float(r[sk]), b)
    return list(out.values())


LEV = [64, 128, 256, 512, 1024, 2048, 4096]


def _ok(w, wins):
    x = 0.05 + 0.9 * np.array(w, float) / max(w)
    return all(any(list(DEC(x, 32, b, fl, 4096)) == v for fl in (16, 64)) for b, v in wins.items())


def recover(m, cat, wins):
    """Anchor recovered from the Winner rows: shape on the Stage 1 grid, top level = the Stage 1 log's largest average."""
    log = (ROOT / "MISTRAL_LONGBENCH_RESULTS" / FOLDER[m] / cat / "unconstrained" / "output.txt") if m in FOLDER and cat != "RULER_ALL" else None
    if log is None or not log.exists():
        return None
    mx = int(np.loadtxt(log)[:, -2].max())
    for v in wins.values():
        bb = np.array(v, float)
        for j in np.where((bb > 64) & (bb < 4096))[0]:
            for L in [l for l in LEV if l <= mx]:
                k = (0.05 + 0.9 * L / mx) / bb[j]
                w = [min(LEV, key=lambda q: abs(q - r)) for r in (k * bb - 0.05) / 0.9 * mx]
                if max(w) == mx and _ok(w, wins):
                    return (float(np.mean(w)), None, w)
    return None


cells = mistral.load()
rows, final = [], {}
for (name, cat, b) in sorted(cells):
    m = name.replace(" (Mistral)", "")
    rs = {LAB[int(r["arch"]) - 1]: r for r in csv.DictReader(open(cell_dir(m, cat, b) / "eval_results.csv"))}
    non = {k: r for k, r in rs.items() if k != "uniform"}
    k = max(non, key=lambda k: float(non[k]["mean_score"]))
    final[(m, cat, b)] = (k, vec(non[k]["budgets"]), {kk: vec(r["budgets"]) for kk, r in non.items()})
for m in ["SnapKV", "H2O", "AdaKV", "L2Norm"]:
    for cat in DISP:
        cs = [v for (mm, c, _), v in final.items() if mm == m and c == cat]
        if not cs:
            continue
        cand = stage2(m, cat)
        wins = {bb: v[2]["winner"] for (mm, c, bb), v in final.items() if mm == m and c == cat and "winner" in v[2]}
        def hits(c):
            x = 0.05 + 0.9 * np.array(c[2], float) / max(c[2])
            return sum(any(list(DEC(x, 32, bb, fl, 4096)) == w for fl in (16, 64)) for bb, w in wins.items())
        best = max(cand, key=lambda c: c[1])
        anchor = max(cand, key=lambda c: (hits(c), c[1]))
        label = None
        if hits(anchor):
            note = f"Stage 2 config, reproduces {hits(anchor)}/{len(wins)} Winner rows" + ("" if anchor is best else f"; full-data best is avg {best[0]:.0f}")
        elif (rec := recover(m, cat, wins)):
            anchor, note = rec, f"recovered from the Winner rows ({len(wins)}/{len(wins)} reproduced); not in the Stage 2 evaluation"
        else:
            bmax = max(wins)
            anchor, label = (float(bmax), None, wins[bmax]), f"B{bmax} Winner"
            note = f"untraced: showing the B{bmax} Winner"
        print(f"panel (a): {m:6s} {cat:20s} avg {anchor[0]:.0f}: {note}")
        tail = f"(avg {round(anchor[0])})"  # untraced rows: the number is the Winner's target budget (see caption)
        rows.append({"panel": "anchor", "row": f"{m.lower()} · {DISP[cat]} {tail}", **{f"L{i}": x for i, x in enumerate(anchor[2])}})
for (m, cat, b), (k, bud, _) in sorted(final.items()):
    rows.append({"panel": "best_config", "row": f"{m.lower()} · {DISP[cat]} · B{b} ({k})", **{f"L{i}": x for i, x in enumerate(bud)}})
with open(OUT_CSV, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["panel", "row"] + [f"L{i}" for i in range(32)])
    w.writeheader()
    w.writerows(rows)
print(f"wrote {OUT_CSV}: {sum(r['panel'] == 'anchor' for r in rows)} anchors + {len(final)} cells")
env = dict(os.environ, LAYERS_IN=str(OUT_CSV), LAYERS_OUT=str(HERE / "figures" / "figure_mistral_layers.tex"))
subprocess.run([sys.executable, str(HERE / "make_layers_data.py")], env=env, check=True)
