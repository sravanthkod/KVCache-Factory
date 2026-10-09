#!/usr/bin/env python3
"""Main LongBench results table (uniform vs MOSAIC per method and budget) -> tables/table_main.tex. RULER has its own table (tables/table_ruler_summary.tex).
MOSAIC = the final configuration, the better of Winner and NAS-refined on full data (three_way.load()). Budgets without a
Stage 4 search show the rescaled Stage 3 winner, from figures/data/stage3_rows.csv (run make_appendix.py first)."""
import csv
from pathlib import Path

import mistral
import three_way as tw

HERE = Path(__file__).resolve().parent
CATS = ["CODE", "MULTI_DOCUMENT_QA", "SINGLE_DOCUMENT_QA", "SUMMARIZATION"]
DISP = {"Code": "CODE", "MultiDoc": "MULTI_DOCUMENT_QA", "SingleDoc": "SINGLE_DOCUMENT_QA", "Summ": "SUMMARIZATION", "RULER": "RULER_ALL"}
LLAMA = ["SnapKV", "H2O", "AdaKV", "L2Norm"]
MODELS = [("Llama-3-8B", LLAMA), ("Mistral-7B", [mistral.NAMES[m] for m in LLAMA])]  # model column, left of the method
BUDGETS = [128, 256, 512, 1024]


def load():
    out = {}  # (method, CAT, B) -> (uniform, mosaic, floor, rescale_only)
    for (m, bench, cat, b), v in tw.load().items():
        out[(m, cat, b)] = (v["uniform"], max(v.get("winner", -1e9), v.get("bo", -1e9)), v["floor"], False)
    for (m, cat, b), v in mistral.load().items():
        out[(m, cat, b)] = (v["uniform"], max(v.get("winner", -1e9), v["bo"]), v["floor"], False)
    # Mistral SnapKV/H2O/AdaKV Summarization: uniform only (no budget search), MOSAIC shown as --
    with open(HERE / "figures" / "data" / "mistral_summarization_uniform.csv") as f:
        for r in csv.DictReader(l for l in f if not l.startswith("#")):
            for m in ["SnapKV", "H2O", "AdaKV"]:
                out.setdefault((mistral.NAMES[m], "SUMMARIZATION", int(r["budget"])), (float(r[m]), None, 0, False))
    for r in csv.DictReader(open(HERE / "figures" / "data" / "stage3_rows.csv")):
        k = (r["method"], DISP[r["category"]], int(r["budget"]))
        if k not in out:
            out[k] = (float(r["uniform"]), float(r["winner"]), int(r["floor"]), True)
    return out


def cell(v):
    if v is None:
        return "-- & --"
    u, m, floor, resc = v
    if m is None:
        return f"{u:.2f} & --"
    mark = ""
    us, ms = f"{u:.2f}", f"{m:.2f}"
    if m > u:
        ms = rf"\textbf{{{ms}}}"
    elif u > m:
        us = rf"\textbf{{{us}}}"
    return f"{us} & {ms}{mark}"


def _model(name, n):
    return rf"\multirow{{{n}}}{{*}}{{\rotatebox[origin=c]{{90}}{{\textbf{{{name}}}}}}}"


def table(out):
    head = " & ".join(rf"\multicolumn{{2}}{{c}}{{\textbf{{{n}}}}}" for n in ["Code", "Multi-Doc QA", "Single-Doc QA", "Summarization"])
    cmid = " ".join(rf"\cmidrule(lr){{{4 + 2 * i}-{5 + 2 * i}}}" for i in range(4))
    lines = [r"\begin{tabular}{@{} c l r rr rr rr rr @{}}", r"  \toprule",
             rf"  & & & {head} \\", f"  {cmid}",
             r"  \textbf{Model} & \textbf{Method} & \textbf{Budget} & " + " & ".join(["Uniform", "MOSAIC"] * 4) + r" \\"]
    for model, methods in MODELS:
        lines.append(r"  \midrule")
        rows = {m: [b for b in BUDGETS if any((m, c, b) in out for c in CATS)] for m in methods}
        total, first = sum(len(r) for r in rows.values()), True
        for mi, m in enumerate(methods):
            if mi:
                lines.append(r"  \cmidrule(l){2-11}")
            for i, b in enumerate(rows[m]):
                lead = _model(model, total) if first else ""
                first = False
                meth = rf"\multirow{{{len(rows[m])}}}{{*}}{{{m.replace(' (Mistral)', '')}}}" if i == 0 else ""
                lines.append(f"  {lead} & {meth} & {b} & " + " & ".join(cell(out.get((m, c, b))) for c in CATS) + r" \\")
    lines += [r"  \bottomrule", r"\end{tabular}"]
    return "\n".join(lines) + "\n"


RBUDGETS = [64, 128, 256, 512, 1024, 1536, 2048]


def ruler_table(out):
    """RULER, compact: one column per budget, two rows (U, M) per method, model column on the left."""
    lines = [r"\begin{tabular}{@{} c l l " + "r" * len(RBUDGETS) + r" @{}}", r"  \toprule",
             r"  \textbf{Model} & \textbf{Method} & & " + " & ".join(rf"\textbf{{{b}}}" for b in RBUDGETS) + r" \\"]
    for model, methods in MODELS:
        lines.append(r"  \midrule")
        for mi, m in enumerate(methods):
            if mi:
                lines.append(rf"  \cmidrule(l){{2-{3 + len(RBUDGETS)}}}")
            us, ms = [], []
            for b in RBUDGETS:
                v = out.get((m, "RULER_ALL", b))
                if v is None:
                    us.append("--"); ms.append("--"); continue
                u, x, floor, resc = v
                mark = ""
                a, c = f"{u:.2f}", f"{x:.2f}"
                if x > u:
                    c = rf"\textbf{{{c}}}"
                elif u > x:
                    a = rf"\textbf{{{a}}}"
                us.append(a); ms.append(c + mark)
            lead = _model(model, 2 * len(methods)) if mi == 0 else ""
            lines.append(rf"  {lead} & \multirow{{2}}{{*}}{{{m.replace(' (Mistral)', '')}}} & Uniform & " + " & ".join(us) + r" \\")
            lines.append(f"   & & MOSAIC & " + " & ".join(ms) + r" \\")
    lines += [r"  \bottomrule", r"\end{tabular}"]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    out = load()
    (HERE / "tables" / "table_ruler_main.tex").write_text("% GENERATED by make_main_table.py -- edit the script, not this file.\n" + ruler_table(out))
    (HERE / "tables").mkdir(exist_ok=True)
    (HERE / "tables" / "table_main.tex").write_text("% GENERATED by make_main_table.py -- edit the script, not this file.\n" + table(out))
    shown = {k: v for k, v in out.items() if k[2] in BUDGETS and v[1] is not None}
    print(f"cells shown {len(shown)} (rescale-only {sum(v[3] for v in shown.values())}, floor 16 {sum(v[2] == 16 for v in shown.values())}); "
          f"MOSAIC > uniform {sum(v[1] > v[0] for v in shown.values())}")
