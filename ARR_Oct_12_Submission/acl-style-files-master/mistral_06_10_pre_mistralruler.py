#!/usr/bin/env python3
"""Mistral-7B-Instruct-v0.2 results (L2Norm only so far), from ICLR_Final_Results/MISTRAL_L2NORM_RESULTS (H100 server;
30% calibration subset in every search; all scores full data). Each budget folder's eval_results.csv holds the five
re-evaluated candidates in the order uniform, heuristic, winner, random, BO.
load() -> {("L2Norm (Mistral)", CATEGORY, budget): {"uniform", "winner", "bo"}}, where "bo" is NAS-refined (best of
heuristic, random and BO on full data), matching three_way.load()."""
import csv
from pathlib import Path

RES = Path(__file__).resolve().parents[2] / "ICLR_Final_Results" / "MISTRAL_L2NORM_RESULTS"
LAB = ["uniform", "heuristic", "winner", "random", "bo"]
NAME = "L2Norm (Mistral)"


def load():
    out = {}
    for cat in ["CODE", "MULTI_DOCUMENT_QA", "SINGLE_DOCUMENT_QA", "SUMMARIZATION", "RULER_ALL"]:
        for d in (RES / cat).glob("B*"):
            f = d / "eval_results.csv"
            if not f.exists():
                continue
            sc = {LAB[int(r["arch"]) - 1]: float(r["mean_score"]) for r in csv.DictReader(open(f))}
            if len(sc) != 5:
                continue
            out[(NAME, cat, int(d.name[1:]))] = {"uniform": sc["uniform"], "winner": sc["winner"],
                                                 "bo": max(sc["heuristic"], sc["random"], sc["bo"]), "floor": 64}
    return out


if __name__ == "__main__":
    c = load()
    w3 = sum(v["winner"] > v["uniform"] for v in c.values())
    w4 = sum(v["bo"] > v["uniform"] for v in c.values())
    wf = sum(max(v["winner"], v["bo"]) > v["uniform"] for v in c.values())
    print(f"{len(c)} cells; Stage 3 {w3}, Stage 4 {w4}, MOSAIC {wf} beat uniform; NAS-refined >= Winner in "
          f"{sum(v['bo'] >= v['winner'] for v in c.values())}")
