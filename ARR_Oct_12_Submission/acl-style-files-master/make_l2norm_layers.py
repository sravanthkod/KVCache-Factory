#!/usr/bin/env python3
"""L2Norm counterpart of Figure 3 (Appendix F), drawn by make_layers_data.py in the same style as make_adakv_layers.py.
Builds figures/data/l2norm_layer_importance.csv from ICLR_Final_Results/LLAMA_L2NORM_RESULTS:
  panel (a) anchor rows      = the full-data-best shaped Stage 2 configuration per task (<CAT>/unconstrained/eval_results.csv),
                               i.e. the ring of Figure 2 and the winner every fixed-budget cell rescales;
  panel (b) best_config rows = MOSAIC's final configuration per cell, i.e. the best NON-uniform candidate on full data
                               (<CAT>/B<b>/eval_results.csv); cells = Table 1's L2Norm MOSAIC cells (three_way.load()).
Then runs make_layers_data.py with LAYERS_IN/LAYERS_OUT -> figures/figure_l2norm_layers.tex; build with pdflatex."""
import csv
import os
import subprocess
import sys
from pathlib import Path

import three_way as tw

HERE = Path(__file__).resolve().parent
L2 = HERE.parents[1] / "ICLR_Final_Results" / "LLAMA_L2NORM_RESULTS"
OUT_CSV = HERE / "figures" / "data" / "l2norm_layer_importance.csv"
DISP = {"CODE": "Code", "MULTI_DOCUMENT_QA": "MultiDoc", "SINGLE_DOCUMENT_QA": "SingleDoc", "SUMMARIZATION": "Summ", "RULER_ALL": "RULER"}
LAB = ["uniform", "heuristic", "winner", "random", "bo"]  # eval_results.csv arch 1-5
vec = lambda s: [int(float(x)) for x in s.split()]

rows = []
for cat in DISP:
    st2 = [r for r in csv.DictReader(open(L2 / cat / "unconstrained" / "eval_results.csv")) if len(set(r["budgets"].split())) > 1]
    w = max(st2, key=lambda r: float(r["mean_score"]))
    rows.append({"panel": "anchor", "row": f"l2norm · {DISP[cat]} (avg {round(float(w['avg_budget']))})", **{f"L{i}": b for i, b in enumerate(vec(w["budgets"]))}})
    print(f"panel (a): {cat:20s} avg {float(w['avg_budget']):.0f}  {float(w['mean_score']):.2f}")
cells = sorted((c, b) for (m, _, c, b) in tw.load() if m == "L2Norm")
for cat, b in cells:
    rs = {LAB[int(r["arch"]) - 1]: r for r in csv.DictReader(open(L2 / cat / f"B{b}" / "eval_results.csv"))}
    non = {k: r for k, r in rs.items() if k != "uniform"}
    k = max(non, key=lambda k: float(non[k]["mean_score"]))
    rows.append({"panel": "best_config", "row": f"l2norm · {DISP[cat]} · B{b} ({k})", **{f"L{i}": x for i, x in enumerate(vec(non[k]["budgets"]))}})
    print(f"  {cat:20s} B{b:<5d} {k:9s} {float(non[k]['mean_score']):.2f}")
with open(OUT_CSV, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["panel", "row"] + [f"L{i}" for i in range(32)])
    w.writeheader()
    w.writerows(rows)
print(f"wrote {OUT_CSV}: {sum(r['panel'] == 'anchor' for r in rows)} anchors + {len(cells)} cells")
env = dict(os.environ, LAYERS_IN=str(OUT_CSV), LAYERS_OUT=str(HERE / "figures" / "figure_l2norm_layers.tex"))
subprocess.run([sys.executable, str(HERE / "make_layers_data.py")], env=env, check=True)
