#!/usr/bin/env python3
"""H2O RULER uniform baselines from the raw runs (Meta-Llama-3-8B-Instruct/H2O_KV_All_Budgets/results_ruler, local A100,
500 examples per subtask). cells.csv has no uniform row at B64/B256/B512, where only the rescaled winner was run in
Stage 3; these runs supply it (they match cells.csv exactly at B128 and B1024-B2048)."""
import csv
from pathlib import Path

RUNS = Path(__file__).resolve().parents[2] / "Meta-Llama-3-8B-Instruct" / "H2O_KV_All_Budgets" / "results_ruler"


def uniform():
    """{budget: mean string-match accuracy over the 11 RULER subtasks}"""
    out = {}
    for d in sorted(RUNS.glob("h2o_budget_*")):
        b = int(d.name.split("_")[-1])
        f = d / f"meta-llama-3-8b-instruct_{b}" / "4096" / "results.csv"
        if not f.exists():
            continue
        row = {r["dataset"]: r for r in csv.DictReader(open(f))}["H2O"]
        vals = [float(v) for k, v in row.items() if k != "dataset"]
        if len(vals) == 11 and min(vals) >= 0:
            out[b] = sum(vals) / len(vals)
    return out


if __name__ == "__main__":
    for b, u in sorted(uniform().items()):
        print(b, f"{u:.2f}")
