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


def _bd_table(blocks, cols, sep="4pt"):
    """Breakdown table: per method a centred header row, per budget two rows (Uniform, MOSAIC) with the
    budget centred over them. blocks = [(method, [(budget, uniform_vals, mosaic_vals, delta_vals), ...]), ...]."""
    n = 2 + len(cols)
    out = [r"  \scriptsize", rf"  \setlength{{\tabcolsep}}{{{sep}}}", r"  \renewcommand{\arraystretch}{0.92}",
           r"  \begin{tabular}{@{} c l " + "r" * len(cols) + r" @{}}", r"    \toprule",
           r"    \textbf{B} & & " + " & ".join(rf"\textbf{{{c}}}" for c in cols) + r" \\"]
    for m, cells in blocks:
        if not cells:
            continue
        out += [r"    \midrule", rf"    \multicolumn{{{n}}}{{c}}{{\textbf{{{m}}}}} \\", r"    \midrule"]
        for i, _cell in enumerate(cells):
            b, U, M, D = _cell[:4]
            _dag = len(_cell) > 4 and _cell[4]
            if i:
                out.append(rf"    \cmidrule(l){{1-{n}}}")
            U, M = list(U), list(M)
            for k in range(len(U)):  # bold the better of uniform and MOSAIC in each column (ties: neither)
                u, mm = float(U[k]), float(M[k])
                if mm > u:
                    M[k] = rf"\textbf{{{M[k]}}}"
                elif u > mm:
                    U[k] = rf"\textbf{{{U[k]}}}"
            if _dag:  # rescale-only cell: MOSAIC is the rescaled Stage 2 winner
                M[-1] += r"$^\dagger$"
            out.append(rf"    \multirow{{2}}{{*}}{{{b}}} & Uniform & " + " & ".join(U) + r" \\")
            out.append(r"     & MOSAIC & " + " & ".join(M) + r" \\")
    out += [r"    \bottomrule", r"  \end{tabular}"]
    return "\n".join(out) + "\n"


parts = [r"""\clearpage
\appendix
\makeatletter
\setlength{\@fptop}{0pt}\setlength{\@fpsep}{14pt}\setlength{\@fpbot}{0pt plus 1fil}
\setlength{\@dblfptop}{0pt}\setlength{\@dblfpsep}{14pt}\setlength{\@dblfpbot}{0pt plus 1fil}
\makeatother
\renewcommand{\topfraction}{0.97}\renewcommand{\bottomfraction}{0.9}\renewcommand{\textfraction}{0.03}
\renewcommand{\floatpagefraction}{0.85}\renewcommand{\dbltopfraction}{0.97}\renewcommand{\dblfloatpagefraction}{0.85}
\setcounter{topnumber}{4}\setcounter{dbltopnumber}{3}\setcounter{totalnumber}{6}

\section{Per-Cell Results}
\label{app:cells}


LongBench categories: Single-Doc QA (NarrativeQA, Qasper, MultiFieldQA-en), Multi-Doc QA (HotpotQA, 2WikiMQA, MuSiQue), Summarization (GovReport, QMSum, Multi-News) and Code (LCC, RepoBench-P); a category's score is the mean over its datasets, each scored on all of its 150--500 samples. RULER uses its 11 subtasks (NIAH-Single-1/2/3, NIAH-MultiKey-1/2/3, NIAH-MultiQuery, NIAH-MultiValue, Common-Words Extraction, Frequent-Words Extraction and Variable Tracking) at 4K context, 500 samples each; the RULER score is the mean over the 11 subtasks.

Tables~\ref{tab:app-cells} and~\ref{tab:app-cells-ruler} (Llama-3-8B-Instruct, LongBench and RULER) and Tables~\ref{tab:app-cells-mistral} and~\ref{tab:app-cells-mistral-ruler} (Mistral-7B-Instruct-v0.2) list every evaluated (task, method, budget) cell on full data. For each task they give three rows: uniform allocation, the rescaled Stage 2 winner (Winner, Stage 3) and NAS-refined, the best configuration of the Stage 4 search. MOSAIC's final configuration is the better of Winner and NAS-refined. Winner rows also cover budgets where Stage 4 did not run, so they give the full winner transfer of Appendix~\ref{app:transfer}. Appendix~\ref{app:breakdown} breaks these cells down into RULER subtasks and LongBench datasets.
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
parts.append("@@CELLS@@")
rows = []
for k in sorted((k for k in _c if k[0] == "L2Norm"), key=lambda k: (_ord[k[2]], k[3])):
    v = _c[k]
    rows.append([CAT[k[2]], str(k[3]), _f(v, "uniform"), _f(v, "winner"), _f(v, "bo"), _d(v)])
_wl = sum(max(_c[k]["winner"], _c[k]["bo"]) > _c[k]["uniform"] for k in _c if k[0] == "L2Norm")
_nl = sum(1 for k in _c if k[0] == "L2Norm")
print(f"per-cell three-way: SnapKV/H2O/AdaKV {_w3}/{_n3}, L2Norm {_wl}/{_nl}, total {_w3 + _wl}/{_n3 + _nl}")

# A3: dataset-level regressions hidden by category means (dataset_regressions.py)
import dataset_regressions as _dr
_drc = _dr.per_dataset()
_drrows = []
DSN = {"narrativeqa": "NarrativeQA", "qasper": "Qasper", "multifieldqa_en": "MultiFieldQA", "hotpotqa": "HotpotQA",
       "2wikimqa": "2WikiMQA", "musique": "MuSiQue", "lcc": "LCC", "repobench-p": "RepoBench-P", "gov_report": "GovReport",
       "qmsum": "QMSum", "multi_news": "MultiNews"}
for (m, c, b), v in sorted(_drc.items(), key=lambda kv: (["SnapKV", "H2O", "AdaKV", "L2Norm"].index(kv[0][0]), kv[0][1], kv[0][2])):
    d = {ds: v["final"][ds] - v["uniform"][ds] for ds in v["uniform"] if ds in v["final"]}
    lo = min(d, key=d.get)
    if d[lo] < 0:
        _drrows.append([m, CAT[c], str(b), DSN.get(lo, lo), neg(f"{d[lo]:+.2f}"), neg(f"{v['final_mean'] - v['uniform_mean']:+.2f}")])
_n_above = sum(not r[5].startswith(r"\textbf") for r in _drrows)
parts.append("@@RULER_SUB@@")
# A.2: LongBench dataset breakdown (replaces the dataset-regression table): uniform / final / delta per dataset
import csv as _csv2
_MR = Path(__file__).resolve().parents[2] / "ICLR_Final_Results"
_LAB = ["uniform", "heuristic", "winner", "random", "bo"]
_mlb = {}  # Mistral L2Norm LongBench: (cat, b) -> {"uniform": {ds}, "final": {ds}, "final_label"}
for _cat in ["CODE", "MULTI_DOCUMENT_QA", "SINGLE_DOCUMENT_QA", "SUMMARIZATION"]:
    for _d in (_MR / "MISTRAL_L2NORM_RESULTS" / _cat).glob("B*"):
        _f = _d / "eval_results.csv"
        if not _f.exists():
            continue
        _rs = {_LAB[int(r["arch"]) - 1]: r for r in _csv2.DictReader(open(_f))}
        _non = {k: r for k, r in _rs.items() if k != "uniform"}
        if "uniform" not in _rs or not _non:
            continue
        _bk = max(_non, key=lambda k: float(_non[k]["mean_score"]))
        _ds = lambda r: {k: float(v) for k, v in r.items() if k not in ("arch", "avg_budget", "nas_f2", "mean_score", "budgets")}
        _mlb[(_cat, int(_d.name[1:]))] = {"uniform": _ds(_rs["uniform"]), "final": _ds(_non[_bk]), "final_label": _bk}
_DSO = {"SINGLE_DOCUMENT_QA": ["narrativeqa", "qasper", "multifieldqa_en"], "MULTI_DOCUMENT_QA": ["hotpotqa", "2wikimqa", "musique"],
        "SUMMARIZATION": ["gov_report", "qmsum", "multi_news"], "CODE": ["lcc", "repobench-p"]}
_DSS = {"narrativeqa": "NQA", "qasper": "Qasper", "multifieldqa_en": "MFQA", "hotpotqa": "HQA", "2wikimqa": "2Wiki", "musique": "MuSiQue",
        "gov_report": "GovRep", "qmsum": "QMSum", "multi_news": "MNews", "lcc": "LCC", "repobench-p": "RepoB-P"}
_CN = {"SINGLE_DOCUMENT_QA": "Single-Doc QA", "MULTI_DOCUMENT_QA": "Multi-Doc QA", "SUMMARIZATION": "Summarization", "CODE": "Code"}
_mreg = sum(any(v["final"][x] < v["uniform"][x] for x in v["uniform"]) for v in _mlb.values())
_lb_start = len(parts)
parts.append(rf"""
\subsection{{LongBench Dataset Breakdown}}
\label{{app:dataset-reg}}

LongBench scores are category means over two or three datasets. Table~\ref{{tab:app-lb}} breaks each LongBench cell into its datasets, comparing uniform with MOSAIC's final configuration (the better of Winner and NAS-refined on the category mean). On Llama, the final configuration falls below uniform on at least one dataset in {len(_drrows)} of {len(_drc)} cells, and in {_n_above} of them the category mean is still above uniform; on Mistral (L2Norm) this happens in {_mreg} of {len(_mlb)} cells.
""")
# one merged table: column groups per category (datasets + mean), per method block two rows per budget
_CATS4 = ["SINGLE_DOCUMENT_QA", "MULTI_DOCUMENT_QA", "SUMMARIZATION", "CODE"]
_ncol = sum(len(_DSO[c]) + 1 for c in _CATS4)
_lines = [r"  \scriptsize", r"  \setlength{\tabcolsep}{3pt}", r"  \renewcommand{\arraystretch}{0.92}",
          r"  \begin{tabular}{@{} c l " + " ".join("r" * (len(_DSO[c]) + 1) for c in _CATS4) + r" @{}}", r"    \toprule"]
_g, _cm, _c0 = [], [], 3
for c in _CATS4:
    k = len(_DSO[c]) + 1
    _g.append(rf"\multicolumn{{{k}}}{{c}}{{\textbf{{{_CN[c]}}}}}")
    _cm.append(rf"\cmidrule(lr){{{_c0}-{_c0 + k - 1}}}")
    _c0 += k
_lines += [r"    & & " + " & ".join(_g) + r" \\", "    " + " ".join(_cm),
           r"    \textbf{B} & & " + " & ".join(" & ".join([_DSS[x] for x in _DSO[c]] + ["Mean"]) for c in _CATS4) + r" \\"]
# rescale-only LongBench cells (no Stage 4): MOSAIC's configuration is the rescaled winner (dagger), from cells.csv step3 rows
_resc = {}
for r in _csv2.DictReader(open(_MR / "analysis_outputs" / "cells.csv")):
    if r["benchmark"] == "longbench" and r["source"] == "step3" and r["label"] in ("uniform", "winner") and r["per_dataset"]:
        k = ({"snapkv": "SnapKV", "h2o": "H2O"}[r["method"]], r["category"], int(r["budget"]))
        _resc.setdefault(k, {})[r["label"]] = {kv.split("=")[0]: float(kv.split("=")[1]) for kv in r["per_dataset"].split(";")}
_resc = {k: {"uniform": v["uniform"], "final": v["winner"], "dagger": True} for k, v in _resc.items()
         if "uniform" in v and "winner" in v and k not in _drc and k[2] in (128, 256, 512, 1024)}
print("LongBench rescale-only breakdown cells:", sorted(_resc))
# regression count over every cell in the table (Stage 4 cells and rescale-only cells)
_allc = {**_drc, **_resc}
_mean = lambda d: sum(d.values()) / len(d)
_nreg = [k for k, v in _allc.items() if any(v["final"][x] < v["uniform"][x] for x in v["uniform"])]
_nabove = sum(_mean(_allc[k]["final"]) > _mean(_allc[k]["uniform"]) for k in _nreg)
_old = f"falls below uniform on at least one dataset in {len(_drrows)} of {len(_drc)} cells, and in {_n_above} of them"
assert _old in parts[_lb_start], "regression sentence"
parts[_lb_start] = parts[_lb_start].replace(_old, f"falls below uniform on at least one dataset in {len(_nreg)} of {len(_allc)} cells, and in {_nabove} of them")
print(f"LongBench regressions: {len(_nreg)}/{len(_allc)}, category mean still above uniform in {_nabove}")
_src = [(m, {(c, b): v for (mm, c, b), v in list(_drc.items()) + list(_resc.items()) if mm == m}) for m in ["SnapKV", "H2O", "AdaKV", "L2Norm"]]
_src.append(("L2Norm (Mistral)", dict(_mlb)))
for _m, _cs in _src:
    _buds = sorted({b for (_, b) in _cs})
    if not _buds:
        continue
    _lines += [r"    \midrule", rf"    \multicolumn{{{2 + _ncol}}}{{c}}{{\textbf{{{_m}}}}} \\", r"    \midrule"]
    for bi, _b in enumerate(_buds):
        if bi:
            _lines.append(rf"    \cmidrule(l){{1-{2 + _ncol}}}")
        U, M = [], []
        for c in _CATS4:
            v = _cs.get((c, _b))
            if v is None:
                U += ["--"] * (len(_DSO[c]) + 1); M += ["--"] * (len(_DSO[c]) + 1); continue
            uu = [v["uniform"][x] for x in _DSO[c]]; ff = [v["final"][x] for x in _DSO[c]]
            uu.append(sum(uu) / len(uu)); ff.append(sum(ff) / len(ff))
            for a_, b_ in zip(uu, ff):
                us, ms = f"{a_:.2f}", f"{b_:.2f}"
                if float(ms) > float(us):
                    ms = rf"\textbf{{{ms}}}"
                elif float(us) > float(ms):
                    us = rf"\textbf{{{us}}}"
                U.append(us); M.append(ms)
            if v.get("dagger"):
                M[-1] += r"$^\dagger$"
        _lines.append(rf"    \multirow{{2}}{{*}}{{{_b}}} & Uniform & " + " & ".join(U) + r" \\")
        _lines.append(r"     & MOSAIC & " + " & ".join(M) + r" \\")
_lines += [r"    \bottomrule", r"  \end{tabular}"]
parts.append(float_("table*", "\n".join(_lines) + "\n",
                    r"\textbf{LongBench dataset scores, uniform vs.\ MOSAIC per cell} (full data); bold: the better of the two in each column. NQA: NarrativeQA; MFQA: MultiFieldQA-en; HQA: HotpotQA; 2Wiki: 2WikiMQA; GovRep: GovReport; MNews: Multi-News; RepoB-P: RepoBench-P. $^\dagger$Rescaled Stage 2 winner (no Stage 4 search). ``--'': not run. L2Norm (Mistral): Mistral-7B-Instruct-v0.2; other blocks Llama-3-8B-Instruct.", "tab:app-lb", pos="tp"))
_lb_parts = parts[_lb_start:]
del parts[_lb_start:]

# B: A5 calibration fidelity
parts.append(r"""
\section{Calibration Scores vs.\ Full-Data Scores}
\label{app:calib}

MOSAIC scores configurations on a calibration subsample while it searches and on the full data when it selects. Figure~\ref{fig:app-calib} shows why both are needed: calibration orders configurations broadly like the full data, but the configuration it ranks first is often not the full-data best, and selection keeps only the first. The Stage 4 searches analysed here use a 10\% subsample for all four methods on both benchmarks; Stage 1 uses 30\% on LongBench and 10\% on RULER.

\paragraph{Stage 4 (Figure~\ref{fig:app-calib}a, b).} All candidates of a Stage 4 cell share one average budget, so their ranking tests calibration directly. Panel (a) gives Kendall's $\tau$ between the calibration and full-data rankings of each cell's re-evaluated candidates, and panel (b) the regret, the full-data points lost by taking the calibration-best candidate instead of the best re-evaluated one. On LongBench the median $\tau$ per method is 0.00 to 0.55, and calibration picks the full-data best in only 4 of 13 cells for SnapKV, 2 of 16 for H2O, 2 of 9 for AdaKV and 10 of 16 for L2Norm; on RULER it picks the full-data best in 20 of 21 cells (Table~\ref{tab:app-calib-summary}).

\paragraph{Stage 1 fronts (Figure~\ref{fig:app-calib}c, d).} Panels (c) and (d) compare each Stage 1 Pareto front's calibration scores with its Stage 2 full-data re-evaluation. On a front both scores rise with budget, so the front's overall order agrees ($\tau$ 0.78 to 1.00; in 13 of 15 fronts $\tau$ equals that between average budget and full-data score). Stage 2, however, keeps only the top configuration. The calibration-top configuration is the most expensive on the front in 13 of 15 SnapKV, H2O and L2Norm fronts, and full data prefers a cheaper one in 4 of 15 (by up to 0.73 points; none of L2Norm's 4 LongBench fronts). AdaKV is omitted: its Stage 1 calibration scores survive only as the plots in Figure~\ref{fig:app-stage1}. Re-scoring a front costs only its 4 to 19 configurations.
""")
_calcells = []  # (bench, method, tau, regret, correct pick)
for r in a5:
    _calcells.append(("LongBench" if r[0] == "longbench" else "RULER", MET[r[3]], float(r[6]), float(r[11]), r[7] == r[9], r[1], int(r[2])))

# B0: Stage 4 calibration summary (formerly main-text Table 1)
parts.append(r"""
""")
parts.append(float_("table", r"  \footnotesize\setlength{\tabcolsep}{2.5pt}" + "\n  \\input{tables/table_calib_stage4.tex}\n",
                    r"\textbf{Stage 4 calibration (10\% subset) vs.\ full-data scores, summary.} Cells: (task, budget) pairs. Gap: mean calibration minus full-data score. $\tau$: mean Kendall correlation between the two rankings of each cell's re-evaluated configurations. Picks: cells where the calibration-best candidate is also full-data best. Regret: mean full-data points lost by trusting calibration.",
                    "tab:app-calib-summary", pos="!htbp"))

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
for (cat, b), v in _cal.items():
    c, f = [x[1] for x in v], [x[2] for x in v]
    pick, best = max(v, key=lambda x: x[1]), max(v, key=lambda x: x[2])
    _calcells.append(("RULER" if cat == "RULER_ALL" else "LongBench", "AdaKV", _tau(c, f), best[2] - pick[2], pick is best, cat, b))

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
for cat, b in l2_keys:
    v = l2[(cat, b)]
    c, f = [x[1] for x in v], [x[2] for x in v]
    pick, best = max(v, key=lambda x: x[1]), max(v, key=lambda x: x[2])
    _calcells.append(("RULER" if cat == "RULER_ALL" else "LongBench", "L2Norm", _tau(c, f), best[2] - pick[2], pick is best, cat, b))
# figure data: x = method index, LongBench left / RULER right of it, small deterministic jitter
_FD = Path(__file__).resolve().parent / "figures" / "data"
_MO = ["SnapKV", "H2O", "AdaKV", "L2Norm"]
_ann, _med = [], []
for bench, off in [("LongBench", -0.18), ("RULER", 0.18)]:
    with open(_FD / f"calib_{bench}.dat", "w") as fh:
        fh.write("x tau regret\n")
        for mi, m in enumerate(_MO):
            cs = sorted([c for c in _calcells if c[0] == bench and c[1] == m], key=lambda c: c[2])
            for k, c in enumerate(cs):
                fh.write(f"{mi + 1 + off + 0.035 * ((k % 5) - 2):.3f} {c[2]:.3f} {c[3]:.3f}\n")
            if cs:
                med = lambda xs: sorted(xs)[len(xs) // 2] if len(xs) % 2 else sum(sorted(xs)[len(xs) // 2 - 1:len(xs) // 2 + 1]) / 2
                _med.append((mi + 1 + off, med([c[2] for c in cs]), med([c[3] for c in cs])))
                _ann.append((mi + 1 + off, f"{sum(c[4] for c in cs)}/{len(cs)}"))
with open(_FD / "calib_cells.csv", "w") as fh:  # per-cell rows behind Figure (calibration); supplementary material
    fh.write("model,benchmark,method,category,budget,kendall_tau,regret,calibration_pick_is_full_data_best\n")
    fh.write("".join(f"Llama-3-8B-Instruct,{c[0]},{c[1]},{c[5]},{c[6]},{c[2]:.4f},{c[3]:.4f},{c[4]}\n" for c in sorted(_calcells, key=lambda c: (c[0], _MO.index(c[1]), c[5], c[6]))))
with open(_FD / "calib_median.dat", "w") as fh:
    fh.write("x tau regret\n" + "".join(f"{x:.3f} {t:.3f} {r:.3f}\n" for x, t, r in _med))
with open(_FD / "calib_picks.tex", "w") as fh:
    fh.write("".join(rf"\node[pick] at (axis cs:{x:.3f},1.22) {{{t}}};" + "\n" for x, t in _ann))
print("calibration figure cells:", {(b, m): sum(1 for c in _calcells if c[0] == b and c[1] == m) for b in ("LongBench", "RULER") for m in _MO},
      "picks:", [t for _, t in _ann])
import calib_stage1 as _c1
_s1 = _c1.rows()
# L2Norm Stage 1 fronts (30% calibration, confirmed by the user 2026-10-06): search score nas_f2 vs Stage 2 full-data score
_L2U = _c1.RES / "LLAMA_L2NORM_RESULTS"
_s1[("LongBench", "l2norm")] = [_c1.front(_L2U / c / "unconstrained" / "eval_results.csv", "nas_f2", "mean_score")
                                for c in ["SINGLE_DOCUMENT_QA", "MULTI_DOCUMENT_QA", "SUMMARIZATION", "CODE"]]
_s1[("RULER", "l2norm")] = [_c1.front(_L2U / "RULER_ALL" / "unconstrained" / "eval_results.csv", "nas_f2", "mean_score")]
_M1 = {"snapkv": "SnapKV", "h2o": "H2O", "adakv": "AdaKV", "l2norm": "L2Norm"}
# AdaKV: no per-configuration Stage 1 calibration scores (archives survive only as plots), so its anchor-vs-best regret,
# a different measurement, is left out of the bottom row; it is disclosed in Limitations instead
for _k in [("LongBench", "adakv"), ("RULER", "adakv")]:
    _s1.pop(_k)
_med1 = []
for bench, off in [("LongBench", -0.18), ("RULER", 0.18)]:
    with open(_FD / f"calib_s2_tau_{bench}.dat", "w") as ft, open(_FD / f"calib_s2_reg_{bench}.dat", "w") as fr:
        ft.write("x tau\n"); fr.write("x regret\n")
        for (bb, m), fronts in _s1.items():
            if bb != bench:
                continue
            mi = _MO.index(_M1[m])
            for k, x in enumerate(fronts):
                xx = mi + 1 + off + 0.035 * ((k % 5) - 2)
                if x["tau"] is not None:
                    ft.write(f"{xx:.3f} {x['tau']:.3f}\n")
                fr.write(f"{xx:.3f} {x['regret']:.3f}\n")
            taus = sorted(x["tau"] for x in fronts if x["tau"] is not None); regs = sorted(x["regret"] for x in fronts)
            md = lambda v: (v[len(v) // 2] if len(v) % 2 else (v[len(v) // 2 - 1] + v[len(v) // 2]) / 2) if v else None
            _med1.append((mi + 1 + off, md(taus), md(regs)))
with open(_FD / "calib_s2_tau_median.dat", "w") as fh:
    fh.write("x tau\n" + "".join(f"{x:.3f} {t:.3f}\n" for x, t, _ in _med1 if t is not None))
with open(_FD / "calib_s2_reg_median.dat", "w") as fh:
    fh.write("x regret\n" + "".join(f"{x:.3f} {r:.3f}\n" for x, _, r in _med1))
_lbf = [x for (bb, _), v in _s1.items() if bb == "LongBench" for x in v]
print(f"Stage 1 fronts: LongBench picks {sum(x['ok'] for x in _lbf)}/{len(_lbf)}")
import subprocess as _sp
_sp.run(["pdflatex", "-interaction=nonstopmode", "figure_calib.tex"], cwd=Path(__file__).resolve().parent / "figures", stdout=_sp.DEVNULL, check=True)
parts.append(r"""\begin{figure*}[t]
  \centering
  \includegraphics[width=0.92\textwidth]{figures/figure_calib.pdf}
  \caption{\textbf{Calibration vs.\ full-data scores, Llama-3-8B-Instruct.} Circles: LongBench; triangles: RULER; bars: medians. Top: Stage 4 (10\% subset on both benchmarks), one marker per evaluated (task, budget) cell, whose candidates share one budget. Bottom: Stage 1 Pareto fronts (30\% on LongBench, 10\% on RULER) against their Stage 2 full-data re-evaluation, one marker per front; AdaKV is omitted from the bottom row: its Stage 1 calibration scores survive only as plots (Figure~\ref{fig:app-stage1}). (a, c) Kendall's $\tau$ between the calibration and full-data rankings. On a front both scores rise with budget, so (c) is high and in 13 of 15 fronts equals $\tau$ between average budget and full-data score: it reflects the budget trend, not whether calibration finds the top configuration. (b, d) Regret: full-data points lost by taking the calibration-top configuration instead of the best re-evaluated one. In (d), full data prefers a cheaper configuration than the calibration-top one in 4 of 15 SnapKV, H2O and L2Norm fronts (up to 0.73 points). ``Best'' refers to the re-evaluated pool only, and a zero median regret does not mean calibration always picks correctly (Table~\ref{tab:app-calib-summary} gives the Stage 4 counts).}
  \label{fig:app-calib}
\end{figure*}
""")

# B4: calibration-ratio case study (AB_calibration_ratio.md)
_cr = tables("AB_calibration_ratio.md")[0]
parts.append(r"""
\paragraph{Calibration ratio: a case study.} Table~\ref{tab:app-calib-ratio} rescores the 24 configurations of one SnapKV Stage 4 search (Code, B512) on a 30\% subsample and compares both subsamples with the full data. In this cell the larger subsample reduces the optimism (+1.37 against +5.10 points), ranks the configurations closer to the full data ($\tau$ 0.75 against 0.51), and picks the full-data best, which the 10\% subsample does not. This is a single cell, chosen because its guided proposal scored below uniform, so it illustrates rather than establishes the effect; a 30\% subsample also costs about three times as much per evaluation. A larger subsample reduces the noise but does not remove it: on the Stage 1 fronts, which use 30\% on LongBench, full data prefers a different configuration from the calibration-top one in 4 of 15 SnapKV, H2O and L2Norm fronts (by up to 0.73 points; Figure~\ref{fig:app-calib}d). MOSAIC therefore re-evaluates its candidates on full data at either ratio.
""")
parts.append(float_("table", tabular("l r r c r", ["Subsample", "Gap", r"$\tau$", "Picks best", "Regret"],
                    [[r[0].replace("%", r"\%"), tex(r[1]), tex(r[2]), r[3], r[4]] for r in _cr], size=r"\footnotesize", sep="4pt"),
                    r"\textbf{Calibration ratio, one cell} (SnapKV, Code B512, 24 configurations, full data as reference). Gap: mean calibration minus full-data score.", "tab:app-calib-ratio", pos="!htbp"))

# C: B2 winner transfer
parts.append(r"""
\section{Shape Transfer Across Tasks and Methods}
\label{app:transfer}
""")
b2 = tables("B2_winner_transfer.md")[0]
# H2O RULER B64/B256/B512: Stage 3 winner only in cells.csv; uniform from the raw H2O runs (h2o_ruler_uniform.py)
import h2o_ruler_uniform as _hru
_have = {(r[1], r[2], r[4]) for r in b2}
_hu = _hru.uniform()
for r in _csv.DictReader(open(Path(__file__).resolve().parents[2] / "ICLR_Final_Results" / "analysis_outputs" / "cells.csv")):
    b = int(r["budget"])
    if (r["benchmark"], r["method"], r["source"], r["label"]) == ("ruler", "h2o", "step3", "winner") \
            and ("RULER_ALL", "h2o", str(b)) not in _have and b in _hu:
        w = float(r["full_score"])
        b2.append(["ruler", "RULER_ALL", "h2o", "2180", str(b), r["era"], f"{_hu[b]:.2f}", f"{w:.2f}", f"{w - _hu[b]:+.2f}"])
b2.sort(key=lambda r: (r[0], r[1], r[2], int(r[4])))
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
# per-cell Stage 3 rows for make_stages.py (main-text Table 2 and the stage-comparison figure)
with open(Path(__file__).resolve().parent / "figures" / "data" / "stage3_rows.csv", "w", newline="") as _f:
    _w = _csv.writer(_f); _w.writerow(["category", "method", "natural", "budget", "floor", "uniform", "winner"])
    for r in rows:
        _w.writerow(r[:7])
print(f"transfer: SnapKV/H2O {sk_t}/{len(b2)}, AdaKV {ada_t}/{ada_tn}, L2Norm {l2_t}/{len(l2_keys)}, "
      f"total {sk_t + ada_t + l2_t}/{len(b2) + ada_tn + len(l2_keys)}")
# budget-matrix per-cell tables (replace the old per-cell and transfer tables), Llama and Mistral
import mistral as _mi
_DN = {"Code": "CODE", "MultiDoc": "MULTI_DOCUMENT_QA", "SingleDoc": "SINGLE_DOCUMENT_QA", "Summ": "SUMMARIZATION", "RULER": "RULER_ALL"}
_TL = {"CODE": "Code", "MULTI_DOCUMENT_QA": "Multi-Doc QA", "SINGLE_DOCUMENT_QA": "Single-Doc QA", "SUMMARIZATION": "Summarization", "RULER_ALL": "RULER"}
_cells, _nat = {}, {}
for (m, bench, cat, b), v in _c.items():
    _cells[(m, cat, b)] = dict(v)
for r in rows:  # Stage 3 rows: [Category, Method, natural, B, floor, uniform, winner, delta]
    k = (r[1], _DN[r[0]], int(r[3]))
    _nat[(r[1], _DN[r[0]])] = r[2]
    c = _cells.setdefault(k, {})
    c.setdefault("uniform", float(r[5])); c.setdefault("winner", float(r[6]))
_mcells = {(m, cat, b): dict(v) for (m, cat, b), v in _mi.load().items()}
_LB = ["CODE", "MULTI_DOCUMENT_QA", "SINGLE_DOCUMENT_QA", "SUMMARIZATION"]
def _matrix(cells, methods, cats, nat, short):
    """Budget matrix: budgets as columns, three rows (uniform / Winner / NAS-refined) per (method, task).
    With several tasks the method is a header row and the task labels the row group; with one task (RULER)
    the method labels the row group."""
    bud = sorted({b for (m, c, b) in cells if c in cats and m in methods})
    one = len(cats) == 1
    out = [r"\begin{tabular}{@{} c l " + "r" * len(bud) + r" @{}}", r"  \toprule",
           rf"  \textbf{{{'Method' if one else 'Task'}}} & & " + " & ".join(rf"\textbf{{{b}}}" for b in bud) + r" \\"]
    wins = n = 0
    nw = [0, 0]
    first = True
    for m in methods:
        mc = [c for c in cats if any((m, c, b) in cells for b in bud)]
        if not mc:
            continue
        if not one:
            out += [r"  \midrule", rf"  \multicolumn{{{2 + len(bud)}}}{{c}}{{\textbf{{{short.get(m, m)}}}}} \\", r"  \midrule"]
        for ci, c in enumerate(mc):
            if one:
                out.append(r"  \midrule")
            elif ci:
                out.append(rf"  \cmidrule(l){{2-{2 + len(bud)}}}")
            best = {}
            for b in bud:
                v = cells.get((m, c, b), {})
                vs = [v[k] for k in ("uniform", "winner", "bo") if k in v]
                best[b] = max(vs) if vs else None
                if "uniform" in v and "bo" in v:
                    n += 1; wins += max(v.get("winner", -1e9), v["bo"]) > v["uniform"]
                if "uniform" in v and "winner" in v:
                    nw[0] += 1; nw[1] += v["winner"] > v["uniform"]
            name = short.get(m, m) if one else _TL[c]
            lab = name + (rf"\\({nat[(m, c)]})" if (m, c) in nat else "")
            for ri, (k, rn) in enumerate([("uniform", "Uniform"), ("winner", "Winner"), ("bo", "NAS-ref.")]):
                vals = []
                for b in bud:
                    x = cells.get((m, c, b), {}).get(k)
                    vals.append("--" if x is None else (rf"\textbf{{{x:.2f}}}" if abs(x - best[b]) < 1e-9 else f"{x:.2f}"))
                lead = rf"\multirow{{3}}{{*}}{{\shortstack[c]{{{lab}}}}}" if ri == 0 else ""
                out.append(f"  {lead} & {rn} & " + " & ".join(vals) + r" \\")
    out += [r"  \bottomrule", r"\end{tabular}"]
    return "\n".join(out), wins, n, nw
_short = {v: k for k, v in _mi.NAMES.items()}
_LM = ["SnapKV", "H2O", "AdaKV", "L2Norm"]
_MM = [_mi.NAMES[m] for m in ["L2Norm", "SnapKV", "H2O", "AdaKV"]]
_T = {key: _matrix(*args) for key, args in {
    "llb": (_cells, _LM, _LB, _nat, {}), "lr": (_cells, _LM, ["RULER_ALL"], _nat, {}),
    "mlb": (_mcells, _MM, _LB, {}, _short), "mr": (_mcells, _MM, ["RULER_ALL"], {}, _short)}.items()}
_tot = lambda ks: (sum(_T[k][1] for k in ks), sum(_T[k][2] for k in ks), sum(_T[k][3][1] for k in ks), sum(_T[k][3][0] for k in ks))
_L, _M = _tot(["llb", "lr"]), _tot(["mlb", "mr"])
print(f"per-cell matrix: Llama MOSAIC {_L[0]}/{_L[1]}, Winner {_L[2]}/{_L[3]}; Mistral MOSAIC {_M[0]}/{_M[1]}, Winner {_M[2]}/{_M[3]}")
def _float(key, caption, label, pos="t", sep="9pt", env="table*", size="scriptsize", stretch="0.9"):
    t, w, n, nw = _T[key]
    return (rf"""
\begin{{{env}}}[{pos}]
  \centering
  \{size}
  \setlength{{\tabcolsep}}{{{sep}}}
  \renewcommand{{\arraystretch}}{{{stretch}}}
""" + t + rf"""
  \caption{{{caption} MOSAIC's final configuration beats uniform in {w} of {n} cells{' with a Stage 4 search' if n < nw[0] else ''}, and the Winner alone in {nw[1]} of {nw[0]}.}}
  \label{{{label}}}
\end{{{env}}}
""")
_cells_tex = (
    _float("llb", r"\textbf{Full-data results for every evaluated LongBench cell, Llama-3-8B-Instruct.} Per task: uniform, the rescaled Stage 2 winner (Winner) and NAS-refined (best of the Stage 4 search); bold: best in each column. The number under each task is the winner's natural average budget, at which Stage 1 found it. ``--'': not run.", "tab:app-cells", pos="tp", sep="4.6pt", env="table", size="footnotesize", stretch="0.9")
    + _float("lr", r"\textbf{Full-data results for every evaluated RULER cell, Llama-3-8B-Instruct.} Layout as in Table~\ref{tab:app-cells}; the number under each method is its winner's natural average budget. ``--'': not run (at B64, Winner and NAS-refined need a per-layer floor below 64). AdaKV at B64: only the rescaled winner was run, compared with Stage 2's uniform-64 configuration.", "tab:app-cells-ruler", sep="14pt", size="footnotesize", stretch="1.0")
    + _float("mlb", r"\textbf{Full-data results for every evaluated LongBench cell, Mistral-7B-Instruct-v0.2} (L2Norm). Layout as in Table~\ref{tab:app-cells}.", "tab:app-cells-mistral", sep="4.6pt", env="table", size="footnotesize", stretch="1.0")
    + _float("mr", r"\textbf{Full-data results for every evaluated RULER cell, Mistral-7B-Instruct-v0.2.} Layout as in Table~\ref{tab:app-cells-ruler}. ``--'': not run.", "tab:app-cells-mistral-ruler", sep="14pt", size="footnotesize", stretch="1.0"))
for _pi, _pt in enumerate(parts):
    if _pt == "@@CELLS@@":
        parts[_pi] = _cells_tex

# C2: cross-task and cross-method shape transfer (NAS_Assets/transfer_evals/*/B*/result.json)
import json as _json
_tr = {"C1_CODEshape_on_SDQA_snapkv": ("SnapKV Code", "SnapKV", "SINGLE_DOCUMENT_QA"),
       "C1_SDQAshape_on_CODE_snapkv": ("SnapKV Single-Doc", "SnapKV", "CODE"),
       "C2_h2oCODEshape_under_snapkv": ("H2O Code", "SnapKV", "CODE"),
       "C2_snapkvCODEshape_under_h2o": ("SnapKV Code", "H2O", "CODE")}
_trrows, _trraw = [], []
for tag, (shape, recv, cat) in _tr.items():
    for b in (128, 512, 1024):
        sc = _json.load(open(Path(__file__).resolve().parents[2] / "NAS_Assets" / "transfer_evals" / tag / f"B{b}" / "result.json"))["full_data_mean_score"]
        v = _tw.load()[(recv, "longbench", cat, b)]
        fin = max(v.get("winner", -1e9), v.get("bo", -1e9))
        _trraw.append((v["uniform"], sc, v["winner"], fin))
        _trrows.append([shape, f"{recv} {CAT[cat]}", str(b), f"{v['uniform']:.2f}", f"{sc:.2f}", neg(f"{sc - v['uniform']:+.2f}"),
                        f"{v['winner']:.2f}", f"{fin:.2f}"])
parts.append(r"""
Figure~\ref{fig:app-shape-transfer} applies a Stage 2 winner shape to a different task or eviction method, rescaled with the same mapping as Stage 3, and compares it with the receiving cell's uniform allocation, its own rescaled Winner and its final configuration. The tests cover SnapKV and H2O on Code and Single-Doc QA at B128, B512 and B1024.

\textbf{Across tasks, shapes do not transfer.} SnapKV's Code shape applied to Single-Doc QA, and its Single-Doc QA shape applied to Code, score below uniform at every budget (by 0.33 to 1.08 and 0.63 to 1.22 points), while each task's own Winner beats uniform in the same six cells. The layers that need more cache differ between the two tasks, so a shape found for one task is worse than uniform allocation on the other.

\textbf{Across eviction methods, shapes do transfer.} On Code, H2O's shape under SnapKV and SnapKV's shape under H2O beat uniform in all six cells ($+0.06$ to $+1.66$). They stay below the receiving method's own final configuration in every cell (by 0.18 to 1.23 points) and below its own Winner in 4 of 6; SnapKV's shape under H2O beats H2O's own Winner at B128 and B1024 ($+0.16$ and $+0.90$). Which layers need more cache therefore depends mainly on the task, so a shape found with one eviction method is a useful starting point for another, while a search with the receiving method still adds up to 1.23 points.
""")
# figure (replaces the transfer table): gain over the receiving cell's uniform, one panel per transfer; CSV for supplementary
_FDt = Path(__file__).resolve().parent / "figures" / "data"
with open(_FDt / "transfer_cells.csv", "w") as _fh:
    _fh.write("shape,applied_to,budget,uniform,transferred,own_winner,own_final\n")
    for _i in range(4):
        with open(_FDt / f"transfer_{_i + 1}.dat", "w") as _fd:
            _fd.write("x tr win fin\n")
            for _k, _r in enumerate(_trrows[3 * _i:3 * _i + 3]):
                _u, _t, _w, _f = _trraw[3 * _i + _k]
                _fd.write(f"{_k + 1} {_t - _u:.3f} {_w - _u:.3f} {_f - _u:.3f}\n")
                _fh.write(f"{_r[0]},{_r[1]},{_r[2]},{_u:.2f},{_t:.2f},{_w:.2f},{_f:.2f}\n")
import subprocess as _sp
_sp.run(["pdflatex", "-interaction=nonstopmode", "figure_transfer.tex"], cwd=Path(__file__).resolve().parent / "figures", stdout=_sp.DEVNULL, check=True)
parts.append(r"""\begin{figure*}[t]
  \centering
  \includegraphics[width=0.95\textwidth]{figures/figure_transfer.pdf}
  \caption{\textbf{Transferring winner shapes across tasks (a, b) and eviction methods (c, d)}, LongBench, full data. Each point is a gain over the receiving cell's uniform allocation at the same budget (dashed line): the transferred shape, rescaled as in Stage 3; the receiving cell's own rescaled Winner; and its own final configuration (the better of Winner and NAS-refined).}
  \label{fig:app-shape-transfer}
\end{figure*}
""")

# D: B1 search cost
cost, step1 = tables("B1_search_cost.md")
parts.append(r"""
\section{Search Cost}
\label{app:cost}

@@COST_TEXT@@
""")
import capped_compare as _cc
_cap = _cc.compute_evals(150)
_samp = {(r[0], int(r[1])): (r[2], r[3], r[6]) for r in cost[:-1]}  # EvolKV evals, EvolKV samples, our samples
_rows = []
for r in _cap:
    d = round(r["score"], 2) - round(r["evolkv"], 2)
    ev_n, ev_s, our_s = _samp[(r["cat"], r["b"])]
    _rows.append([CAT[r["cat"]], str(r["b"]), ev_n, ev_s, f"{r['evolkv_h']:.1f}", f"{r['evolkv']:.2f}",
                  str(r["evals"]), our_s, f"{r['h']:.1f}", f"{r['score']:.2f}", neg(f"{d:+.2f}")])
_ev_h, _our_h = sum(r["evolkv_h"] for r in _cap), sum(r["h"] for r in _cap)
_wins = sum(round(r["score"], 2) > round(r["evolkv"], 2) for r in _cap)
_d = [round(r["score"], 2) - round(r["evolkv"], 2) for r in _cap]
# per task, three budgets: Stage 4 + Stage 2 (+ Stage 1 at 180 evaluations where logged) vs. EvolKV direct
_tot = lambda c, extra: sum(r["h"] for r in _cap if r["cat"] == c) + extra
_evt = lambda c: sum(r["evolkv_h"] for r in _cap if r["cat"] == c)
_rows.append([r"\textbf{Total}", "", "", "", rf"\textbf{{{_ev_h:.1f}}}", "", "", "", rf"\textbf{{{_our_h:.1f}}}", "", rf"\textbf{{{_wins}/6}}"])
parts[-1] = parts[-1].replace("@@COST_TEXT@@", rf"""Table~\ref{{tab:app-cost}} compares one budget-constrained search per cell with our EvolKV reproduction (SnapKV, LongBench), on the same A100-40GB machine and evaluation harness. EvolKV runs 60 generations $\times$ population 10, 600 evaluations on 30 calibration samples each. MOSAIC's Stage 4 runs at most 150 evaluations on a 10\% calibration subset (55--100 samples): we keep each run's evaluations $\leq$150 in the order they were run, and add the full-data re-evaluation of the three NAS-refined candidates. Both searches process a sample equally fast (about 2.5\,s on Code and 1.0\,s on Single-Doc QA), so cost is evaluations times samples, and MOSAIC spends it on fewer evaluations of larger samples. It costs no more than EvolKV in any cell ({_our_h:.1f} GPU-hours against {_ev_h:.1f} in total) and beats it in {_wins} of 6 cells (${min(x for x in _d if x > 0):+.2f}$ to ${max(_d):+.2f}$); it loses Single-Doc QA B512 by {-min(_d):.2f} points.

MOSAIC has four stages. Stages 1--2 run once per (task, method) and produce the Winner; Stages 3--4 rescale it to each budget and refine it there. Users can stop after Stages 1--2 and deploy the rescaled Winner, which beats direct EvolKV in all 6 cells (Section~\ref{{sec:evolkv}}), or also run Stage 4 at the budgets they need. Stage 2 re-evaluates the Stage 1 front on full data: 3.6 GPU-hours on Single-Doc QA (20 configurations) and 8.0 on Code (11 configurations). Table~\ref{{tab:app-step1}} gives the cost of the 180-evaluation Stage 1 for each task and method. With Stages 1--2 added, running all four stages costs more than EvolKV's direct searches at these three budgets (at least {_tot('CODE', 8.0):.1f} vs.\ {_evt('CODE'):.1f} GPU-hours on Code, {_tot('SINGLE_DOCUMENT_QA', 3.6 + 16.5 * 180 / 331):.1f} vs.\ {_evt('SINGLE_DOCUMENT_QA'):.1f} on Single-Doc QA).""")
parts.append(float_("table*", tabular("l r r r r r r r r r r",
                    [r"& & \multicolumn{4}{c}{EvolKV, direct} & \multicolumn{4}{c}{MOSAIC Stage 4, NAS-refined} & \\ \cmidrule(lr){3-6}\cmidrule(lr){7-10}" "\n    Category & B & Evals & Samples & GPU-h & Score & Evals & Samples & GPU-h & Score & $\Delta$"],
                    _rows, sep="4pt"),
                    r"\textbf{Per-budget search cost and score, EvolKV direct vs.\ MOSAIC Stage 4} (SnapKV, LongBench, full-data scores, A100). EvolKV: 600 evaluations plus one final evaluation. MOSAIC: $\leq$150 evaluations of each Stage 4 run; its GPU-hours include the full-data re-evaluation of three candidates but exclude the one-time Stages 1--2. $\Delta$: NAS-refined minus EvolKV; losses in bold.",
                    "tab:app-cost"))
rows = []
for r in step1:  # GPU-hours of 180 Stage 1 evaluations at each run's measured time per evaluation; runs without timing are left out
    if r[0] in ("CODE", "SUMMARIZATION") or "no timing" in r[3]:
        continue
    h = float(r[3].lstrip("~≈")) * 180 / int(r[2])
    rows.append([CAT[r[0]], MET[r[1]], (r"$\sim$" if r[3][0] in "~≈" else "") + f"{h:.1f}"])
parts.append(float_("table", tabular("l l r", ["Category", "Method", "GPU-h"], rows),
                    r"\textbf{MOSAIC Stage 1 cost}", "tab:app-step1"))

# E: B3 floor
tok, share = tables("B3_floor.md")
parts.append(r"""
\section{Choice of the Per-Layer Floor}
\label{app:floor}

SnapKV and H2O always retain an 8-token recent window, so a layer with budget $b$ selects only $b-8$ tokens by attention. At a floor of 16, only 8 tokens are chosen from contexts of thousands. Table~\ref{tab:app-floor} shows how often MOSAIC's final configuration in each cell places layers exactly at the floor. Under floor 64 the floor is still active at low budgets.
""")
# Layers at the floor in MOSAIC's final configuration (the better of Winner and NAS-refined). B3_floor.md counts the best
# configuration of any kind; where uniform is best (0 layers by construction), count MOSAIC's final configuration from cells.csv.
_fin = {}
for r in _csv2.DictReader(open(SRC / "cells.csv")):
    if r["source"] == "five_way" and r["label"] != "uniform":
        _k = (r["category"], r["method"], r["budget"])
        _b = [int(float(x)) for x in re.findall(r"[0-9.]+", r["budgets"])]
        _fin.setdefault(_k, {})[r["label"]] = (float(r["full_score"]), sum(x == 64 for x in _b))
_flo = {}
for r in share:
    n = r[6].split("/")[0]
    if r[5] == "uniform":
        c = _fin[(r[1], r[3], r[2])]
        nas = max((c[l] for l in ("heuristic", "random", "bo")), key=lambda v: v[0])
        n = str(max(c["winner"], nas, key=lambda v: v[0])[1])
    _flo[(r[1], r[3], r[2])] = n + (r"$^\dagger$" if r[4] == "16" else "")
_FB = ["128", "256", "512", "1024", "1536", "2048"]
rows = []
for c in ["CODE", "MULTI_DOCUMENT_QA", "SINGLE_DOCUMENT_QA", "SUMMARIZATION", "RULER_ALL"]:
    for i, m in enumerate(["snapkv", "h2o"]):
        if any((c, m, b) in _flo for b in _FB):
            rows.append([CAT[c] if i == 0 else "", MET[m]] + [_flo.get((c, m, b), "--") for b in _FB])
parts.append(float_("table", tabular("l l " + "r" * len(_FB), ["Task", "Method"] + _FB, rows, sep="4pt"),
                    r"\textbf{Layers at the floor (out of 32) in MOSAIC's final configuration of each cell.} $^\dagger$Searched under the earlier floor of 16; all other cells use floor 64. --: no Stage 4 search in this cell.", "tab:app-floor"))

# E2: controlled floor ablation (AB_floor.md)
_fl = tables("AB_floor.md")[0]
parts.append(r"""
\paragraph{Controlled comparison.} Table~\ref{tab:app-floor-ablation} decodes the same rescaled SnapKV winner under both floors and evaluates both on full data. Floor 64 is better in three cells, all at B128 (by 0.37--1.10 points), the two are tied in two cells, and floor 16 is better in one (by 0.26). The differences concentrate at the lowest budget, where the floor binds most often.
""")
parts.append(float_("table", tabular("l r r r r", ["Cell", "Uniform", "Floor 64", "Floor 16", r"$\Delta$ (16$-$64)"],
                    [[r[0].replace("SINGLE_DOCUMENT_QA", "SingleDoc").replace("MULTI_DOCUMENT_QA", "MultiDoc").replace("CODE", "Code"), r[1], r[2], r[3], neg(r[4])] for r in _fl],
                    size=r"\scriptsize", sep="3pt"),
                    r"\textbf{Same rescaled winner under floor 64 and floor 16} (SnapKV, LongBench, full data). Negative $\Delta$ (bold): floor 64 is better.", "tab:app-floor-ablation", pos="!htbp"))

# F: A6 RULER subtasks (A.1)
niah, mean = tables("A6_niah_breakdown.md")
_f_start = len(parts)
parts.append(r"""
\subsection{RULER Subtask Breakdown}
\label{app:ruler}

Tables~\ref{tab:app-ruler} (Llama-3-8B-Instruct) and~\ref{tab:app-ruler-mistral} (Mistral-7B-Instruct-v0.2) break each RULER cell into its 11 subtasks (S1--3: niah\_single; MK1--3: niah\_multikey; MQ: multiquery; MV: multivalue; CWE/FWE: common/frequent-word extraction; VT: variable tracking; NIAH: mean of the eight needle subtasks; All: mean of all 11), comparing uniform with MOSAIC's final configuration. Averaged over floor-clean cells (floor 64, plus B1536/B2048), NAS gains concentrate on the hardest needle subtasks: MK3 +31.9, S3 +28.0, S1 +23.8, versus CWE +0.8, FWE +3.5 and VT +5.6. The floor-16 H2O B1024 configuration trades CWE accuracy (98.3$\rightarrow$21.5) for needle retrieval.
""")
cols = ["S1", "S2", "S3", "MK1", "MK2", "MK3", "MQ", "MV", "CWE", "FWE", "VT", "NIAH", "All"]
def fmt(xs):
    return [f"{x:.1f}" for x in xs] + [f"{sum(xs[:8]) / 8:.1f}", f"{sum(xs) / 11:.1f}"]
def _dl(U, B):
    return [tex(f"{float(x):+.1f}") for x in fmt([y - x for x, y in zip(U, B)])]
_blk = {}
_k = 0
while _k < len(niah):
    u, bst, dd = niah[_k], niah[_k + 1], niah[_k + 2]
    assert u[4] == "uniform" and dd[4].startswith("**"), (u, dd)
    _blk.setdefault(MET[u[0]], []).append((u[1], u[5:], bst[5:], [tex(c) for c in dd[5:]]))
    _k += 3

# F2: AdaKV RULER subtasks
parts.append(r"""
For AdaKV the pattern matches SnapKV and H2O: the largest gains are on niah\_multikey\_3 at B1024 and above.
""")
_ab = []
for b in sorted(b for c, b in ada if c == "RULER_ALL"):
    v = ada[("RULER_ALL", b)]
    ukey = ("RULER_ALL", b, "uniform") if "uniform" in v else ("RULER_ALL", 64, "uniform")
    non = {a: s_ for a, s_ in v.items() if a != "uniform"}
    best = max(non, key=non.get)
    U, Bst = ada_sub[ukey], ada_sub[("RULER_ALL", b, best)]
    _ab.append((str(b), fmt(U), fmt(Bst), _dl(U, Bst)))
# F3: L2Norm RULER subtasks
_lb = []
for b in sorted(b for c, b in l2 if c == "RULER_ALL"):
    v = {a: f for a, _, f in l2[("RULER_ALL", b)]}
    best = max((a for a in v if a != "uniform"), key=v.get)
    U, Bs = l2_sub[(b, "uniform")], l2_sub[(b, best)]
    _lb.append((str(b), fmt(U), fmt(Bs), _dl(U, Bs)))
_SUBS = ["niah_single_1", "niah_single_2", "niah_single_3", "niah_multikey_1", "niah_multikey_2", "niah_multikey_3",
         "niah_multiquery", "niah_multivalue", "cwe", "fwe", "vt"]
# H2O RULER rescale-only cells (B64/B256/B512): uniform from the raw H2O runs (h2o_ruler_uniform.RUNS, same server),
# MOSAIC = the rescaled Stage 2 winner from cells.csv step3 rows
_have = {int(c[0]) for c in _blk.get("H2O", [])}
_hw = {}
for r in _csv2.DictReader(open(_MR / "analysis_outputs" / "cells.csv")):
    if (r["benchmark"], r["method"], r["source"], r["label"]) == ("ruler", "h2o", "step3", "winner") and int(r["budget"]) not in _have:
        _hw[int(r["budget"])] = {kv.split("=")[0]: float(kv.split("=")[1]) for kv in r["per_dataset"].split(";")}
for _b, _w in sorted(_hw.items()):
    _f = _hru.RUNS / f"h2o_budget_{_b}" / f"meta-llama-3-8b-instruct_{_b}" / "4096" / "results.csv"
    if not _f.exists():
        continue
    _u = {r["dataset"]: r for r in _csv2.DictReader(open(_f))}["H2O"]
    U = [float(_u[x]) for x in _SUBS]; W = [_w[x] for x in _SUBS]
    _blk["H2O"].append((str(_b), fmt(U), fmt(W), _dl(U, W), True))
_blk["H2O"].sort(key=lambda c: int(c[0]))
# dagger every Llama RULER cell without a Stage 4 search (as in main Table 3)
def _dagger(m, cells):
    return [tuple(c[:4]) + ("bo" not in _c.get((m, "ruler", "RULER_ALL", int(c[0])), {}),) for c in cells]
_blk = {m: _dagger(m, v) for m, v in _blk.items()}
_ab, _lb = _dagger("AdaKV", _ab), _dagger("L2Norm", _lb)
print("RULER rescale-only (dagger):", {m: [c[0] for c in v if c[4]] for m, v in list(_blk.items()) + [("AdaKV", _ab), ("L2Norm", _lb)]})
print("H2O RULER rescale-only breakdown cells:", sorted(_hw))
parts.append(float_("table*", _bd_table([(m, _blk.get(m, [])) for m in ["SnapKV", "H2O"]] + [("AdaKV", _ab), ("L2Norm", _lb)], cols),
                    r"\textbf{RULER subtask accuracy (string match, \%), uniform vs.\ MOSAIC per cell, Llama-3-8B-Instruct.} $^\dagger$Rescaled Stage 2 winner (no Stage 4 search). AdaKV B64 has only the rescaled winner, compared with uniform-64 from Stage 2.", "tab:app-ruler", pos="tp"))

# F4: Mistral RULER subtasks (all four methods)
_SUBS = ["niah_single_1", "niah_single_2", "niah_single_3", "niah_multikey_1", "niah_multikey_2", "niah_multikey_3",
         "niah_multiquery", "niah_multivalue", "cwe", "fwe", "vt"]
_mrb = {}
for _m, _base in [("L2Norm", _MR / "MISTRAL_L2NORM_RESULTS" / "RULER_ALL"), ("SnapKV", _MR / "MISTRAL_RULER_RESULTS" / "SNAPKV" / "RULER_ALL"),
                  ("H2O", _MR / "MISTRAL_RULER_RESULTS" / "H2O" / "RULER_ALL"), ("AdaKV", _MR / "MISTRAL_RULER_RESULTS" / "ADAKV" / "RULER_ALL")]:
    for _b in sorted(int(d.name[1:]) for d in _base.glob("B*") if (d / "eval_results.csv").exists()):
        _rs = {_LAB[int(r["arch"]) - 1]: r for r in _csv2.DictReader(open(_base / f"B{_b}" / "eval_results.csv"))}
        _non = {k_: r for k_, r in _rs.items() if k_ != "uniform"}
        if "uniform" not in _rs or not _non:
            continue
        _bk = max(_non, key=lambda k_: float(_non[k_]["mean_score"]))
        U = [float(_rs["uniform"][x]) for x in _SUBS]; Bs = [float(_non[_bk][x]) for x in _SUBS]
        _mrb.setdefault(_m, []).append((str(_b), fmt(U), fmt(Bs), _dl(U, Bs)))
parts.append(float_("table*", _bd_table([(m, _mrb.get(m, [])) for m in ["SnapKV", "H2O", "AdaKV", "L2Norm"]], cols),
                    r"\textbf{RULER subtask accuracy (string match, \%), uniform vs.\ MOSAIC per cell, Mistral-7B-Instruct-v0.2.}", "tab:app-ruler-mistral", pos="tp"))
_f_end = len(parts)
_moved = parts[_f_start:_f_end]
del parts[_f_start:_f_end]
parts.remove("@@RULER_SUB@@")

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

# G2: search-budget curve (AB_search_budget_curve.md)
_sc = tables("AB_search_budget_curve.md")
_rows, _cells = [], {}
for r in _sc[0]:
    _cells.setdefault(r[0], {})[r[1].split(" ")[0]] = (r[1], r[5])
for cell, v in _cells.items():
    n = v["all"][0].split("(")[1].rstrip(")")
    _rows.append([cell.replace("SINGLE_DOCUMENT_QA", "SingleDoc").replace("CODE", "Code"), n, neg(v["64"][1]), neg(v["all"][1])])
_mean = {r[0]: r[1] for r in _sc[1]}
_rows.append([r"\textbf{Mean}", "", tex(_mean["64"]), tex(_mean["all"])])
parts.append(r"""
\paragraph{Search length on LongBench.} Table~\ref{tab:app-search-curve} takes eight SnapKV Stage 4 searches and, for each, the configuration with the best calibration score among the first 64 evaluations (the initial design) and among all evaluations, both scored on full data. On average the longer search does not improve on its initial design (+0.47 against +0.72 over uniform): it changes the pick in three cells, for the better in one and for the worse in two. These are the picks calibration alone would make; NAS-refined differs because it compares several candidates of the search on full data (in Code B512 it gains +1.28). On LongBench a higher calibration score found later in the search often does not carry over to the full data (Appendix~\ref{app:calib}), which is why MOSAIC selects its final configuration on full data and keeps the Winner as a candidate.
""")
parts.append(float_("table", tabular("l r r r", ["Cell", "Evals", r"$\Delta$, first 64", r"$\Delta$, all"], _rows, size=r"\footnotesize", sep="4pt"),
                    r"\textbf{Calibration-best configuration after the initial design vs.\ after the full Stage 4 search} (SnapKV, LongBench, full data). $\Delta$: gain over uniform; losses in bold.", "tab:app-search-curve", pos="!htbp"))

# H: AdaKV allocation shapes (figures/figure_adakv_layers.pdf from make_adakv_layers.py, same style as Figure 3)
parts.append(r"""
\section{AdaKV Per-Layer Allocations}
\label{app:adakv-shapes}

Figure~\ref{fig:app-adakv-shapes} is the AdaKV counterpart of Figure~\ref{fig:heatmap}, drawn in the same way. AdaKV shows a weaker version of the middle-layer preference: layer 10 receives more than its uniform share in 95\% of the 19 AdaKV allocations and layers 13--16 in 68--89\%, but over the whole middle block (layers 10 and 14--20) the share is 55\%, against 65\% for SnapKV and H2O.

\begin{figure*}[t]
  \centering
  \includegraphics{figures/figure_adakv_layers.pdf}
  \caption{\textbf{AdaKV per-layer allocations}, drawn as Figure~\ref{fig:heatmap}. \textit{(a)} Stage 2 winners at their natural average budget (left). \textit{(b)} MOSAIC's final configuration for every cell (the better of Winner and NAS-refined), with the target budget on the left ($^\dagger$: searched with the earlier floor of 16) and a marker on the right for which of the two it is. \textit{(c)} For each layer, the share of the 19 allocations in (a) and (b) that give it more than its uniform share; navy bars exceed 50\%. Colour: each layer's budget divided by the row mean, on a log$_2$ scale (blue: more than the uniform share; red: less).}
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
    Search space of one search & 8-dimensional (one group, the other 24 layers fixed), at one budget: at most $4033^8 \approx 10^{29}$ allocations per search & 32-dimensional; Stage 1: $5^{32}$ or $7^{32}$ ($\approx 10^{22}$--$10^{27}$) grid configurations across all budgets; Stage 4: $\approx 10^{69}$ allocations at B128 (${\sim}10^{40}\times$ one EvolKV search) to $10^{111}$ at B2048 \\
    Initial search & task score at a target average budget fixed beforehand (128) & average budget and task score as separate objectives; no target budget imposed \\
    Search output & one allocation, selected by the search fitness & a Pareto set of budget--score trade-offs, from which one anchor (the winner) is selected \\
    Reaching other budgets & rescale the allocation (expanded), or run a separate search at each budget (direct) & rescale the anchor (Stage 3), optionally refine at each budget (Stage 4) \\
    Search at a target budget starts from & the uniform allocation at that budget & the rescaled anchor, six heuristic shapes and 57 LHS points \\
    Optimizer & CMA-ES, one group at a time & classifier-guided Bayesian optimization (MLP + differential evolution) \\
    Eviction methods tested & SnapKV & SnapKV, H2O, AdaKV, L2Norm \\
    Benchmarks tested & LongBench Code, Single-Doc QA & LongBench (4 categories), RULER \\
    \midrule
    \multicolumn{3}{@{}l}{\textit{Search once: EvolKV expanded from B128 vs.\ MOSAIC Winner}} \\
    Code, B256/512/1024 & 55.99 / 56.82 / 56.42 & \textbf{57.33} / \textbf{58.16} / \textbf{58.52} \\
    Single-Doc, B256/512/1024 & \textbf{35.43} / 36.14 / 36.38 & 34.51 / \textbf{36.33} / \textbf{36.46} \\
    \multicolumn{3}{@{}l}{\textit{Search once vs.\ search at each budget: EvolKV direct vs.\ MOSAIC Winner}} \\
    Code, B128/512/1024 & 54.92 / 57.02 / 57.20 & \textbf{55.86} / \textbf{58.16} / \textbf{58.52} \\
    Single-Doc, B128/512/1024 & 33.50 / 36.28 / 36.40 & \textbf{33.51} / \textbf{36.33} / \textbf{36.46} \\
    One-time cost (A100) & 12.7 (Code), 5.2 (Single-Doc) GPU-h & Code: 8.0 GPU-h for Stage 2, Stage 1 logs lost; Single-Doc: 20.1 GPU-h \\
    \midrule
    \multicolumn{3}{@{}l}{\textit{Search at each budget, MOSAIC Stage 4 at most 150 evaluations: EvolKV direct vs.\ MOSAIC NAS-refined}} \\
    Code, B128/512/1024 & 54.92 / 57.02 / 57.20 & \textbf{$\geq$55.73} / \textbf{58.01} / \textbf{58.91} \\
    Single-Doc, B128/512/1024 & 33.50 / \textbf{36.28} / 36.40 & \textbf{$\geq$33.67} / 35.61 / \textbf{37.01} \\
    Cost, 6 cells (A100) & 53.7 GPU-h & 43.8 GPU-h, plus the one-time Stages 1--2 that seed it \\
    \bottomrule
  \end{tabular}
  \caption{\textbf{EvolKV vs.\ MOSAIC.} Bold marks the better score within each block. Costs are measured on the same hardware and harness (Appendix~\ref{app:cost}). MOSAIC's search-once Winner wins on Code but needs a costlier one-time search; with each Stage 4 search cut to its first 150 evaluations, NAS-refined costs less than EvolKV in every cell and wins 5 of 6 (Table~\ref{tab:app-cost}; $\geq$: lower bound), a comparison that excludes MOSAIC's one-time Stages 1--2.}
  \label{tab:app-evolkv-glance}
\end{table*}
""")

# I: reproducibility details (all values read from the run code: NAS_Assets/run_longbench_lamp.py, run_ruler_lamp.py,
#    LAMP.py, eval_fixed_budgets_from_anchor.py, eval_evolkv_expansion.py)
parts.append(r"""
\section{Reproducibility Details}
\label{app:repro}

\paragraph{Budget decoding.} Stage 1 maps each coordinate $x_i \in [0,1]$ of a configuration to a discrete per-layer budget by equal-width bins over a grid $G$, $b_i = G[\min(\lfloor x_i |G| \rfloor, |G|-1)]$: seven levels from 64 to 4096 on RULER, for L2Norm and for H2O on Code, and five from 64 to 1024 for the other LongBench runs (SnapKV, AdaKV, H2O); for SnapKV Code, whose Stage 1 log was lost, the 1024 cap is inferred from its winner. The grid limits only Stage 1: Stages 3 and 4 decode continuously within $[64, 4096]$ for every run, so a winner found under the 1024 cap can receive larger per-layer budgets after rescaling. The total cache, and hence memory, is fixed by the average budget $B$, so this only redistributes budget across layers; LongBench inputs (up to 7{,}500 tokens after truncation) are longer than the 4096 cap, so a layer's extra budget is spent on retaining more tokens. Stages 3 and 4 use a continuous decoder that fixes the mean at the target $B$. With total $T = 32B$ and weights $w_i = \max(x_i, 10^{-6})$, it sets $b_i = R\,w_i / \sum_{j \in F} w_j$ for the free layers $F$, where $R$ is $T$ minus the budget of the clamped layers. Layers above the cap of 4096 are clamped first; only when none exceeds it are layers below the floor clamped; clamped layers stay clamped, and the step repeats until no bound is violated (at most 32 passes). The surplus or deficit is therefore redistributed in proportion to $w_i$ over the free layers. Budgets are then rounded down, and the remaining tokens go one each to the free layers with the largest fractional parts; ties go to the lower layer index (stable sort), so $\sum_i b_i = T$ exactly whenever $32 \cdot 64 \le T \le 32 \cdot 4096$. \emph{Search-space size.} The Stage 1 grid holds $|G|^{32}$ configurations. At a fixed budget $B$, the number of integer allocations $b \in [64, 4096]^{32}$ with $\sum_i b_i = 32B$ follows by inclusion--exclusion over the cap, $\sum_k (-1)^k {32 \choose k}{S - 4033k + 31 \choose 31}$ with $S = 32(B - 64)$: about $10^{69}$, $10^{84}$, $10^{95}$, $10^{105}$ and $10^{111}$ at B128, B256, B512, B1024 and B2048; at B64 the floor leaves only the uniform allocation. For EvolKV we count the allocations one search can propose: it varies one 8-layer group with the other groups fixed, so even ignoring its CacheScore budget penalty (counting every integer vector in $[64, 4096]^8$) a search covers at most $4033^8 \approx 7\times10^{28}$ allocations, against about $6\times10^{68}$ for one joint MOSAIC search at B128, a factor of about $10^{40}$. This compares single searches, not the methods' allocation spaces: the allocations of both lie in the same space $[64, 4096]^{32}$.

\paragraph{Rescaling the Stage 2 winner.} A winner with per-layer budgets $w_i$ is mapped to $x_i = 0.05 + 0.9\,w_i / \max_j w_j$ and decoded at each target $B$ as above. This keeps the order of the layers and the shape of the allocation, but it is an affine map rather than an exact proportional one: ratios between layers are compressed (a layer at the winner's minimum receives at least $0.05/0.95$ of the largest layer's budget). The same mapping seeds the winner into the Stage 4 search.

\paragraph{Per-layer floor and cap.} The cap is 4096 in every run. The floor is 64 except in runs launched under an earlier default of 16: RULER B1024--B2048 for SnapKV, H2O and AdaKV (at B1536--B2048 no SnapKV or H2O final configuration reaches it), the rescaled SnapKV RULER winners at B64 and B512, and AdaKV RULER B64. Every Llama LongBench cell and every L2Norm cell uses floor 64; the Mistral SnapKV, H2O and AdaKV RULER runs use floor 16 throughout. Table~\ref{tab:app-floor} reports how often the floor binds.

\paragraph{Initial designs.} Stage 1 starts from the uniform allocation at every grid level (5 or 7 points, $x_i$ at the bin centres) followed by Latin Hypercube points (59 or 57) drawn with seed 43. Stage 4 rows 0--63 are, in order: uniform ($x_i = 0.5$); five heuristic shapes, namely an ascending ramp ($x$ linear from 0.05 to 0.95 over layers 0--31), its reverse, a middle-heavy triangle (0.05 to 0.95 over layers 0--15, back to 0.05 over 16--31), its complement $1-x$ (edge-heavy), and an alternating pattern $(0.15, 0.85, \dots)$; the rescaled Stage 2 winner, $x_i = 0.05 + 0.9\,w_i/\max_j w_j$; and 57 Latin Hypercube points (seed 43). Calibration subsets use a separate seed (42, below).

\paragraph{Surrogate.} The rank-1 classifier is a scikit-learn \texttt{MLPClassifier} with hidden layers (32, 32) and library defaults otherwise (ReLU, Adam, 200 iterations); proposals maximize its rank-1 probability with SciPy's \texttt{differential\_evolution} at library defaults (\texttt{best1bin}, population 15, up to 1000 generations, polishing on). Neither is seeded, so reruns are not bit-identical.

\paragraph{Stopping rules.} The evaluation cap is 1000 (64 initial + 936 guided). H2O LongBench Stage 4 and SnapKV Summarization Stage 4 use a cap of 200. Other SnapKV LongBench Stage 4 runs were stopped by a saturation watchdog: a run ends when the best calibration score has not improved over the last 40 rows, after at least 60 rows beyond the initial design. Two kept runs, Code B128 and Multi-Doc QA B256, were stopped by an earlier watchdog with a patience of 15 rows after 20, and Single-Doc and Multi-Doc QA B128 reached the 1000 cap. SnapKV and H2O RULER Stage 4 runs stop after 40 evaluations without a new best (counted from the later of the best row and row 64) or at 160 rows. AdaKV searches were stopped by hand once the archive had settled or after a crash; the Mistral AdaKV RULER searches at B1024--B2048 were stopped after only 3--26 evaluations, so their results are close to the initial design. Stage 1 runs were stopped by hand; H2O RULER Stage 1 used at least 198 evaluations, 40 without a new best shaped configuration, and a cap of 350. L2Norm's stopping rule is not recorded in the files available to us.

\paragraph{Candidate provenance.} Stage 2 re-evaluates every distinct rank-1 configuration of the Stage 1 archive on full data, and the winner is the non-uniform configuration with the highest full-data score. The RULER winners were taken by calibration score instead: for SnapKV this is also the full-data best, and for H2O only the four top calibration-ranked configurations were re-evaluated, whose full-data ranking equals the calibration ranking. Stage 4 re-evaluates, besides uniform and the Winner, the calibration-best row of each group: heuristic shapes (rows 1--5), Latin Hypercube points (rows 7--63) and guided proposals (rows 64 and later); NAS-refined is the best of these three on full data. Earlier RULER cells used fewer candidates: SnapKV and H2O B1024 and H2O B1536--B2048 re-evaluated uniform, the best of rows 1--6, the best LHS point and the best row overall; SnapKV B1536--B2048 re-evaluated uniform, the Winner and the best LHS point only. If a run was restarted, the restart's initial design was appended after row 63 and counts as guided rows.

\paragraph{Unavailable records.} The Code Stage 1 archives and logs (SnapKV and H2O) were lost; only their Stage 2 re-evaluations survive. AdaKV RULER Stage 1 timings, the SnapKV Multi-Doc QA Stage 1 timing, and L2Norm search timings are not available.

\paragraph{EvolKV expansion.} Following EvolKV's budget completion rule \citep{yu2025evolkv}, an allocation $k_i$ found at budget 128 is expanded to target $B$ by $b_i = k_i\,T / \sum_j k_j$, rounded with the largest-remainder method so that the mean is exactly $B$, and clipped to $[64, 4096]$ (neither bound binds for B256--B1024).

\paragraph{Evaluation settings.} Llama-3-8B-Instruct in float16, greedy decoding (one beam). LongBench uses the official prompts and chat template, middle truncation of inputs longer than 7{,}500 tokens (the first and last 3{,}750 tokens are kept), the official per-dataset output lengths (32--512 tokens) and the official metrics (F1 for QA, ROUGE-L for summarization, edit similarity for code). RULER uses its 11 subtasks at 4K context with string-match accuracy. SnapKV and H2O keep a fixed recent window of 8 tokens; SnapKV pools observation-window scores with a max-pool of kernel size 7. Calibration subsets are drawn per dataset with Python's \texttt{random.Random(42).sample} at the stated ratio, and the same seed is used throughout. All four methods use FlashAttention-2 for attention.

\paragraph{Hardware.} Searches and evaluations ran on four servers: SnapKV, H2O and AdaKV on NVIDIA A100 GPUs (the EvolKV comparison on the same A100-40GB machine and harness as MOSAIC), AdaKV additionally on RTX A6000 GPUs, and L2Norm on H100 GPUs. The Mistral-7B-Instruct-v0.2 L2Norm searches ran on H100 GPUs with a 30\% calibration subset in every stage, and the Mistral SnapKV, H2O and AdaKV RULER searches on A100 GPUs with a 10\% subset.
""")


parts.append(r"""
\FloatBarrier
\section{Subtask and Dataset Breakdown}
\label{app:breakdown}

This section breaks the per-cell results of Appendix~\ref{app:cells} into RULER subtasks and LongBench datasets, comparing uniform allocation with MOSAIC's final configuration (the better of Winner and NAS-refined) in every cell; bold marks the better of the two in each column.
""")
parts.extend(_moved + _lb_parts)
OUT.write_text("\n".join(parts))
print(f"wrote {OUT}")
