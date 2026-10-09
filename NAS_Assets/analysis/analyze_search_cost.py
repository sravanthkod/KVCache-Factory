"""
B1 — search cost: our Step-4 slice search vs the EvolKV reproduction, at the 6
matched (category, budget) cells (SnapKV x {CODE, SINGLE_DOCUMENT_QA} x
{128, 512, 1024}). Same local A100-40GB box, same model, same harness.

Our per-eval times come from "[HFF] Config ... time=Xs" lines in each cell's
nas_run.log. Where a later relaunch overwrote part of the log (timed evals <
90% of output.txt rows), wall-clock is estimated as rows x median eval time.
EvolKV wall-clock comes from START/END stamps in EVOLKV_GRID_10_09_2026.log.
"""

import datetime
import json
import os
import re
import statistics

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
NAS = os.path.dirname(HERE)
ROOT = os.path.dirname(NAS)
OUT_DIR = os.path.join(ROOT, "ICLR_Final_Results", "analysis_outputs")
LB = os.path.join(ROOT, "data", "LongBench")
DATASETS = {"CODE": ["lcc", "repobench-p"],
            "SINGLE_DOCUMENT_QA": ["narrativeqa", "qasper", "multifieldqa_en"],
            "MULTI_DOCUMENT_QA": ["hotpotqa", "2wikimqa", "musique"],
            "SUMMARIZATION": ["gov_report", "qmsum", "multi_news"]}
NAS_SAMPLE_RATIO = 0.1
EVOLKV_CALIB = 30


def n_lines(ds):
    with open(os.path.join(LB, f"{ds}.jsonl")) as f:
        return sum(1 for _ in f)


def ours_samples_per_eval(cat):
    return sum(max(1, int(n_lines(d) * NAS_SAMPLE_RATIO)) for d in DATASETS[cat])


def evolkv_samples_per_eval(cat):
    per = max(1, EVOLKV_CALIB // len(DATASETS[cat]))
    return sum(min(n_lines(d), per) for d in DATASETS[cat])


def eval_times(cell_dir):
    log = os.path.join(cell_dir, "nas_run.log")
    if not os.path.isfile(log):
        return []
    return [float(t) for t in re.findall(r"\[HFF\] Config.*time=([0-9.]+)s", open(log).read())]


def sibling_median(cat, meth):
    ts = []
    for b in (128, 256, 512, 1024):
        ts += eval_times(os.path.join(NAS, f"{cat}_B{b}", meth))
    return statistics.median(ts) if ts else float("nan")


def step_cost(cell_dir, fallback_median=float("nan")):
    rows = len(np.atleast_2d(np.loadtxt(os.path.join(cell_dir, "output.txt"))))
    times = eval_times(cell_dir)
    if times and len(times) >= 0.9 * rows:
        return rows, sum(times) / 3600, "", statistics.median(times)
    med = statistics.median(times) if times else fallback_median
    return rows, rows * med / 3600, "~" if times else "≈", med


def evolkv_wallclock():
    log = os.path.join(ROOT, "sravanth_logs", "EVOLKV_GRID_10_09_2026.log")
    stamps = {}
    for line in open(log):
        m = re.match(r"=== \[(.+?)\] (START|END) category=(\S+) budget=(\d+)", line)
        if m:
            t = datetime.datetime.strptime(m.group(1), "%a %b %d %I:%M:%S %p UTC %Y")
            stamps.setdefault((m.group(3), int(m.group(4))), {})[m.group(2)] = t
    gens = len(re.findall(r"done, running F_best", open(log).read())) // max(1, len(stamps))
    return {k: (v["END"] - v["START"]).total_seconds() / 3600 for k, v in stamps.items()}, gens


def main():
    ek_hours, gens_per_run = evolkv_wallclock()
    popsize = 10
    ek_evals = gens_per_run * popsize + 1  # + final post-completion eval
    out = ["## B1 — Search cost: our Step-4 slice search vs EvolKV reproduction\n",
           f"Same machine (local A100-40GB), same model/harness. EvolKV: {gens_per_run} generations × "
           f"popsize {popsize} = {ek_evals - 1} fitness evals (+1 final) per budget, "
           f"{EVOLKV_CALIB} calibration samples/eval. Ours (Step 4): capped at `NAS_EVAL_BUDGET` "
           f"(200 for H2O; SnapKV LongBench ran to saturation), {int(NAS_SAMPLE_RATIO*100)}% "
           "calibration subsample/eval. `~` = wall-clock estimated as rows × this cell's median "
           "eval time (a later relaunch overwrote part of its log); `≈` = no timing lines at all, "
           "estimated from the median eval time of the same category/method at other budgets. "
           "SnapKV run lengths (125-1000 evals) were set by the saturation watchdog, not by design, "
           "so the last column normalizes to the 200-eval cap used for all later runs.\n",
           "| Category | Budget | EvolKV evals | EvolKV samples/eval | EvolKV GPU-h | "
           "Ours evals (actual) | Ours samples/eval | Ours GPU-h (actual) | Ours GPU-h @200 evals |",
           "|---|---|---|---|---|---|---|---|---|"]
    tot = {"ek_h": 0, "ours_h": 0, "ours200": 0}
    for cat in ("CODE", "SINGLE_DOCUMENT_QA"):
        ek_spe, our_spe = evolkv_samples_per_eval(cat), ours_samples_per_eval(cat)
        fb = sibling_median(cat, "snapkv")
        for b in (128, 512, 1024):
            rows, hours, flag, med = step_cost(os.path.join(NAS, f"{cat}_B{b}", "snapkv"), fb)
            ekh = ek_hours[(cat, b)]
            h200 = 200 * med / 3600
            out.append(f"| {cat} | {b} | {ek_evals} | {ek_spe} | {ekh:.1f} | "
                       f"{rows} | {our_spe} | {flag}{hours:.1f} | {h200:.1f} |")
            tot["ek_h"] += ekh
            tot["ours_h"] += hours
            tot["ours200"] += h200
    out.append(f"| **Total (6 cells)** | | | | **{tot['ek_h']:.1f}** | | | **{tot['ours_h']:.1f}** | "
               f"**{tot['ours200']:.1f}** |")
    out += ["", "Per-sample throughput is identical for both searches (≈2.5 s/sample on CODE, "
            "≈1.0 s/sample on SINGLE_DOCUMENT_QA), so cost per budget is set by evals × samples/eval: "
            "EvolKV does many cheap, noisy evals; ours does fewer evals on a 2-3× larger subsample."]

    out += ["", "**One-time, budget-independent cost (ours only): Step 1 unconstrained search**", "",
            "| Category | Method | Step-1 evals | Step-1 GPU-h |", "|---|---|---|---|"]
    for cat in ("SINGLE_DOCUMENT_QA", "MULTI_DOCUMENT_QA", "SUMMARIZATION", "RULER_ALL"):
        for meth in ("snapkv", "h2o"):
            d = os.path.join(NAS, cat, meth)
            if os.path.isfile(os.path.join(d, "output.txt")) and os.path.isfile(os.path.join(d, "nas_run.log")):
                rows, hours, flag, _ = step_cost(d)
                shown = f"{flag}{hours:.1f}" if hours == hours else "(no timing lines in log)"
                out.append(f"| {cat} | {meth} | {rows} | {shown} |")
    out.append("| CODE | snapkv/h2o | (Step-1 raw logs lost in the 2026-09-10 `rm -rf`; Step-2 winner survived) | — |")
    out += ["", "Step 1 runs once per (category, method) and its winner is reused at every budget "
            "(see B2); EvolKV has no equivalent amortized stage — its full cost recurs per budget."]

    path = os.path.join(OUT_DIR, "B1_search_cost.md")
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))
    print(f"\n-> {path}")


if __name__ == "__main__":
    main()
