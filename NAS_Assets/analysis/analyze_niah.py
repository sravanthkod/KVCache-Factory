"""
A6 — NIAH subtask breakdown from existing RULER full-data results.

8 of RULER's 11 subtasks are needle-in-a-haystack variants. For each RULER
(method, budget) cell with a multi-config eval, compare uniform vs the best
config (by overall mean) per subtask. Step-3-only cells (uniform + winner) are
included too, flagged by source. Floor era is shown because pre-Sep-2026 RULER
runs used a per-layer floor of 16 (see B3).
"""

import csv
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(HERE)), "ICLR_Final_Results", "analysis_outputs")
NIAH = ["niah_single_1", "niah_single_2", "niah_single_3", "niah_multikey_1",
        "niah_multikey_2", "niah_multikey_3", "niah_multiquery", "niah_multivalue"]
OTHER = ["cwe", "fwe", "vt"]
SHORT = {"niah_single_1": "S1", "niah_single_2": "S2", "niah_single_3": "S3",
         "niah_multikey_1": "MK1", "niah_multikey_2": "MK2", "niah_multikey_3": "MK3",
         "niah_multiquery": "MQ", "niah_multivalue": "MV", "cwe": "CWE", "fwe": "FWE", "vt": "VT"}


def parse(r):
    return {k: float(v) for k, v in (kv.split("=") for kv in r["per_dataset"].split(";"))}


def main():
    rows = [r for r in csv.DictReader(open(os.path.join(OUT_DIR, "cells.csv")))
            if r["benchmark"] == "ruler"]
    cells = defaultdict(list)
    for r in rows:
        cells[(r["method"], int(r["budget"]))].append(r)

    cols = NIAH + OTHER
    out = ["## A6 — RULER subtask breakdown (full-data, string-match %)\n",
           "S1-3 = niah_single_1/2/3, MK1-3 = niah_multikey_1/2/3, MQ = multiquery, MV = multivalue "
           "(8 NIAH subtasks); CWE/FWE/VT = common-word, frequent-word, variable-tracking. "
           "Best = config with the highest 11-subtask mean among those evaluated in the cell. "
           "Floor 16 = pre-Sep-2026 run (see B3; B1024 is floor-confounded, B1536/2048 are not).\n",
           "| Method | Budget | Floor | Source | Config | " + " | ".join(SHORT[c] for c in cols) +
           " | NIAH mean | All-11 mean |",
           "|---|---|---|---|---|" + "---|" * (len(cols) + 2)]
    gains = defaultdict(list)
    for (meth, b), rs in sorted(cells.items()):
        uni = next((r for r in rs if r["label"] == "uniform"), None)
        best = max(rs, key=lambda r: float(r["full_score"]))
        if uni is None or best is uni:
            continue
        pu, pb = parse(uni), parse(best)
        for tag, r, p in (("uniform", uni, pu), (best["label"], best, pb)):
            niah_mean = sum(p[c] for c in NIAH) / len(NIAH)
            out.append(f"| {meth} | {b} | {r['era']} | {r['source']} | {tag} | " +
                       " | ".join(f"{p[c]:.1f}" for c in cols) +
                       f" | {niah_mean:.1f} | {float(r['full_score']):.1f} |")
        d = {c: pb[c] - pu[c] for c in cols}
        out.append(f"| | | | | **Δ** | " + " | ".join(f"{d[c]:+.1f}" for c in cols) +
                   f" | **{sum(d[c] for c in NIAH)/len(NIAH):+.1f}** | "
                   f"**{float(best['full_score']) - float(uni['full_score']):+.1f}** |")
        if best["era"] == "64" or b >= 1536:
            for c in cols:
                gains[c].append(d[c])

    out += ["", "**Mean Δ per subtask over the floor-clean cells** (64-floor cells, plus B1536/B2048 "
            "whose best configs never touch the floor):", "",
            "| " + " | ".join(SHORT[c] for c in cols) + " |", "|" + "---|" * len(cols),
            "| " + " | ".join(f"{sum(gains[c])/len(gains[c]):+.1f}" for c in cols) + " |"]

    path = os.path.join(OUT_DIR, "A6_niah_breakdown.md")
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))
    print(f"\n-> {path}")


if __name__ == "__main__":
    main()
