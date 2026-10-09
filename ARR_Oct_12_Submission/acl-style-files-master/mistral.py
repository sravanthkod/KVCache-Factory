#!/usr/bin/env python3
"""Mistral-7B-Instruct-v0.2 results, all full data.
  L2Norm, LongBench + RULER: ICLR_Final_Results/MISTRAL_L2NORM_RESULTS (H100; 30% calibration in every search).
  SnapKV, H2O, AdaKV, RULER: ICLR_Final_Results/MISTRAL_RULER_RESULTS (A100 supercomputer; 10% calibration;
  per-layer floor 16; AdaKV B1024-B2048 searches stopped after 3-26 evaluations).
  SnapKV, H2O, AdaKV, LongBench (Code, Multi-Doc QA, Single-Doc QA; Summarization has Stage 1 only and is excluded):
  ICLR_Final_Results/MISTRAL_LONGBENCH_RESULTS (A100 supercomputer; 30% calibration; per-layer floor 16; H2O truncates
  prompts at 7500 tokens, SnapKV and AdaKV at 31500).
Each budget folder's eval_results.csv lists the re-evaluated candidates by arch index 1..5 = uniform, heuristic, winner,
random, BO; some AdaKV cells lack candidates. load() -> {(method label, CATEGORY, budget): {"uniform", "winner"?, "bo",
"floor"}}, where "bo" is NAS-refined (best of heuristic, random and BO on full data), matching three_way.load()."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "ICLR_Final_Results"
LAB = ["uniform", "heuristic", "winner", "random", "bo"]
NAME = "L2Norm (Mistral)"
NAMES = {"L2Norm": NAME, "SnapKV": "SnapKV (Mistral)", "H2O": "H2O (Mistral)", "AdaKV": "AdaKV (Mistral)"}


def _cell(f, floor):
    sc = {LAB[int(r["arch"]) - 1]: float(r["mean_score"]) for r in csv.DictReader(open(f))}
    nas = [sc[k] for k in ("heuristic", "random", "bo") if k in sc]
    if "uniform" not in sc or not nas:
        return None
    v = {"uniform": sc["uniform"], "bo": max(nas), "floor": floor}
    if "winner" in sc:
        v["winner"] = sc["winner"]
    return v


def load():
    out = {}
    for cat in ["CODE", "MULTI_DOCUMENT_QA", "SINGLE_DOCUMENT_QA", "SUMMARIZATION", "RULER_ALL"]:
        for d in (ROOT / "MISTRAL_L2NORM_RESULTS" / cat).glob("B*"):
            if (d / "eval_results.csv").exists() and (v := _cell(d / "eval_results.csv", 64)):
                out[(NAME, cat, int(d.name[1:]))] = v
    for folder, m in [("SNAPKV", "SnapKV"), ("H2O", "H2O"), ("ADAKV", "AdaKV")]:
        for cat in ["CODE", "MULTI_DOCUMENT_QA", "SINGLE_DOCUMENT_QA"]:
            for d in (ROOT / "MISTRAL_LONGBENCH_RESULTS" / folder / cat).glob("B*"):
                if (d / "eval_results.csv").exists() and (v := _cell(d / "eval_results.csv", 16)):
                    out[(NAMES[m], cat, int(d.name[1:]))] = v
        for d in (ROOT / "MISTRAL_RULER_RESULTS" / folder / "RULER_ALL").glob("B*"):
            if (d / "eval_results.csv").exists() and (v := _cell(d / "eval_results.csv", 16)):
                out[(NAMES[m], "RULER_ALL", int(d.name[1:]))] = v
    return out


if __name__ == "__main__":
    c = load()
    for m in NAMES.values():
        cs = {k: v for k, v in c.items() if k[0] == m}
        w3 = sum(v["winner"] > v["uniform"] for v in cs.values() if "winner" in v)
        n3 = sum("winner" in v for v in cs.values())
        print(f"{m:18s} {len(cs):2d} cells; Stage 3 {w3}/{n3}, Stage 4 {sum(v['bo'] > v['uniform'] for v in cs.values())}/{len(cs)}, "
              f"MOSAIC {sum(max(v.get('winner', -1e9), v['bo']) > v['uniform'] for v in cs.values())}/{len(cs)}")
