"""
B2 — one search, many budgets. For every (category, method), compare the
rescaled Step-2 winner shape against uniform at each target budget, using the
full-data scores in analysis_outputs/cells.csv (5-way rows preferred over the
2-row Step-3 eval when both exist; they are the same two configs).

The winner shape comes from ONE unconstrained Step-1 search + Step-2 full-data
pick, then is proportionally rescaled to each target with no further search.
"""

import csv
import os
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
NAS = os.path.dirname(HERE)
OUT_DIR = os.path.join(os.path.dirname(NAS), "ICLR_Final_Results", "analysis_outputs")
ANCHORS = {
    ("longbench", c, m): os.path.join(NAS, "anchors", f"anchor_longbench_{c}_{m}.txt")
    for c in ("CODE", "MULTI_DOCUMENT_QA", "SINGLE_DOCUMENT_QA", "SUMMARIZATION")
    for m in ("snapkv", "h2o")
}
ANCHORS[("ruler", "RULER_ALL", "snapkv")] = os.path.join(NAS, "anchor_1756_budgets.txt")
ANCHORS[("ruler", "RULER_ALL", "h2o")] = os.path.join(NAS, "anchors", "anchor_h2o_2180.txt")
SOURCE_PRIORITY = {"five_way": 0, "slice_eval": 1, "step3": 2}


def main():
    rows = list(csv.DictReader(open(os.path.join(OUT_DIR, "cells.csv"))))
    best = {}
    for r in rows:
        if r["label"] not in ("uniform", "winner"):
            continue
        key = (r["benchmark"], r["category"], r["method"], int(r["budget"]), r["label"])
        if key not in best or SOURCE_PRIORITY[r["source"]] < SOURCE_PRIORITY[best[key]["source"]]:
            best[key] = r

    groups = defaultdict(dict)
    for (bm, cat, meth, b, lab), r in best.items():
        groups[(bm, cat, meth)].setdefault(b, {})[lab] = r

    out = ["## B2 — One search, many budgets (rescaled Step-2 winner vs uniform, full-data)\n",
           "Each winner shape was found once by the unconstrained Step-1 search and picked on "
           "full data in Step 2, then proportionally rescaled to every target budget "
           "(`0.05 + 0.9·b/max(b)`, continuous decode) with **no further search**. "
           "EvolKV, by contrast, re-runs its full CMA-ES search per target budget.\n",
           "| Benchmark | Category | Method | Winner's natural avg budget | Budget | Floor | "
           "Uniform | Rescaled winner | Δ |",
           "|---|---|---|---|---|---|---|---|---|"]
    summary = []
    for (bm, cat, meth), by_b in sorted(groups.items()):
        ap = ANCHORS.get((bm, cat, meth))
        nat = f"{np.loadtxt(ap).mean():.0f}" if ap and os.path.isfile(ap) else "?"
        wins = n = 0
        deltas = []
        for b in sorted(by_b):
            pair = by_b[b]
            if "uniform" not in pair or "winner" not in pair:
                continue
            if b == 64 and bm == "longbench":
                continue  # floor==target: winner collapses to uniform, degenerate
            u, w = float(pair["uniform"]["full_score"]), float(pair["winner"]["full_score"])
            era = pair["winner"]["era"]
            d = w - u
            n += 1
            wins += d > 0
            deltas.append(d)
            out.append(f"| {bm} | {cat} | {meth} | {nat} | {b} | {era} | {u:.2f} | {w:.2f} | {d:+.2f} |")
        if n:
            summary.append((bm, cat, meth, nat, wins, n, sum(deltas) / n))

    out += ["", "**Summary per (category, method)**", "",
            "| Benchmark | Category | Method | Natural avg budget | Budgets where winner > uniform | Mean Δ |",
            "|---|---|---|---|---|---|"]
    tw = tn = 0
    for bm, cat, meth, nat, wins, n, md in summary:
        out.append(f"| {bm} | {cat} | {meth} | {nat} | {wins}/{n} | {md:+.2f} |")
        tw += wins
        tn += n
    out.append(f"\n**Overall: rescaled winner beats uniform at {tw}/{tn} (category, method, budget) cells.**")

    path = os.path.join(OUT_DIR, "B2_winner_transfer.md")
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))
    print(f"\n-> {path}")


if __name__ == "__main__":
    main()
