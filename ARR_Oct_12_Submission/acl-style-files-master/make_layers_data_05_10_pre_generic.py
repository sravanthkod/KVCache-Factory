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
cand, cfloor = {}, {}
for c in csv.DictReader(open(HERE.parents[1] / "ICLR_Final_Results" / "analysis_outputs" / "cells.csv")):
    if c["source"] != "step3" and c["label"] in ("winner", "heuristic", "random", "bo"):
        k = (c["method"], c["category"], int(c["budget"]))
        cfloor[k] = int(c["era"])
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
# floor-16 cells (SnapKV/H2O RULER B1024-B2048) are not in the A4 file: add MOSAIC's final configuration for them,
# marked with a dagger in panel (b)
FLOOR16 = set()
have = {parse(r["row"])[:3] for r in rows if r["panel"] == "best_config"}
for (m, c, b), (score, lab, bud) in sorted(cand.items()):
    if cfloor[(m, c, b)] == 16 and c == "RULER_ALL" and (m, "RULER", b) not in have:
        r = {"panel": "best_config", "row": f"{m} · RULER · B{b} ({lab})"}
        r.update({f"L{i}": bud[i] for i in range(32)})
        rows.append(r)
        FLOOR16.add((m, "RULER", b))
        print(f"  added floor-16 row: {m} RULER B{b} -> {lab} ({score:.2f})")
blocks = {"best_config": [], "anchor": []}
for r in rows:
    meth, cat, b, typ = parse(r["row"])
    blocks[r["panel"]].append((["snapkv", "h2o"].index(meth), CAT_ORDER.index(cat), b, meth, cat, typ,
                               np.array([float(r[f"L{i}"]) for i in range(32)])))
for k in blocks:
    blocks[k].sort(key=lambda x: x[:3])
allrows = np.array([it[-1] for k in blocks for it in blocks[k]])
share = (allrows > allrows.mean(1, keepdims=True)).mean(0) * 100
MID6 = [10, 14, 15, 16, 20]  # the middle layers that stand out once the floor-16 RULER cells are included
def _stats(sel):
    a = np.array([it[-1] for k in blocks for it in blocks[k] if sel(k, it)])
    sh = (a > a.mean(1, keepdims=True)).mean(0) * 100
    return len(a), sh[MID6].min(), sh[MID6].max(), sh[:10].min(), sh[:10].max(), np.median(sh[:10]), sh[21:30].min(), sh[21:30].max(), np.median(sh[21:30])
for name, sel in [("all", lambda k, it: True), ("no rescaled winners", lambda k, it: it[5] != "winner")]:
    print("  %-20s n=%d middle-six %.0f-%.0f%%  early %.0f-%.0f%% (median %.0f)  late %.0f-%.0f%% (median %.0f)" % ((name,) + _stats(sel)))
W = 32 * PX

L = []  # tikz lines
A = L.append
GAP_TASK = 0.05                # small gap between task groups inside a method block
X_TASK, X_BUD, X_BRK = -0.62, -0.08, -1.84
X_BRACE, X_GTASK = -0.7, -0.81   # panel (b): brace just left of the budgets, task name left of the brace


def heat_panel(items, title, final):
    """final=True: panel (b), rows grouped by task with the budget per row and a Winner / NAS-refined marker."""
    global y
    A(rf"\node[ptitle] at ({W / 2:.3f},{y + 0.18:.3f}) {{{title}}};")
    top = y
    prev_m = prev_t = None
    spans = {}
    groups = {}  # (method, task) -> (top y, bottom y), panel (b)
    for it in items:
        m, task = it[3], it[4]
        if prev_m is not None and m != prev_m:
            y -= GAP_GROUP
        elif final and prev_t is not None and task != prev_t:
            y -= GAP_TASK
        new_task = (m, task) != (prev_m, prev_t)
        prev_m, prev_t = m, task
        v = np.log2(it[-1] / it[-1].mean())
        for x in range(32):
            A(rf"\fill[fill={colour(v[x])}] ({x * PX + 0.012:.3f},{y - RH + 0.012:.3f}) rectangle ({(x + 1) * PX - 0.012:.3f},{y - 0.012:.3f});")
        yc = y - RH / 2
        if not final:
            A(rf"\node[lab, anchor=east] at ({X_TASK:.3f},{yc:.3f}) {{{CAT[task]}}};")
        else:
            gt, gb = groups.get((m, task), (y, y))
            groups[(m, task)] = (max(gt, y), min(gb, y - RH))
        dag = r"$^\dagger$" if final and (m, task, it[2]) in FLOOR16 else ""
        A(rf"\node[lab, text=black!60, anchor=east] at ({X_BUD:.3f},{yc:.3f}) {{{it[2]}{dag}}};")
        if final:
            mx, h = W + 0.1, 0.105
            style = "fill=ink!75" if it[5] == "winner" else "draw=ink!75, line width=0.45pt, fill=white"
            A(rf"\path[{style}] ({mx:.3f},{yc - h / 2:.3f}) rectangle ({mx + h:.3f},{yc + h / 2:.3f});")
        lo, hi = spans.get(m, (y, y))
        spans[m] = (max(lo, y), min(hi, y - RH))
        y -= RH
    for (m, task), (gt, gb) in groups.items():
        A(rf"\draw[decorate, decoration={{brace, amplitude=1.5pt}}, black!45, line width=0.35pt] "
          rf"({X_BRACE:.3f},{gb + 0.02:.3f}) -- ({X_BRACE:.3f},{gt - 0.02:.3f});")
        A(rf"\node[lab, anchor=east] at ({X_GTASK:.3f},{(gt + gb) / 2:.3f}) {{{CAT[task]}}};")
    for m, (a, b) in spans.items():
        name, col = METH[m]
        A(rf"\draw[{col}, line width=1.1pt] ({X_BRK:.3f},{a - 0.03:.3f}) -- ({X_BRK:.3f},{b + 0.03:.3f});")
        A(rf"\node[mlab, text={col}, rotate=90, anchor=south] at ({X_BRK - 0.04:.3f},{(a + b) / 2:.3f}) {{{name}}};")
    return top, y


def layer_ticks(yy):
    for x in (0, 4, 8, 12, 16, 20, 24, 28, 31):
        A(rf"\node[lab] at ({(x + 0.5) * PX:.3f},{yy:.3f}) {{{x}}};")


# ---------- (a) Stage 2 winners ----------
y = 0.0
ta, ba = heat_panel(blocks["anchor"], r"(a)\enspace Stage 2 winners (natural average budget)", False)
# ---------- (b) MOSAIC's final configuration per cell ----------
y -= GAP_PANEL
tb, bb = heat_panel(blocks["best_config"], r"(b)\enspace MOSAIC's final configuration per cell (target budget; $\dagger$: floor 16)", True)
A(rf"\node[lab, anchor=north east] at ({W + 0.2:.3f},{bb - 0.27:.3f}) {{"
  rf"\tikz[baseline=-0.4ex]\fill[ink!75] (0,0) rectangle (0.1,0.1);~Winner (Stage 3)\quad "
  rf"\tikz[baseline=-0.4ex]\draw[ink!75, line width=0.45pt] (0,0) rectangle (0.1,0.1);~NAS-refined (Stage 4)}};")
layer_ticks(bb - 0.14)
# ---------- (c) share bars ----------
y = bb - GAP_PANEL - 0.62 - BAR_H
y0 = y
A(rf"\node[ptitle] at ({W / 2:.3f},{y0 + BAR_H + 0.18:.3f}) {{(c)\enspace Share of the allocations in (a) and (b) that give each layer more than its uniform share}};")
for g in (0, 50, 100):
    yy = y0 + BAR_H * g / 100
    A(rf"\draw[black!{12 if g != 50 else 55}, line width={0.3 if g != 50 else 0.5}pt{', densely dashed' if g == 50 else ''}] (0,{yy:.3f}) -- ({W:.3f},{yy:.3f});")
    A(rf"\node[lab, anchor=east] at (-0.06,{yy:.3f}) {{{g}{'\\%' if g == 100 else ''}}};")
for i, s_ in enumerate(share):
    col = "navy" if s_ > 50 else "black!22"
    A(rf"\fill[{col}] ({i * PX + 0.05:.3f},{y0:.3f}) rectangle ({(i + 1) * PX - 0.05:.3f},{y0 + BAR_H * s_ / 100:.3f});")
layer_ticks(y0 - 0.14)
A(rf"\node[axlab] at ({W / 2:.3f},{y0 - 0.42:.3f}) {{layer index}};")

# ---------- colour bar (spans panels a and b) ----------
cbl, cbt = bb, ta
cx, n = W + 0.55, 60
for k in range(n):
    v = -LIM + 2 * LIM * (k + 0.5) / n
    ya = cbl + (cbt - cbl) * k / n
    A(rf"\fill[fill={colour(v)}] ({cx:.3f},{ya:.3f}) rectangle ({cx + 0.17:.3f},{ya + (cbt - cbl) / n + 0.002:.3f});")
for v, t in zip(range(-3, 4), [r"$1/8\times$", r"$1/4\times$", r"$1/2\times$", "uniform", r"$2\times$", r"$4\times$", r"$8\times$"]):
    yy = cbl + (cbt - cbl) * (v + LIM) / (2 * LIM)
    A(rf"\draw[black!45, line width=0.3pt] ({cx + 0.17:.3f},{yy:.3f}) -- ({cx + 0.24:.3f},{yy:.3f});")
    A(rf"\node[lab, anchor=west] at ({cx + 0.25:.3f},{yy:.3f}) {{{t}}};")
A(rf"\node[axlab, rotate=90, anchor=north] at ({cx + 1.12:.3f},{(cbt + cbl) / 2:.3f}) {{layer budget / row mean}};")

OUT.write_text(r"""% GENERATED by ../make_layers_data.py from data/A4_layer_importance.csv -- edit the script, not this file.
\documentclass[border=2pt]{standalone}
\usepackage[scaled=0.92]{helvet}
\renewcommand\familydefault{\sfdefault}
\usepackage[T1]{fontenc}
\usepackage{sansmath}
\sansmath
\usepackage{tikz}
\usetikzlibrary{decorations.pathreplacing}
\definecolor{csnapkv}{HTML}{1F4E79}
\definecolor{chto}{HTML}{5E8FB4}
\definecolor{navy}{HTML}{1F4E79}
\definecolor{ink}{HTML}{2B2B2B}
\tikzset{lab/.style={font=\fontsize{5.6}{6}\selectfont, text=ink!85, inner sep=0.5pt},
         mlab/.style={font=\fontsize{6.2}{7}\selectfont\bfseries, inner sep=0.5pt},
         axlab/.style={font=\scriptsize, text=black!65},
         ptitle/.style={font=\scriptsize\bfseries, text=ink, anchor=south, inner sep=0pt}}
\begin{document}
\begin{tikzpicture}
""" + "\n".join(L) + "\n\\end{tikzpicture}\n\\end{document}\n")
print(f"wrote {OUT}; layers above 50%: {[i for i, s in enumerate(share) if s > 50]}")
print("shares:", " ".join(f"L{i}={s:.0f}" for i, s in enumerate(share)))
