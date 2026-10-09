#!/usr/bin/env python3
"""AdaKV counterpart of Figure 3 (Appendix H), drawn by make_layers_data.py in the same style.
Builds figures/data/adakv_layer_importance.csv from ICLR_Final_Results/ADAKV_RESULTS/data:
  panel (a) anchor rows      = the full-data-best Stage 2 configuration per task, i.e. the ring of Figure 2 (user, 2026-10-05),
  panel (b) best_config rows = MOSAIC's final configuration per cell, i.e. the best NON-uniform candidate on full data
                               (Winner, best heuristic, best LHS point, best guided proposal); cells = Table 1's AdaKV
                               MOSAIC cells; RULER B1024-B2048 were searched with floor 16 (flag f16 -> dagger).
Then runs make_layers_data.py with LAYERS_IN/LAYERS_OUT -> figures/figure_adakv_layers.tex; build with pdflatex."""
import csv
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ADA = HERE.parents[1] / "ICLR_Final_Results" / "ADAKV_RESULTS" / "data"
OUT_CSV = HERE / "figures" / "data" / "adakv_layer_importance.csv"
DISP = {"CODE": "Code", "MULTI_DOCUMENT_QA": "MultiDoc", "SINGLE_DOCUMENT_QA": "SingleDoc", "SUMMARIZATION": "Summ", "RULER_ALL": "RULER"}
TYPE = {"Winner (rescaled anchor)": "winner", "Best heuristic": "heuristic", "Best random": "random", "Best BO": "bo"}
NATURAL = {"SINGLE_DOCUMENT_QA": 464, "MULTI_DOCUMENT_QA": 188, "CODE": 482, "RULER_ALL": 2536}  # winners used downstream


def vec(s):
    return [int(float(x)) for x in s.split()]


cells = {}  # (cat, budget) -> {arch_name: (score, budgets)}
for r in csv.DictReader(open(ADA / "longbench_slices_step3_4.csv")):
    cells.setdefault((r["category"], int(r["target_budget"])), {})[r["arch_name"]] = (float(r["mean_score"]), vec(r["budgets"]))
for r in csv.DictReader(open(ADA / "ruler_all_results.csv")):
    if r["stage"] == "step3_4_slice":
        cells.setdefault(("RULER_ALL", int(r["target_budget"])), {})[r["arch_name"]] = (float(r["mean_score"]), vec(r["budgets"]))
best = {}  # cat -> (full-data score, avg budget, budgets) of the best shaped Stage 2 configuration (= Figure 2 ring)
for r in csv.DictReader(open(ADA / "longbench_step2_pareto_full_eval.csv")):
    if r["type"] != "uniform":
        k, sc = r["category"], float(r["avg_score"])
        if k not in best or sc > best[k][0]:
            best[k] = (sc, round(float(r["avg_budget"])), vec(r["budgets"]))
for r in csv.DictReader(open(ADA / "ruler_all_results.csv")):
    if r["stage"].startswith("step2") and len(set(vec(r["budgets"]))) > 1:
        sc = float(r["mean_score"])
        if "RULER_ALL" not in best or sc > best["RULER_ALL"][0]:
            best["RULER_ALL"] = (sc, round(float(r["avg_budget"])), vec(r["budgets"]))
anchors = {k: v[2] for k, v in best.items()}
NATURAL = {k: v[1] for k, v in best.items()}
assert len(anchors) == 5, sorted(anchors)
print("panel (a):", {k: (v[1], round(v[0], 2)) for k, v in best.items()})

rows = []
for cat, bud in anchors.items():
    rows.append({"panel": "anchor", "row": f"adakv · {DISP[cat]} (avg {NATURAL[cat]})", **{f"L{i}": bud[i] for i in range(32)}})
for (cat, b), v in sorted(cells.items()):
    non = {a: x for a, x in v.items() if a in TYPE}
    best = max(non, key=lambda a: non[a][0])
    flag = ", f16" if cat == "RULER_ALL" and b in (1024, 1536, 2048) else ""
    rows.append({"panel": "best_config", "row": f"adakv · {DISP[cat]} · B{b} ({TYPE[best]}{flag})",
                 **{f"L{i}": non[best][1][i] for i in range(32)}})
    print(f"  {cat:20s} B{b:<5d} {TYPE[best]:9s} {non[best][0]:.2f}{'  (floor 16)' if flag else ''}")
with open(OUT_CSV, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["panel", "row"] + [f"L{i}" for i in range(32)])
    w.writeheader()
    w.writerows(rows)
print(f"wrote {OUT_CSV}: {len(anchors)} anchors + {len(rows) - len(anchors)} cells")
env = dict(os.environ, LAYERS_IN=str(OUT_CSV), LAYERS_OUT=str(HERE / "figures" / "figure_adakv_layers.tex"))
subprocess.run([sys.executable, str(HERE / "make_layers_data.py")], env=env, check=True)
