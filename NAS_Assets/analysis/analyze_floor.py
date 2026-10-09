"""
B3 — minimum per-layer budget (floor) justification.

Mechanism: for SnapKV and H2O, run_longbench_lamp.set_model_budgets fixes
window_size=8 regardless of budget (run_longbench_lamp.py:314-318), and both
SnapKVCluster and H2OKVCluster assert max_capacity_prompt - window_size > 0.
So a layer with budget b keeps the 8 most recent tokens plus (b - 8) tokens
selected by attention score from the rest of the context.

Evidence: for every evaluated best config in analysis_outputs/cells.csv, count
layers sitting exactly at the floor in effect when it was evaluated.
"""

import csv
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(HERE)), "ICLR_Final_Results", "analysis_outputs")
WINDOW = 8


def main():
    rows = list(csv.DictReader(open(os.path.join(OUT_DIR, "cells.csv"))))
    cells = defaultdict(list)
    for r in rows:
        if r["source"] != "step3":
            cells[(r["benchmark"], r["category"], int(r["budget"]), r["method"], int(r["era"]))].append(r)

    out = ["## B3 — Why the per-layer floor is 64, not 16\n",
           f"SnapKV/H2O always keep a fixed **{WINDOW}-token recent window** "
           "(`window_size=8`, `run_longbench_lamp.py:314-318`), enforced by "
           "`assert max_capacity_prompt - window_size > 0` in `SnapKVCluster`/`H2OKVCluster`. "
           f"A layer with budget *b* therefore selects only *b − {WINDOW}* tokens by attention "
           "score from the whole context.\n",
           "| Per-layer budget | Recent window (always kept) | Attention-selected tokens |",
           "|---|---|---|"]
    for b in (16, 32, 64, 128):
        out.append(f"| {b} | {WINDOW} | {b - WINDOW} |")
    out += ["", "At budget 16 only 8 tokens are chosen from a context of thousands — effectively noise. "
            "Raising the floor to 64 gives 56 selected tokens (7×).\n",
            "**How often the best-scoring config parks layers exactly at the floor** "
            "(best = highest full-data score among the evaluated configs of each cell):", "",
            "| Benchmark | Category | Budget | Method | Floor in effect | Best label | "
            "Layers at floor | Share |",
            "|---|---|---|---|---|---|---|---|"]
    for (bm, cat, b, meth, era), rs in sorted(cells.items()):
        best = max(rs, key=lambda r: float(r["full_score"]))
        budgets = [int(x) for x in best["budgets"].split()]
        n_floor = sum(x <= era for x in budgets)
        out.append(f"| {bm} | {cat} | {b} | {meth} | {era} | {best['label']} | "
                   f"{n_floor}/{len(budgets)} | {n_floor/len(budgets):.0%} |")
    out += ["", "Reading: when the floor was 16, the search pushed up to two-thirds of layers "
            "(RULER B1024, H2O) down into the 8-selected-token regime — exploiting a degenerate "
            "setting rather than finding a meaningful allocation — while at B1536/B2048 it never "
            "needed to (0 layers), so those results are floor-independent. Under floor=64 many "
            "best configs still sit a large share of layers at the floor, i.e. the floor is an "
            "active constraint and the choice of value matters."]

    path = os.path.join(OUT_DIR, "B3_floor.md")
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))
    print(f"\n-> {path}")


if __name__ == "__main__":
    main()
