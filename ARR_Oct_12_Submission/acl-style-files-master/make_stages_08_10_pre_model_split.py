#!/usr/bin/env python3
"""Stage 3 vs Stage 4 against uniform, per (task, eviction method).
Writes tables/table_stages.tex (main-text Table 2: Stage 3 = rescaled winner, Stage 4 = NAS-refined) and the data files of
figures/figure_stages.tex (uniform / Stage 3 / Stage 4 score at every target budget). Inputs: figures/data/stage3_rows.csv
(written by make_appendix.py) and three_way.load(). Run make_appendix.py first."""
import csv
from pathlib import Path

import mistral
import three_way as tw

HERE = Path(__file__).resolve().parent
DATA = HERE / "figures" / "data"
DISP = {"CODE": "Code", "MULTI_DOCUMENT_QA": "MultiDoc", "SINGLE_DOCUMENT_QA": "SingleDoc", "SUMMARIZATION": "Summ", "RULER_ALL": "RULER"}
CODE = {v: k for k, v in DISP.items()}
ORDER = [  # same grouping as the paper's transfer table
    [(c, m) for c in ["Code", "MultiDoc", "SingleDoc", "Summ", "RULER"] for m in ["H2O", "SnapKV"]],
    [(c, "AdaKV") for c in ["Code", "MultiDoc", "SingleDoc", "Summ", "RULER"]],
    [(c, "L2Norm") for c in ["Code", "MultiDoc", "SingleDoc", "Summ", "RULER"]],
    [(c, mistral.NAME) for c in ["Code", "MultiDoc", "SingleDoc", "Summ", "RULER"]]
    + [(c, mistral.NAMES[m]) for m in ["SnapKV", "H2O", "AdaKV"] for c in ["Code", "MultiDoc", "SingleDoc", "RULER"]],  # second model, own total
]
NGROUPS_LLAMA = 3


def load():
    s3, nat = {}, {}
    for r in csv.DictReader(open(DATA / "stage3_rows.csv")):
        k = (r["category"], r["method"])
        s3.setdefault(k, {})[int(r["budget"])] = (float(r["uniform"]), float(r["winner"]))
        nat[k] = r["natural"]
    s4, fin = {}, {}
    for (m, bench, cat, b), v in tw.load().items():
        if "bo" in v:
            s4.setdefault((DISP[cat], m), {})[b] = (v["uniform"], v["bo"])
            # MOSAIC's final configuration: the better of Winner and NAS-refined on full data
            fin.setdefault((DISP[cat], m), {})[b] = (v["uniform"], max(v["bo"], v.get("winner", -1e9)))
    for (m, cat, b), v in mistral.load().items():
        k = (DISP[cat], m)
        if "winner" in v:
            s3.setdefault(k, {})[b] = (v["uniform"], v["winner"])
        s4.setdefault(k, {})[b] = (v["uniform"], v["bo"])
        fin.setdefault(k, {})[b] = (v["uniform"], max(v["bo"], v.get("winner", -1e9)))
    return s3, s4, fin, nat


def stats(cells):
    d = [w - u for u, w in cells.values()]
    return sum(x > 0 for x in d), len(d), (sum(d) / len(d) if d else None)


def sgn(x):
    return f"${x:+.2f}$".replace("$-", "$-") if x is not None else "--"


def table(s3, s4, fin, nat):
    lines = [r"\begin{tabular}{@{} l l r r r r r r @{}}", r"  \toprule",
             r"  & & \multicolumn{2}{c}{\textbf{Stage 3}} & \multicolumn{2}{c}{\textbf{Stage 4}} & \multicolumn{2}{c}{\textbf{MOSAIC}} \\",
             r"  & & \multicolumn{2}{c}{(Winner)} & \multicolumn{2}{c}{(NAS-refined)} & \multicolumn{2}{c}{(best of both)} \\",
             r"  \cmidrule(lr){3-4} \cmidrule(lr){5-6} \cmidrule(lr){7-8}",
             r"  \textbf{Task} & \textbf{Method} & \textbf{Wins} & \textbf{$\Delta$} & \textbf{Wins} & \textbf{$\Delta$} & \textbf{Wins} & \textbf{$\Delta$} \\",
             r"  \midrule"]
    tot = [0, 0, 0, 0, 0, 0]
    totm = [0, 0, 0, 0, 0, 0]
    for gi, group in enumerate(ORDER):
        if gi:
            lines.append(r"  \midrule")
        for i, k in enumerate(group):
            w3, n3, m3 = stats(s3.get(k, {}))
            w4, n4, m4 = stats(s4.get(k, {}))
            wf, nf, mf = stats(fin.get(k, {}))
            acc = tot if gi < NGROUPS_LLAMA else totm
            for j, x in enumerate((w3, n3, w4, n4, wf, nf)):
                acc[j] += x
            if i % 2 == 0:
                lines.append(r"  \rowcolor{gray!10}")
            lines.append(f"  {k[0]:9s} & {(k[1].replace(' (Mistral)', '$^\\ddagger$')):6s} & {w3}/{n3} & {sgn(m3)} & "
                         + (f"{w4}/{n4} & {sgn(m4)} & {wf}/{nf} & {sgn(mf)}" if n4 else "-- & -- & -- & --") + r" \\")
    row = lambda name, t: rf"  \multicolumn{{2}}{{@{{}}l}}{{\textbf{{{name}}}}} & \textbf{{{t[0]}/{t[1]}}} & & \textbf{{{t[2]}/{t[3]}}} & & \textbf{{{t[4]}/{t[5]}}} & \\"
    lines.insert(len(lines) - 5 * 2 - 1, "")  # placeholder, removed below
    lines = [l for l in lines if l != ""]
    # Llama total goes before the Mistral block, Mistral total at the end
    cut = max(i for i, l in enumerate(lines) if l.strip() == r"\midrule")
    lines = lines[:cut] + [r"  \midrule", row("Total (Llama)", tot)] + lines[cut:]
    lines += [r"  \midrule", row(r"Total (Mistral$^\ddagger$)", totm),
              r"  \bottomrule", r"\end{tabular}"]
    return "\n".join(lines) + "\n", tot


def figure_data(s3, s4):
    for c in DISP.values():
        for m in ["SnapKV", "H2O", "AdaKV", "L2Norm"]:
            a, b = s3.get((c, m), {}), s4.get((c, m), {})
            uni = {x: u for x, (u, _) in a.items()} | {x: u for x, (u, _) in b.items()}
            tag = f"stages_{CODE[c]}_{m.lower()}"
            for suf, pts in [("uni", uni), ("s3", {x: w for x, (_, w) in a.items()}), ("s4", {x: w for x, (_, w) in b.items()})]:
                with open(DATA / f"{tag}_{suf}.dat", "w") as f:
                    f.write("budget score\n" + "".join(f"{x} {y:.3f}\n" for x, y in sorted(pts.items())))


if __name__ == "__main__":
    s3, s4, fin, nat = load()
    tex, tot = table(s3, s4, fin, nat)
    (HERE / "tables").mkdir(exist_ok=True)
    (HERE / "tables" / "table_stages.tex").write_text("% GENERATED by make_stages.py -- edit the script, not this file.\n" + tex)
    figure_data(s3, s4)
    print(f"Stage 3 {tot[0]}/{tot[1]}, Stage 4 {tot[2]}/{tot[3]}, MOSAIC {tot[4]}/{tot[5]}")
    for g in ORDER:
        for k in g:
            print(k, stats(s3.get(k, {})), stats(s4.get(k, {})), sorted(s4.get(k, {})))
