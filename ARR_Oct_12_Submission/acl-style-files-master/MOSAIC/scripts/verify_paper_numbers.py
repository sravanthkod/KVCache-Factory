#!/usr/bin/env python3
"""Recompute the paper's headline counts from results/cells.csv and check them against the values printed in the paper.

    python scripts/verify_paper_numbers.py          # exit code 0 if every check passes

Also checks that every released allocation has 32 layers and averages exactly its target budget."""
import csv
import sys
from collections import defaultdict
from pathlib import Path

CSV = Path(__file__).resolve().parents[1] / "results" / "cells.csv"
rows = list(csv.DictReader(open(CSV)))
f = lambda x: float(x) if x not in ("", None) else None


def wins(rs, col):
    rs = [r for r in rs if f(r[col]) is not None]
    return sum(f(r[col]) > f(r["uniform"]) for r in rs), len(rs)


searched = [r for r in rows if r["stage4_search"] == "1"]
llama = [r for r in searched if r["model"].startswith("Llama")]
mistral = [r for r in searched if r["model"].startswith("Mistral")]
llama_s3 = [r for r in rows if r["model"].startswith("Llama") and r["winner"]]  # all Stage 3 cells, incl. those without Stage 4

checks = [
    ("MOSAIC beats uniform, Llama cells with a Stage 4 search", wins(llama, "mosaic"), (74, 78)),
    ("MOSAIC beats uniform, Mistral cells", wins(mistral, "mosaic"), (72, 76)),
    ("MOSAIC beats uniform, all searched cells (abstract)", wins(searched, "mosaic"), (146, 154)),
    ("rescaled Winner beats uniform, all Llama cells", wins(llama_s3, "winner"), (75, 87)),
    ("rescaled Winner beats uniform, Mistral cells", wins([r for r in mistral if r["winner"]], "winner"), (51, 75)),
    ("NAS-refined beats uniform, Mistral cells", wins(mistral, "nas_refined"), (71, 76)),
]
ok = True
print(f"{len(rows)} rows in {CSV.name}\n")
for name, got, want in checks:
    good = got == want
    ok &= good
    print(f"[{'ok' if good else 'MISMATCH'}] {name}: {got[0]}/{got[1]}" + ("" if good else f"  (paper: {want[0]}/{want[1]})"))

by = defaultdict(list)
for r in searched:
    by[(r["model"].split("-")[0], r["method"])].append(r)
print("\nper model and method (MOSAIC beats uniform / cells):")
for (m, meth), rs in sorted(by.items()):
    w = wins(rs, "mosaic")
    print(f"  {m:8s} {meth:7s} {w[0]:3d}/{w[1]}")

bad = 0
for r in rows:
    for col in ("winner_allocation", "nas_refined_allocation"):
        if r[col]:
            b = [int(x) for x in r[col].split()]
            bad += not (len(b) == 32 and sum(b) == 32 * int(r["budget"]))
print(f"\nallocations with 32 layers and mean == budget: {'all' if not bad else f'{bad} FAILED'}")
sys.exit(0 if ok and not bad else 1)
