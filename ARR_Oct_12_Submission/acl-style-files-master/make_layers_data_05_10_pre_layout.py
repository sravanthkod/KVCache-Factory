#!/usr/bin/env python3
"""Build figures/figure_layers.tex (SnapKV/H2O per-layer allocations, pure TikZ) from figures/data/A4_layer_importance.csv.
Then: cd figures && pdflatex figure_layers.tex"""
import csv
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE / "figures" / "data"
OUT = HERE / "figures" / "figure_layers.tex"
CAT = {"Code": "Code", "MultiDoc": "Multi-Doc", "SingleDoc": "Single-Doc", "Summ": "Summ.", "RULER": "RULER"}
CAT_ORDER = ["Code", "MultiDoc", "SingleDoc", "Summ", "RULER"]
TYPE = {"bo": "NAS-refined", "winner": "Winner", "heuristic": "NAS-refined", "random": "NAS-refined", "uniform": "uniform"}  # three-way view: BO = best Stage 4 search config
METH = {"snapkv": ("SnapKV", "csnapkv"), "h2o": ("H2O", "chto")}
LIM = 3.0
LESS, MID, MORE = np.array([184, 58, 50]), np.array([242, 241, 237]), np.array([31, 78, 121])

PX, RH = 0.32, 0.19            # cell pitch (cm) horizontally / row height
GAP_GROUP, GAP_PANEL = 0.12, 0.62
BAR_H = 1.15                   # height of 100% in panel (a)


def parse(label):
    parts = [p.strip() for p in label.split("·")]
    meth, rest = parts[0], parts[1:]
    if len(rest) == 2:
        cat, tail = rest
        b, typ = tail.split(" (")
        return meth, cat, int(b[1:]), typ.rstrip(")")
    cat, avg = rest[0].split(" (avg ")
    return meth, cat, int(avg.rstrip(")")), None


def colour(v):
    v = max(-LIM, min(LIM, v)) / LIM
    c = MID + (MORE - MID) * v if v >= 0 else MID + (LESS - MID) * (-v)
    return "{rgb,255:red,%d;green,%d;blue,%d}" % tuple(np.round(c))


rows = list(csv.DictReader(open(DATA / "A4_layer_importance.csv")))
# Panel (b) shows MOSAIC's final configuration: the best NON-uniform candidate on full data (Winner, best heuristic,
# best LHS point or best guided proposal). The A4 file marks uniform as best in the cells where MOSAIC loses to it, so
# those rows are replaced by MOSAIC's best candidate from cells.csv.
CELLCAT = {"Code": "CODE", "MultiDoc": "MULTI_DOCUMENT_QA", "SingleDoc": "SINGLE_DOCUMENT_QA", "Summ": "SUMMARIZATION", "RULER": "RULER_ALL"}
cand = {}
for c in csv.DictReader(open(HERE.parents[1] / "ICLR_Final_Results" / "analysis_outputs" / "cells.csv")):
    if c["source"] != "step3" and c["label"] in ("winner", "heuristic", "random", "bo") and c["era"] == "64":
        k = (c["method"], c["category"], int(c["budget"]))
        if k not in cand or float(c["full_score"]) > cand[k][0]:
            cand[k] = (float(c["full_score"]), c["label"], [int(float(x)) for x in c["budgets"].split()])
for r in rows:
    if r["panel"] == "best_config" and r["row"].endswith("(uniform)"):
        meth, cat, b, _ = parse(r["row"])
        score, lab, bud = cand[(meth, CELLCAT[cat], b)]
        r["row"] = r["row"].replace("(uniform)", f"({lab})")
        for i in range(32):
            r[f"L{i}"] = bud[i]
        print(f"  replaced uniform row: {meth} {cat} B{b} -> {lab} ({score:.2f})")
blocks = {"best_config": [], "anchor": []}
for r in rows:
    meth, cat, b, typ = parse(r["row"])
    blocks[r["panel"]].append((["snapkv", "h2o"].index(meth), CAT_ORDER.index(cat), b, meth, cat, typ,
                               np.array([float(r[f"L{i}"]) for i in range(32)])))
for k in blocks:
    blocks[k].sort(key=lambda x: x[:3])
allrows = np.array([it[-1] for k in blocks for it in blocks[k]])
share = (allrows > allrows.mean(1, keepdims=True)).mean(0) * 100
MID6 = [10, 14, 15, 16, 18, 20]
def _stats(sel):
    a = np.array([it[-1] for k in blocks for it in blocks[k] if sel(k, it)])
    sh = (a > a.mean(1, keepdims=True)).mean(0) * 100
    return len(a), sh[MID6].min(), sh[MID6].max(), sh[:10].min(), sh[:10].max(), np.median(sh[:10]), sh[21:30].min(), sh[21:30].max(), np.median(sh[21:30])
for name, sel in [("all", lambda k, it: True), ("no rescaled winners", lambda k, it: it[5] != "winner")]:
    print("  %-20s n=%d middle-six %.0f-%.0f%%  early %.0f-%.0f%% (median %.0f)  late %.0f-%.0f%% (median %.0f)" % ((name,) + _stats(sel)))
W = 32 * PX

L = []  # tikz lines
A = L.append
# ---------- (a) bars ----------
y0 = 0.0
A(rf"\node[ptitle] at (0,{y0 + BAR_H + 0.18:.3f}) {{(a)\enspace Share of allocations that give each layer more than its uniform share}};")
for g in (0, 50, 100):
    yy = y0 + BAR_H * g / 100
    A(rf"\draw[black!{12 if g != 50 else 55}, line width={0.3 if g != 50 else 0.5}pt{', densely dashed' if g == 50 else ''}] (0,{yy:.3f}) -- ({W:.3f},{yy:.3f});")
    A(rf"\node[lab, anchor=east] at (-0.06,{yy:.3f}) {{{g}{'\\%' if g == 100 else ''}}};")
for i, s in enumerate(share):
    col = "navy" if s > 50 else "black!22"
    A(rf"\fill[{col}] ({i * PX + 0.05:.3f},{y0:.3f}) rectangle ({(i + 1) * PX - 0.05:.3f},{y0 + BAR_H * s / 100:.3f});")

# ---------- heatmap panels ----------
y = y0 - GAP_PANEL - 0.3


def heat_panel(items, title, tags):
    global y
    A(rf"\node[ptitle] at (0,{y + 0.18:.3f}) {{{title}}};")
    top = y
    prev = None
    spans = {}
    for it in items:
        if prev is not None and it[3] != prev:
            y -= GAP_GROUP
        prev = it[3]
        v = np.log2(it[-1] / it[-1].mean())
        for x in range(32):
            A(rf"\fill[fill={colour(v[x])}] ({x * PX + 0.012:.3f},{y - RH + 0.012:.3f}) rectangle ({(x + 1) * PX - 0.012:.3f},{y - 0.012:.3f});")
        lab = f"{CAT[it[4]]} \\textperiodcentered{{}} B{it[2]}" if tags else f"{CAT[it[4]]} \\textperiodcentered{{}} avg {it[2]}"
        A(rf"\node[lab, anchor=east] at (-0.08,{y - RH / 2:.3f}) {{{lab}}};")
        if tags:
            A(rf"\node[lab, text=black!55, anchor=west] at ({W + 0.08:.3f},{y - RH / 2:.3f}) {{{TYPE[it[5]]}}};")
        lo, hi = spans.get(it[3], (y, y))
        spans[it[3]] = (max(lo, y), min(hi, y - RH))
        y -= RH
    for m, (a, b) in spans.items():
        name, col = METH[m]
        A(rf"\draw[{col}, line width=1.1pt] (-2.2,{a - 0.03:.3f}) -- (-2.2,{b + 0.03:.3f});")
        A(rf"\node[mlab, text={col}, rotate=90, anchor=south] at (-2.24,{(a + b) / 2:.3f}) {{{name}}};")
    return top, y


tb, bb = heat_panel(blocks["best_config"], r"(b)\enspace MOSAIC's final configuration per cell (floor 64)", True)
y -= GAP_PANEL
ta, ba = heat_panel(blocks["anchor"], r"(c)\enspace Stage 2 winner anchors (unconstrained search, natural average budget)", False)
for x in (0, 4, 8, 12, 16, 20, 24, 28, 31):
    A(rf"\node[lab] at ({(x + 0.5) * PX:.3f},{ba - 0.14:.3f}) {{{x}}};")
    A(rf"\node[lab] at ({(x + 0.5) * PX:.3f},{y0 - 0.14:.3f}) {{{x}}};")
A(rf"\node[axlab] at ({W / 2:.3f},{ba - 0.42:.3f}) {{layer index}};")

# ---------- colour bar (spans panels b and c) ----------
cbl = ba  # bottom of panel (c)
cx, n = W + 1.35, 60
for k in range(n):
    v = -LIM + 2 * LIM * (k + 0.5) / n
    ya = cbl + (tb - cbl) * k / n
    A(rf"\fill[fill={colour(v)}] ({cx:.3f},{ya:.3f}) rectangle ({cx + 0.17:.3f},{ya + (tb - cbl) / n + 0.002:.3f});")
for v, t in zip(range(-3, 4), [r"$1/8\times$", r"$1/4\times$", r"$1/2\times$", "uniform", r"$2\times$", r"$4\times$", r"$8\times$"]):
    yy = cbl + (tb - cbl) * (v + LIM) / (2 * LIM)
    A(rf"\draw[black!45, line width=0.3pt] ({cx + 0.17:.3f},{yy:.3f}) -- ({cx + 0.24:.3f},{yy:.3f});")
    A(rf"\node[lab, anchor=west] at ({cx + 0.25:.3f},{yy:.3f}) {{{t}}};")
A(rf"\node[axlab, rotate=90, anchor=north] at ({cx + 1.12:.3f},{(tb + cbl) / 2:.3f}) {{layer budget / row mean}};")

OUT.write_text(r"""% GENERATED by ../make_layers_data.py from data/A4_layer_importance.csv -- edit the script, not this file.
\documentclass[border=2pt]{standalone}
\usepackage[scaled=0.92]{helvet}
\renewcommand\familydefault{\sfdefault}
\usepackage[T1]{fontenc}
\usepackage{sansmath}
\sansmath
\usepackage{tikz}
\definecolor{csnapkv}{HTML}{1F4E79}
\definecolor{chto}{HTML}{5E8FB4}
\definecolor{navy}{HTML}{1F4E79}
\definecolor{ink}{HTML}{2B2B2B}
\tikzset{lab/.style={font=\fontsize{5.6}{6}\selectfont, text=ink!85, inner sep=0.5pt},
         mlab/.style={font=\fontsize{6.2}{7}\selectfont\bfseries, inner sep=0.5pt},
         axlab/.style={font=\scriptsize, text=black!65},
         ptitle/.style={font=\scriptsize\bfseries, text=ink, anchor=south west, inner sep=0pt}}
\begin{document}
\begin{tikzpicture}
""" + "\n".join(L) + "\n\\end{tikzpicture}\n\\end{document}\n")
print(f"wrote {OUT}; layers above 50%: {[i for i, s in enumerate(share) if s > 50]}")
print("shares:", " ".join(f"L{i}={s:.0f}" for i, s in enumerate(share)))
