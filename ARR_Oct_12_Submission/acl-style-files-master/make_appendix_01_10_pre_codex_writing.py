#!/usr/bin/env python3
"""Build appendix.tex from ICLR_Final_Results/analysis_outputs/*.md (rerun after those change)."""
import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "ICLR_Final_Results" / "analysis_outputs"
OUT = Path(__file__).resolve().parent / "appendix.tex"

CAT = {"CODE": "Code", "MULTI_DOCUMENT_QA": "MultiDoc", "SINGLE_DOCUMENT_QA": "SingleDoc",
       "SUMMARIZATION": "Summ", "RULER_ALL": "RULER"}
MET = {"snapkv": "SnapKV", "h2o": "H2O", "snapkv/h2o": "SnapKV/H2O"}
LBL = {"bo": "NAS-refined", "winner": "Winner", "random": "NAS-refined", "heuristic": "NAS-refined", "uniform": "uniform"}  # three-way view
def DISP(a):
    """uniform / Winner / NAS-refined (best config of the Stage 4 search, incl. its initial design)."""
    return "uniform" if a == "uniform" else "Winner" if a == "winner" else "NAS-refined"


def tables(name):
    """Return every markdown table in the file as a list of row-lists (header row dropped)."""
    out, cur = [], None
    for line in (SRC / name).read_text().splitlines():
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cur is None:
                cur = []
            elif not set("".join(cells)) <= set("-: "):
                cur.append(cells)
        elif cur is not None:
            out.append(cur)
            cur = None
    if cur is not None:
        out.append(cur)
    return out


ADA = SRC.parent / "ADAKV_RESULTS" / "data"
# Stage 2 winner anchors' natural average budgets, from ADAKV_RESULTS.md (anchors/anchor_adakv_<budget>.txt)
ADA_NATURAL = {"SINGLE_DOCUMENT_QA": 464, "MULTI_DOCUMENT_QA": 188, "CODE": 482, "RULER_ALL": 2536}
ADA_ARCH = {"Uniform": "uniform", "Winner (rescaled anchor)": "winner", "Best heuristic": "heuristic",
            "Best random": "LHS seed", "Best BO": "BO"}
RULER_TASKS = ["niah_single_1", "niah_single_2", "niah_single_3", "niah_multikey_1", "niah_multikey_2",
               "niah_multikey_3", "niah_multiquery", "niah_multivalue", "cwe", "fwe", "vt"]


def ada_floor(cat, b):
    # RULER B64 and B1024-B2048 AdaKV runs predate the switch from floor 16 to 64
    return 16 if cat == "RULER_ALL" and b in (64, 1024, 1536, 2048) else 64


def adakv():
    """AdaKV full-data results: {(category, budget): {stage: score}}, RULER subtasks, uniform-64 from Stage 2."""
    import csv
    cells, sub = {}, {}
    for r in csv.DictReader(open(ADA / "longbench_slices_step3_4.csv")):
        cells.setdefault((r["category"], int(r["target_budget"])), {})[ADA_ARCH[r["arch_name"]]] = float(r["mean_score"])
    u64 = None
    for r in csv.DictReader(open(ADA / "ruler_all_results.csv")):
        if r["stage"].startswith("step2"):
            if r["arch_name"] == "uniform" and float(r["avg_budget"]) == 64:
                u64 = float(r["mean_score"]); sub[("RULER_ALL", 64, "uniform")] = [float(r[t]) for t in RULER_TASKS]
            continue
        b, a = int(r["target_budget"]), ADA_ARCH[r["arch_name"]]
        cells.setdefault(("RULER_ALL", b), {})[a] = float(r["mean_score"])
        sub[("RULER_ALL", b, a)] = [float(r[t]) for t in RULER_TASKS]
    return cells, sub, u64


L2 = SRC.parent / "LLAMA_L2NORM_RESULTS"
L2_ARCH = ["uniform", "heuristic", "winner", "LHS seed", "BO"]  # eval_results.csv arch 1-5 (README)
L2_CATS = ["CODE", "MULTI_DOCUMENT_QA", "SINGLE_DOCUMENT_QA", "SUMMARIZATION", "RULER_ALL"]


def l2norm():
    """L2Norm (Llama): five-way cells {(cat, b): [(arch, calib, full)]}, RULER subtasks, Stage 2 winner natural budget."""
    import csv
    five, sub, natural = {}, {}, {}
    for cat in L2_CATS:
        s2 = [r for r in csv.DictReader(open(L2 / cat / "unconstrained" / "eval_results.csv"))
              if len(set(r["budgets"].split())) > 1]
        natural[cat] = round(float(max(s2, key=lambda r: float(r["mean_score"]))["avg_budget"]))
        for d in (L2 / cat).glob("B*"):
            rows = list(csv.DictReader(open(d / "eval_results.csv")))
            if len(rows) != 5:  # B64 (uniform only) and the top extreme (rescaled winner only, no uniform)
                continue
            b = int(d.name[1:])
            five[(cat, b)] = [(L2_ARCH[int(r["arch"]) - 1], -float(r["nas_f2"]), float(r["mean_score"])) for r in rows]
            if cat == "RULER_ALL":
                for r in rows:
                    sub[(b, L2_ARCH[int(r["arch"]) - 1])] = [float(r[t]) for t in RULER_TASKS]
    return five, sub, natural


def tex(s):
    s = s.replace("**", "").replace("%", r"\%").replace("_", r"\_").replace("~", r"$\sim$")
    s = s.replace("≈", r"$\approx$").replace("—", "--").replace("τ", r"$\tau$").replace("×", r"$\times$")
    s = re.sub(r"^([+-])(\d)", lambda m: ("$-$" if m.group(1) == "-" else "+") + m.group(2), s)
    return s


def neg(s):
    return r"\textbf{" + tex(s) + "}" if s.startswith("-") else tex(s)


def tabular(spec, header, rows, size=r"\footnotesize", sep="4pt"):
    body = "\n".join("    " + " & ".join(r) + r" \\" for r in rows)
    return (f"  {size}\n  \\setlength{{\\tabcolsep}}{{{sep}}}\n  \\begin{{tabular}}{{@{{}}{spec}@{{}}}}\n"
            f"    \\toprule\n    {' & '.join(header)} \\\\\n    \\midrule\n{body}\n    \\bottomrule\n  \\end{{tabular}}\n")


def float_(env, content, caption, label, pos="t"):
    return (f"\\begin{{{env}}}[{pos}]\n  \\centering\n{content}  \\caption{{{caption}}}\n"
            f"  \\label{{{label}}}\n\\end{{{env}}}\n")


parts = [r"""\clearpage
\appendix

\section{Per-Cell Results}
\label{app:cells}

LongBench categories: Single-Doc QA (NarrativeQA, Qasper, MultiFieldQA-en), Multi-Doc QA (HotpotQA, 2WikiMQA, MuSiQue), Summarization (GovReport, QMSum, Multi-News) and Code (LCC, RepoBench-P); a category's score is the mean over its datasets, each scored on all of its 150--500 samples. RULER uses its 11 subtasks at 4K context, 500 samples each.

Tables~\ref{tab:app-cells} and~\ref{tab:app-cells-l2norm} list every (category, method, budget) cell with a full-data evaluation on Llama-3-8B-Instruct: uniform, the rescaled Stage 2 winner (Winner), and NAS-refined, the best configuration found by the Stage 4 search. $\Delta$ is MOSAIC's final configuration (the better of Winner and NAS-refined) minus uniform; losses are in bold. ``Floor'' is the per-layer minimum budget in effect for that run.
"""]

# A: B4 per-cell
a5, _agg, b4, *_ = tables("A5_B4_tables.md")
rows = [[CAT[r[1]], r[2], MET[r[3]], r[4], r[5], f"{r[6]} ({LBL[r[7]]})", neg(r[8])] for r in b4]
sk_wins = sum(not r[8].startswith("-") for r in b4)
ada, ada_sub, ada_u64 = adakv()
order = ["CODE", "MULTI_DOCUMENT_QA", "SINGLE_DOCUMENT_QA", "RULER_ALL"]
ada_five = sorted([k for k, v in ada.items() if "uniform" in v], key=lambda k: (order.index(k[0]), k[1]))
ada_wins = 0
for cat, b in ada_five:
    v = ada[(cat, b)]
    non = {a: s for a, s in v.items() if a != "uniform"}
    best = max(non, key=non.get)
    d = non[best] - v["uniform"]
    ada_wins += d > 0
    rows.append([CAT[cat], str(b), "AdaKV", str(ada_floor(cat, b)), f"{v['uniform']:.2f}", f"{non[best]:.2f} ({best})", neg(f"{d:+.2f}")])
n_cells = len(b4) + len(ada_five)
n_wins = sk_wins + ada_wins
print(f"per-cell: SnapKV/H2O {sk_wins}/{len(b4)}, AdaKV {ada_wins}/{len(ada_five)}, total {n_wins}/{n_cells}")
# A2: L2Norm per-cell (floor 64 everywhere)
l2, l2_sub, l2_nat = l2norm()
l2_order = ["CODE", "MULTI_DOCUMENT_QA", "SINGLE_DOCUMENT_QA", "SUMMARIZATION", "RULER_ALL"]
l2_keys = sorted(l2, key=lambda k: (l2_order.index(k[0]), k[1]))
rows, l2_wins = [], 0
for cat, b in l2_keys:
    v = {a: f for a, _, f in l2[(cat, b)]}
    non = {a: s for a, s in v.items() if a != "uniform"}
    best = max(non, key=non.get)
    d = non[best] - v["uniform"]
    l2_wins += d > 0
    rows.append([CAT[cat], str(b), f"{v['uniform']:.2f}", f"{non[best]:.2f} ({best})", neg(f"{d:+.2f}")])
print(f"per-cell L2Norm {l2_wins}/{len(l2_keys)}; all four methods {n_wins + l2_wins}/{n_cells + len(l2_keys)}")

# three-way per-cell tables (uniform / Winner / BO), shared loader
import three_way as _tw
_c = _tw.load()
_ord = {"CODE": 0, "MULTI_DOCUMENT_QA": 1, "SINGLE_DOCUMENT_QA": 2, "SUMMARIZATION": 3, "RULER_ALL": 4}
def _f(v, k):
    return f"{v[k]:.2f}" if k in v else "--"
def _d(v):
    return neg(f"{max(v.get('winner', -1e9), v.get('bo', -1e9)) - v['uniform']:+.2f}")
rows = []
for k in sorted((k for k in _c if k[0] != "L2Norm"), key=lambda k: (["SnapKV", "H2O", "AdaKV"].index(k[0]), _ord[k[2]], k[3])):
    v = _c[k]
    rows.append([CAT[k[2]], str(k[3]), k[0], str(v["floor"]), _f(v, "uniform"), _f(v, "winner"), _f(v, "bo"), _d(v)])
_w3 = sum(max(_c[k].get("winner", -1e9), _c[k].get("bo", -1e9)) > _c[k]["uniform"] for k in _c if k[0] != "L2Norm")
_n3 = sum(1 for k in _c if k[0] != "L2Norm")
parts.append(float_("table", tabular("l r l r r r r r", ["Cat.", "B", "Method", "Floor", "Uniform", "Winner", "NAS-ref.", r"$\Delta$"], rows, size=r"\scriptsize", sep="2.5pt"),
                    rf"\textbf{{Full-data results for every evaluated cell, SnapKV, H2O and AdaKV.}} MOSAIC beats uniform in {_w3} of {_n3} cells. ``--'': not evaluated (H2O RULER B2048 has no winner row).", "tab:app-cells", pos="!b"))
rows = []
for k in sorted((k for k in _c if k[0] == "L2Norm"), key=lambda k: (_ord[k[2]], k[3])):
    v = _c[k]
    rows.append([CAT[k[2]], str(k[3]), _f(v, "uniform"), _f(v, "winner"), _f(v, "bo"), _d(v)])
_wl = sum(max(_c[k]["winner"], _c[k]["bo"]) > _c[k]["uniform"] for k in _c if k[0] == "L2Norm")
_nl = sum(1 for k in _c if k[0] == "L2Norm")
print(f"per-cell three-way: SnapKV/H2O/AdaKV {_w3}/{_n3}, L2Norm {_wl}/{_nl}, total {_w3 + _wl}/{_n3 + _nl}")
parts.append(float_("table", tabular("l r r r r r", ["Cat.", "B", "Uniform", "Winner", "NAS-refined", r"$\Delta$"], rows, size=r"\scriptsize", sep="3pt"),
                    rf"\textbf{{Full-data results for every evaluated cell, L2Norm}} (floor 64 in every cell). MOSAIC beats uniform in {_wl} of {_nl} cells. At B64 only uniform is possible (every layer sits at the floor), and at the top budget only the rescaled winner was run, so neither cell is listed.", "tab:app-cells-l2norm"))

# B: A5 calibration fidelity
parts.append(r"""
\section{Calibration Scores vs.\ Full-Data Scores}
\label{app:calib}

During search, each configuration is scored on a calibration subsample. The Stage 4 searches analysed here use a 10\% subsample for all four methods on both benchmarks (Stage 1 uses 30\% on LongBench). Table~\ref{tab:app-calib} (SnapKV and H2O), Table~\ref{tab:app-calib-adakv} (AdaKV) and Table~\ref{tab:app-calib-l2norm} (L2Norm) compare these scores with the full-data scores of the same five candidates per cell: the mean gap (calibration minus full data), Kendall's $\tau$ between the two rankings, the candidate the calibration score would pick, the true full-data best, and the regret (full-data points lost by trusting calibration).
""")
rows = [[CAT[r[1]], r[2], MET[r[3]], r[4], tex(r[5]), tex(r[6]), f"{LBL[r[7]]} ({r[8]})", f"{LBL[r[9]]} ({r[10]})", r[11]] for r in a5]
parts.append(float_("table*", tabular("l r l r r r l l r", ["Category", "B", "Method", "Floor", "Gap", r"$\tau$", "Calib.\\ pick (score)", "True best (score)", "Regret"], rows),
                    r"\textbf{Calibration fidelity per cell.} On LongBench, calibration scores are optimistic and their ranking is essentially uncorrelated with full-data ranking; on RULER they are faithful.", "tab:app-calib"))

# B2: AdaKV calibration fidelity (from ADAKV_RESULTS/data/calibration_vs_full_eval.csv)
import csv as _csv, itertools as _it
_cal = {}
for r in _csv.DictReader(open(ADA / "calibration_vs_full_eval.csv")):
    _cal.setdefault((r["category"], int(r["target_budget"])), []).append(
        (ADA_ARCH.get("Best " + r["candidate"].lower(), r["candidate"]).replace("Uniform", "uniform").replace("Winner", "winner"),
         float(r["calibration_score"]), float(r["full_eval_score"])))
def _tau(a, b):
    pr = list(_it.combinations(range(len(a)), 2))
    return sum(((a[i] - a[j]) * (b[i] - b[j]) > 0) - ((a[i] - a[j]) * (b[i] - b[j]) < 0) for i, j in pr) / len(pr)
rows = []
for (cat, b) in sorted(_cal, key=lambda k: (order.index(k[0]), k[1])):
    v = _cal[(cat, b)]
    c, f = [x[1] for x in v], [x[2] for x in v]
    gap = sum(ci - fi for ci, fi in zip(c, f)) / len(v)
    pick, best = max(v, key=lambda x: x[1]), max(v, key=lambda x: x[2])
    rows.append([CAT[cat], str(b), tex(f"{gap:+.2f}"), tex(f"{_tau(c, f):+.2f}"),
                 f"{DISP(pick[0]) if pick[0] in ('uniform','winner') else 'NAS-refined'} ({pick[2]:.2f})", f"{DISP(best[0]) if best[0] in ('uniform','winner') else 'NAS-refined'} ({best[2]:.2f})", f"{best[2] - pick[2]:.2f}"])
parts.append(float_("table*", tabular("l r r r l l r", ["Category", "B", "Gap", r"$\tau$", "Calib.\\ pick (score)", "True best (score)", "Regret"], rows),
                    r"\textbf{Calibration fidelity per cell, AdaKV.} On LongBench the calibration pick is the true best in only 2 of 9 cells, and on RULER in 5 of 6.", "tab:app-calib-adakv"))

# B3: L2Norm calibration fidelity (nas_f2 = -calibration score)
rows, l2cal = [], {}
for cat, b in l2_keys:
    v = l2[(cat, b)]
    c, f = [x[1] for x in v], [x[2] for x in v]
    gap = sum(ci - fi for ci, fi in zip(c, f)) / len(v)
    pick, best = max(v, key=lambda x: x[1]), max(v, key=lambda x: x[2])
    bench = "RULER" if cat == "RULER_ALL" else "LongBench"
    l2cal.setdefault(bench, []).append((gap, _tau(c, f), pick[0] == best[0], best[2] - pick[2]))
    rows.append([CAT[cat], str(b), tex(f"{gap:+.2f}"), tex(f"{_tau(c, f):+.2f}"),
                 f"{DISP(pick[0]) if pick[0] in ('uniform','winner') else 'NAS-refined'} ({pick[2]:.2f})", f"{DISP(best[0]) if best[0] in ('uniform','winner') else 'NAS-refined'} ({best[2]:.2f})", f"{best[2] - pick[2]:.2f}"])
for bench, l in l2cal.items():
    print(f"L2Norm calib {bench}: cells {len(l)} gap {sum(x[0] for x in l)/len(l):+.2f} tau {sum(x[1] for x in l)/len(l):+.2f} "
          f"picks {sum(x[2] for x in l)}/{len(l)} regret {sum(x[3] for x in l)/len(l):.2f}")
parts.append(float_("table*", tabular("l r r r l l r", ["Category", "B", "Gap", r"$\tau$", "Calib.\\ pick (score)", "True best (score)", "Regret"], rows),
                    r"\textbf{Calibration fidelity per cell, L2Norm.} Calibration ranks candidates better than for SnapKV and H2O on LongBench, and faithfully on RULER.", "tab:app-calib-l2norm"))

# C: B2 winner transfer
parts.append(r"""
\section{Winner Transfer Across Budgets}
\label{app:transfer}

Each Stage 2 winner was found once by the unconstrained search at its natural average budget, then rescaled to each target budget with no further search (exact rule in Appendix~\ref{app:repro}). Table~\ref{tab:app-transfer} compares it with uniform allocation at the same budget. @@TRANSFER_SENTENCE@@
""")
b2 = tables("B2_winner_transfer.md")[0]
rows = [[CAT[r[1]], MET[r[2]], r[3], r[4], r[5], r[6], r[7], neg(r[8])] for r in b2]
sk_t = sum(not r[8].startswith("-") for r in b2)
ada_t, ada_tn = 0, 0
for cat, b in sorted(ada, key=lambda k: (order.index(k[0]), k[1])):
    v = ada[(cat, b)]
    if "winner" not in v:
        continue
    u = v.get("uniform", ada_u64 if (cat, b) == ("RULER_ALL", 64) else None)
    d = v["winner"] - u
    ada_t += d > 0; ada_tn += 1
    rows.append([CAT[cat], "AdaKV", str(ADA_NATURAL[cat]), str(b), str(ada_floor(cat, b)), f"{u:.2f}", f"{v['winner']:.2f}", neg(f"{d:+.2f}")])
l2_t = 0
for cat, b in l2_keys:
    v = {a: f for a, _, f in l2[(cat, b)]}
    d = v["winner"] - v["uniform"]
    l2_t += d > 0
    rows.append([CAT[cat], "L2Norm", str(l2_nat[cat]), str(b), "64", f"{v['uniform']:.2f}", f"{v['winner']:.2f}", neg(f"{d:+.2f}")])
print(f"transfer: SnapKV/H2O {sk_t}/{len(b2)}, AdaKV {ada_t}/{ada_tn}, L2Norm {l2_t}/{len(l2_keys)}, "
      f"total {sk_t + ada_t + l2_t}/{len(b2) + ada_tn + len(l2_keys)}")
parts[-1] = parts[-1].replace("@@TRANSFER_SENTENCE@@",
    f"The rescaled winner beats uniform in {sk_t + ada_t + l2_t} of {len(b2) + ada_tn + len(l2_keys)} cells (SnapKV and H2O: {sk_t}/{len(b2)}; AdaKV: {ada_t}/{ada_tn}; L2Norm: {l2_t}/{len(l2_keys)}). "
    r"For AdaKV RULER B64 only the rescaled winner was run, so it is compared with the uniform-64 configuration from Stage 2.")
parts.append(float_("table*", tabular("l l r r r r r r", ["Category", "Method", "Natural avg.", "B", "Floor", "Uniform", "Rescaled winner", r"$\Delta$"], rows, size=r"\scriptsize", sep="3pt"),
                    r"\textbf{Rescaled Stage 2 winner vs.\ uniform, full data.} Losses in bold.", "tab:app-transfer"))

# D: B1 search cost
cost, step1 = tables("B1_search_cost.md")
parts.append(r"""
\section{Search Cost}
\label{app:cost}

Table~\ref{tab:app-cost} compares the cost of one budget-constrained search against our EvolKV reproduction on the same A100-40GB machine and evaluation harness. EvolKV runs 60 generations $\times$ population 10 (600 evaluations on 30 calibration samples each); our Stage 4 uses fewer evaluations on a 10\% subsample (55--100 samples). Per-sample throughput is identical (about 2.5\,s on Code and 1.0\,s on SingleDoc). SnapKV LongBench Stage 4 run lengths were set by a saturation watchdog, so the last column normalizes to the 200-evaluation cap used for later runs; it is a projection, not the cost of the runs that produced the reported configurations, which Table~\ref{tab:app-capped} compares at matched compute. ``$\sim$'' marks wall-clock estimated from the cell's median evaluation time; ``$\approx$'' marks estimates from other budgets of the same category and method. Table~\ref{tab:app-step1} gives the one-time Stage 1 cost, which is paid once per (category, method) and reused at every budget.

The search-once protocols cost differently. EvolKV's main protocol runs one search at budget 128 (12.7 GPU-hours on Code, 5.2 on Single-Doc QA) and expands it. MOSAIC's Winner needs Stage 1 and the full-data re-evaluation of the Stage 2 Pareto front. On Single-Doc QA (SnapKV) these cost 16.5 and 3.6 GPU-hours (20 configurations), 20.1 in total, about four times EvolKV's single search. On Code, Stage 2 took 8.0 GPU-hours (11 configurations), and the Stage 1 logs were lost. The per-budget comparison in Table~\ref{tab:app-cost} is the matched-cost one, but MOSAIC's Stage 4 is seeded with the Winner and so also depends on Stages 1--2.
""")
rows = [[CAT[r[0]]] + [tex(c) for c in r[1:]] for r in cost[:-1]]
rows.append([r"\textbf{Total}", "", "", "", r"\textbf{53.7}", "", "", r"\textbf{76.9}", r"\textbf{51.1}"])
parts.append(float_("table*", tabular("l r r r r r r r r", ["Category", "B", "EvolKV evals", "Samples", "EvolKV GPU-h", "Our evals", "Samples", "Our GPU-h", "@200 evals"], rows, sep="3pt"),
                    r"\textbf{Per-budget search cost, EvolKV reproduction vs.\ MOSAIC Stage 4 (SnapKV, LongBench).}", "tab:app-cost"))

import capped_compare as _cc
_cap = _cc.compute()
parts.append(r"""
\paragraph{Compute-matched comparison.} The SnapKV Stage 4 searches as run cost more than direct EvolKV: 76.9 GPU-hours of search plus 8.0 for the full-data re-evaluation of the three candidates NAS-refined selects from (best heuristic shape, best LHS point, best guided proposal), 84.9 in total against EvolKV's 53.7. Table~\ref{tab:app-capped} therefore caps each search at the GPU-hours EvolKV used for the same cell, re-evaluation included. Evaluations are kept in the order they were run, and the cap always covers the 64-point initial design. In five cells the reported configuration was found within the cap, so the result is unchanged; in all five it is a heuristic shape or LHS point from the initial design, not a guided proposal. In Code B128 it was found at evaluation 454, beyond the cap of 151; the capped search would re-evaluate a guided proposal from evaluations 65--151 that we never re-evaluated, so its score is a lower bound given by the best re-evaluated candidate within the cap. The capped protocol costs 47.2 GPU-hours and beats direct EvolKV in 5 of 6 cells.
""")
_rows = []
for r in _cc.compute():
    d = round(r["capped"], 2) - round(r["evolkv"], 2)
    _rows.append([CAT[r["cat"]], str(r["b"]), f"{r['evolkv_h']:.1f}", f"{r['evolkv']:.2f}", str(r["actual_evals"]), f"{r['actual_h']:.1f}",
                  str(r["best_row"]), f"{r['full']:.2f}", str(r["capped_evals"]), f"{r['capped_h']:.1f}",
                  (r"$\geq$" if r["lower"] else "") + f"{r['capped']:.2f}", neg(f"{d:+.2f}")])
_rows.append([r"\textbf{Total}", "", rf"\textbf{{{sum(r['evolkv_h'] for r in _cap):.1f}}}", "", "", rf"\textbf{{{sum(r['actual_h'] for r in _cap):.1f}}}",
              "", "", "", rf"\textbf{{{sum(r['capped_h'] for r in _cap):.1f}}}", "", rf"\textbf{{{sum(round(r['capped'], 2) > round(r['evolkv'], 2) for r in _cap)}/6}}"])
parts.append(float_("table*", tabular("l r r r r r r r r r r r",
                    ["Category", "B", "EvolKV GPU-h", "EvolKV", "Run evals", "Run GPU-h", "Found at", "Run NAS-ref.", "Cap evals", "Cap GPU-h", "Cap NAS-ref.", r"$\Delta$"],
                    _rows, size=r"\scriptsize", sep="3pt"),
                    r"\textbf{NAS-refined vs.\ direct EvolKV at matched compute} (SnapKV, LongBench, full data, A100). Run: Stage 4 as run; ``Found at'' is the evaluation index of the reported configuration. Cap: the same search capped at EvolKV's GPU-hours for that cell. MOSAIC GPU-hours include the full-data re-evaluation of three candidates. $\Delta$: capped NAS-refined minus EvolKV; losses in bold.",
                    "tab:app-capped"))
rows = []
for r in step1:
    if r[0] == "CODE":
        rows.append(["Code", MET[r[1]], r"\multicolumn{2}{l}{logs lost}"])
    else:
        rows.append([CAT[r[0]], MET[r[1]], r[2], "n/a" if "no timing" in r[3] else tex(r[3])])
parts.append(float_("table", tabular("l l r r", ["Category", "Method", "Stage 1 evals", "GPU-h"], rows),
                    r"\textbf{One-time Stage 1 cost.} Code Stage 1 logs were lost; its winner survived.", "tab:app-step1"))

# D2: AdaKV search cost (from ADAKV_RESULTS/data/search_timings.csv)
parts.append(r"""
Table~\ref{tab:app-cost-adakv} lists every AdaKV search, run on one NVIDIA RTX A6000 (48\,GB) per search with sequential evaluation. GPU-hours are archive rows times mean seconds per evaluation. The searches were stopped by hand once the archive had settled, so their lengths vary (97--1000 evaluations); only MultiDoc B256 reached the 1000-evaluation cap. AdaKV evaluations are slower than SnapKV's (300--1600\,s each), so a single AdaKV Stage 4 search costs 18--113 GPU-hours, and all AdaKV searches together cost about 1{,}000 GPU-hours.
""")
rows = []
for r in _csv.DictReader(open(ADA / "search_timings.csv")):
    rows.append([r["stage"], r["benchmark"], r["run"].replace("RULER RULER", "RULER"), r["archive_rows"], r["guided_iterations"],
                 f"{float(r['mean_sec_per_eval']):.0f}", f"{float(r['archive_gpu_hours']):.1f}"])
tot = sum(float(r[6]) for r in rows)
rows.append([r"\textbf{Total}", "", "", "", "", "", rf"\textbf{{{tot:.0f}}}"])
parts.append(float_("table", tabular("l l l r r r r", ["Stage", "Bench.", "Run", "Evals", "Guided", "s/eval", "GPU-h"], rows, size=r"\scriptsize", sep="2.5pt"),
                    r"\textbf{AdaKV search cost} (RTX A6000). AdaKV RULER Stage 1 logs are not available.", "tab:app-cost-adakv"))

# E: B3 floor
tok, share = tables("B3_floor.md")
parts.append(r"""
\section{Choice of the Per-Layer Floor}
\label{app:floor}

SnapKV and H2O always retain an 8-token recent window, so a layer with budget $b$ selects only $b-8$ tokens by attention (Table~\ref{tab:app-floor-tokens}). At a floor of 16, only 8 tokens are chosen from contexts of thousands. Table~\ref{tab:app-floor} shows how often the best configuration of each cell places layers exactly at the floor: under the earlier floor of 16, up to two-thirds of layers sat there (RULER B1024, H2O), while at B1536 and B2048 no layer did, so those cells are floor-independent. Under floor 64 the floor is still active at low budgets. Figure~\ref{fig:app-floor16} shows the floor-16 RULER B1024 SnapKV configurations, which park many layers at 16.
""")
parts.append(float_("table", tabular("r r r", ["Layer budget", "Recent window", "Attention-selected"], tok),
                    r"\textbf{Tokens selected by attention at each per-layer budget.}", "tab:app-floor-tokens"))
rows = [[CAT[r[1]], r[2], MET[r[3]], r[4], LBL[r[5]], r[6], tex(r[7])] for r in share]
parts.append(float_("table", tabular("l r l r l r r", ["Cat.", "B", "Method", "Floor", "Best", "At floor", "Share"], rows, size=r"\scriptsize", sep="3pt"),
                    r"\textbf{Layers at the floor in each cell's best configuration.}", "tab:app-floor"))
parts.append(r"""\begin{figure}[t]
  \centering
  \includegraphics[width=\columnwidth]{figures/figure2_heatmap.png}
  \caption{\textbf{Floor-16 example (not used for the main results).} Per-layer budgets of five SnapKV configurations on RULER B1024, searched under the earlier floor of 16. The top BO configuration places 10 of 32 layers at 16, where only 8 tokens are selected by attention.}
  \label{fig:app-floor16}
\end{figure}
""")

# F: A6 RULER subtasks
niah, mean = tables("A6_niah_breakdown.md")
parts.append(r"""
\section{RULER Subtask Breakdown}
\label{app:ruler}

Table~\ref{tab:app-ruler} breaks each RULER cell into its 11 subtasks (S1--3: niah\_single; MK1--3: niah\_multikey; MQ: multiquery; MV: multivalue; CWE/FWE: common/frequent-word extraction; VT: variable tracking). ``Best'' is the configuration with the highest 11-subtask mean in that cell. Averaged over floor-clean cells (floor 64, plus B1536/B2048), NAS gains concentrate on the hardest needle subtasks: MK3 +44.6, S3 +37.4, S1 +33.4, versus CWE $-0.6$, FWE +2.7 and VT +3.6. The floor-16 H2O B1024 configuration trades CWE accuracy (98.3$\rightarrow$21.5) for needle retrieval.
""")
rows = []
for r in niah:
    if r[4].startswith("**"):
        rows.append(["", "", "", r"$\Delta$"] + [tex(c) for c in r[5:]])
        rows.append([r"\midrule"])
    else:
        rows.append([MET[r[0]], r[1], r[2], LBL[r[4]]] + r[5:])
body = []
for r in rows[:-1]:
    body.append(r[0] if r == [r"\midrule"] else " & ".join(r) + r" \\")
cols = ["S1", "S2", "S3", "MK1", "MK2", "MK3", "MQ", "MV", "CWE", "FWE", "VT", "NIAH", "All"]
content = (r"  \scriptsize" "\n" r"  \setlength{\tabcolsep}{2.5pt}" "\n"
           r"  \begin{tabular}{@{}l r r l " + "r " * 13 + "@{}}\n    \\toprule\n    Method & B & Floor & Config & "
           + " & ".join(cols) + r" \\" + "\n    \\midrule\n" + "\n".join("    " + b for b in body) + "\n    \\bottomrule\n  \\end{tabular}\n")
parts.append(float_("table*", content, r"\textbf{RULER subtask accuracy (string match, \%), uniform vs.\ best configuration per cell, SnapKV and H2O.}", "tab:app-ruler"))

# F2: AdaKV RULER subtasks
parts.append(r"""
Table~\ref{tab:app-ruler-adakv} gives the same breakdown for AdaKV. The pattern matches SnapKV and H2O: the largest gains are on niah\_multikey\_3 at B1024 and above.
""")
ada_rows = []
for b in sorted(b for c, b in ada if c == "RULER_ALL"):
    v = ada[("RULER_ALL", b)]
    ukey = ("RULER_ALL", b, "uniform") if "uniform" in v else ("RULER_ALL", 64, "uniform")
    non = {a: s for a, s in v.items() if a != "uniform"}
    best = max(non, key=non.get)
    U, Bst = ada_sub[ukey], ada_sub[("RULER_ALL", b, best)]
    def fmt(xs):
        return [f"{x:.1f}" for x in xs] + [f"{sum(xs[:8]) / 8:.1f}", f"{sum(xs) / 11:.1f}"]
    ada_rows.append(" & ".join(["AdaKV", str(b), str(ada_floor("RULER_ALL", b)), "uniform"] + fmt(U)) + r" \\")
    ada_rows.append(" & ".join(["AdaKV", str(b), str(ada_floor("RULER_ALL", b)), DISP(best)] + fmt(Bst)) + r" \\")
    dl = [y - x for x, y in zip(U, Bst)]
    dl_all = fmt(dl)
    ada_rows.append(" & ".join(["", "", "", r"$\Delta$"] + [tex(f"{float(x):+.1f}") for x in dl_all]) + r" \\")
    ada_rows.append(r"\midrule")
content = (r"  \scriptsize" "\n" r"  \setlength{\tabcolsep}{2.5pt}" "\n"
           r"  \begin{tabular}{@{}l r r l " + "r " * 13 + "@{}}\n    \\toprule\n    Method & B & Floor & Config & "
           + " & ".join(cols) + r" \\" + "\n    \\midrule\n" + "\n".join("    " + b for b in ada_rows[:-1]) + "\n    \\bottomrule\n  \\end{tabular}\n")
parts.append(float_("table*", content, r"\textbf{AdaKV RULER subtask accuracy (string match, \%), uniform vs.\ best configuration per cell.} B64 has only the rescaled winner, compared with uniform-64 from Stage 2.", "tab:app-ruler-adakv"))

# F3: L2Norm RULER subtasks (floor 64 everywhere)
l2_rows = []
for b in sorted(b for c, b in l2 if c == "RULER_ALL"):
    v = {a: f for a, _, f in l2[("RULER_ALL", b)]}
    best = max((a for a in v if a != "uniform"), key=v.get)
    def fmt(xs):
        return [f"{x:.1f}" for x in xs] + [f"{sum(xs[:8]) / 8:.1f}", f"{sum(xs) / 11:.1f}"]
    U, Bs = l2_sub[(b, "uniform")], l2_sub[(b, best)]
    l2_rows.append(" & ".join(["L2Norm", str(b), "uniform"] + fmt(U)) + r" \\")
    l2_rows.append(" & ".join(["L2Norm", str(b), DISP(best)] + fmt(Bs)) + r" \\")
    l2_rows.append(" & ".join(["", "", r"$\Delta$"] + [tex(f"{float(x):+.1f}") for x in fmt([y - x for x, y in zip(U, Bs)])]) + r" \\")
    l2_rows.append(r"\midrule")
content = (r"  \scriptsize" "\n" r"  \setlength{\tabcolsep}{2.5pt}" "\n"
           r"  \begin{tabular}{@{}l r l " + "r " * 13 + "@{}}\n    \\toprule\n    Method & B & Config & "
           + " & ".join(cols) + r" \\" + "\n    \\midrule\n" + "\n".join("    " + x for x in l2_rows[:-1]) + "\n    \\bottomrule\n  \\end{tabular}\n")
parts.append("\nTable~\\ref{tab:app-ruler-l2norm} gives the breakdown for L2Norm, whose RULER searches all used floor 64.\n")
parts.append(float_("table*", content, r"\textbf{L2Norm RULER subtask accuracy (string match, \%), uniform vs.\ best configuration per cell} (floor 64).", "tab:app-ruler-l2norm"))

# G: search dynamics (floor-16 run; kept for reference)
parts.append(r"""
\section{Search Dynamics}
\label{app:dynamics}

Figure~\ref{fig:app-stage1} shows what the unconstrained Stage 1 search explores, for AdaKV on LongBench: every evaluated configuration and the Pareto front on the calibration score (30\% subsample). Only the front is carried to Stage 2, where it is re-evaluated on full data (Figure~\ref{fig:pareto}); many front points do not keep their advantage there.

\begin{figure*}[t]
  \centering
  \includegraphics[width=\textwidth]{figures/adakv_stage1_archives.png}
  \caption{\textbf{Stage 1 search archives, AdaKV on LongBench (calibration scores).} Grey: every evaluated configuration; blue: the Pareto front on average budget vs.\ calibration score. ``Step 1'' in the plot title is Stage 1.}
  \label{fig:app-stage1}
\end{figure*}

Figure~\ref{fig:convergence} shows one Stage 4 search in detail: SnapKV on RULER at B1024, a cell searched under the earlier per-layer floor of 16 (Appendix~\ref{app:floor}). On RULER the calibration score tracks the full-data score (Appendix~\ref{app:calib}), so the best score found by BO is informative there; on LongBench it is not (Section~\ref{sec:which-stage}).

\begin{figure*}[t]
  \centering
  \includegraphics[width=0.95\textwidth]{figures/figure3_convergence_profiles.pdf}
  \caption{\textbf{Stage 4 search on SnapKV, RULER B1024 (floor 16).} \textit{(a)} Best calibration score found versus BO iteration. \textit{(b)} Per-layer budgets of uniform, the Winner and configurations from the Stage 4 search.}
  \label{fig:convergence}
\end{figure*}
""")

# H: AdaKV allocation shapes (figures/adakv_allocation_shapes.png from make_adakv_shapes.py)
parts.append(r"""
\section{AdaKV Per-Layer Allocations}
\label{app:adakv-shapes}

Figure~\ref{fig:app-adakv-shapes} is the AdaKV counterpart of Figure~\ref{fig:heatmap}, drawn with the same colour scale. AdaKV shows a weaker version of the middle-layer preference: layer 10 receives more than its uniform share in every AdaKV allocation and layers 13--16 in 63--84\%, but over the whole middle block (L10, L14--L20) the share is 56\%, against 60\% for SnapKV and H2O. The four identical RULER rows are the same configuration, which is best at four budgets.

\begin{figure*}[t]
  \centering
  \includegraphics[width=0.8\textwidth]{figures/adakv_allocation_shapes.png}
  \caption{\textbf{AdaKV per-layer allocations.} Colour shows each layer's budget divided by the row average on a log$_2$ scale (blue: more than the uniform share; red: less). \textit{Top:} MOSAIC's final configuration per cell (candidate type in parentheses). \textit{Bottom:} Stage 2 winner anchors at their natural average budget.}
  \label{fig:app-adakv-shapes}
\end{figure*}
""")

# EvolKV vs MOSAIC at a glance (facts from Section 6 / Ablation_Results.md / EvolKV paper)
parts.append(r"""
\section{MOSAIC and EvolKV at a Glance}
\label{app:evolkv-glance}

Table~\ref{tab:app-evolkv-glance} sets MOSAIC and EvolKV \citep{yu2025evolkv} side by side. Result rows are full-data scores for SnapKV on Llama-3-8B-Instruct from Section~\ref{sec:evolkv}. Each block pairs scores with the cost of the protocol that produced them: \emph{search once} (no search at the target budget) and \emph{search at each budget}.

\begin{table*}[t]
  \centering
  \footnotesize
  \setlength{\tabcolsep}{5pt}
  \renewcommand{\arraystretch}{1.15}
  \begin{tabular}{@{} p{0.24\textwidth} p{0.32\textwidth} p{0.36\textwidth} @{}}
    \toprule
    & \textbf{EvolKV} & \textbf{MOSAIC} \\
    \midrule
    Layer budgets & one per layer, optimized block by block (4 groups of 8, earlier groups frozen) & one per layer, all 32 optimized jointly \\
    What one search optimizes & task score at one fixed budget (128) & the budget--score trade-off over all budgets (Pareto front) \\
    Reaching other budgets & proportional rescaling of the budget-128 allocation & rescaling of the winner from its natural budget; optional per-budget refinement (Stage 4) \\
    Optimizer & CMA-ES, one group at a time & classifier-guided Bayesian optimization (MLP + differential evolution) \\
    Configuration selection & search score on 30 calibration samples & full-data re-evaluation (550--1{,}000 examples per task) \\
    Calibration optimism & search scores exceed full-data scores by 6.7--9.8 pts & not carried into reported scores; selection and reporting still share the same examples (Limitations) \\
    Eviction methods tested & SnapKV & SnapKV, H2O, AdaKV, L2Norm \\
    Benchmarks tested & LongBench Code, Single-Doc QA & LongBench (4 categories), RULER \\
    \midrule
    \multicolumn{3}{@{}l}{\textit{Search once: EvolKV expanded from B128 vs.\ MOSAIC Winner}} \\
    Code, B256/512/1024 & 55.99 / 56.82 / 56.42 & \textbf{57.33} / \textbf{58.16} / \textbf{58.52} \\
    Single-Doc, B256/512/1024 & \textbf{35.43} / 36.14 / 36.38 & 34.51 / \textbf{36.33} / \textbf{36.46} \\
    One-time cost (A100) & 12.7 (Code), 5.2 (Single-Doc) GPU-h & Code: 8.0 GPU-h for Stage 2, Stage 1 logs lost; Single-Doc: 20.1 GPU-h \\
    \midrule
    \multicolumn{3}{@{}l}{\textit{Search at each budget, MOSAIC capped at EvolKV's per-cell cost: EvolKV direct vs.\ MOSAIC NAS-refined}} \\
    Code, B128/512/1024 & 54.92 / 57.02 / 57.20 & \textbf{$\geq$55.73} / \textbf{58.01} / \textbf{58.91} \\
    Single-Doc, B128/512/1024 & 33.50 / \textbf{36.28} / 36.40 & \textbf{33.67} / 35.61 / \textbf{37.01} \\
    Cost, 6 cells (A100) & 53.7 GPU-h & 47.2 GPU-h capped (84.9 as run), plus the one-time Stages 1--2 that seed it \\
    \bottomrule
  \end{tabular}
  \caption{\textbf{EvolKV vs.\ MOSAIC.} Bold marks the better score within each block. Costs are measured on the same hardware and harness (Appendix~\ref{app:cost}). MOSAIC's search-once Winner wins on Code but needs a costlier one-time search; with each per-budget search capped at EvolKV's cost, NAS-refined wins 5 of 6 cells (Table~\ref{tab:app-capped}).}
  \label{tab:app-evolkv-glance}
\end{table*}
""")

# I: reproducibility details (all values read from the run code: NAS_Assets/run_longbench_lamp.py, run_ruler_lamp.py,
#    LAMP.py, eval_fixed_budgets_from_anchor.py, eval_evolkv_expansion.py)
parts.append(r"""
\section{Reproducibility Details}
\label{app:repro}

\paragraph{Budget decoding.} Stage 1 maps each coordinate $x_i \in [0,1]$ of a configuration to a discrete per-layer budget by equal-width bins over a grid $G$: seven levels from 64 to 4096 on RULER, for L2Norm and for H2O on Code, and five from 64 to 1024 for the other LongBench runs (SnapKV, AdaKV, H2O). Stages 3 and 4 use a continuous decoder that fixes the mean at the target $B$: with total $T = 32B$, it sets $b_i = T\,x_i / \sum_j x_j$, clamps layers to $[64, 4096]$ and redistributes the clamped surplus over the remaining layers until no bound is violated, then rounds with the largest-remainder method so that $\sum_i b_i = T$ exactly.

\paragraph{Rescaling the Stage 2 winner.} A winner with per-layer budgets $w_i$ is mapped to $x_i = 0.05 + 0.9\,w_i / \max_j w_j$ and decoded at each target $B$ as above. This keeps the order of the layers and the shape of the allocation, but it is an affine map rather than an exact proportional one: ratios between layers are compressed (a layer at the winner's minimum receives at least $0.05/0.95$ of the largest layer's budget). The same mapping seeds the winner into the Stage 4 search.

\paragraph{EvolKV expansion.} Following EvolKV's budget completion rule \citep{yu2025evolkv}, an allocation $k_i$ found at budget 128 is expanded to target $B$ by $b_i = k_i\,T / \sum_j k_j$, rounded with the largest-remainder method so that the mean is exactly $B$, and clipped to $[64, 4096]$ (neither bound binds for B256--B1024).

\paragraph{Evaluation settings.} Llama-3-8B-Instruct in float16, greedy decoding (one beam). LongBench uses the official prompts and chat template, middle truncation of inputs longer than 7{,}500 tokens (the first and last 3{,}750 tokens are kept), the official per-dataset output lengths (32--512 tokens) and the official metrics (F1 for QA, ROUGE-L for summarization, edit similarity for code). RULER uses its 11 subtasks at 4K context with string-match accuracy. SnapKV and H2O keep a fixed recent window of 8 tokens; SnapKV pools observation-window scores with a max-pool of kernel size 7. Calibration subsets are drawn per dataset with Python's \texttt{random.Random(42).sample} at the stated ratio, and the same seed is used throughout. All four methods use FlashAttention-2 for attention.

\paragraph{Hardware.} Searches and evaluations ran on four servers: SnapKV, H2O and AdaKV on NVIDIA A100 GPUs (the EvolKV comparison on the same A100-40GB machine and harness as MOSAIC), AdaKV additionally on RTX A6000 GPUs, and L2Norm on H100 GPUs.
""")


OUT.write_text("\n".join(parts))
print(f"wrote {OUT}")
