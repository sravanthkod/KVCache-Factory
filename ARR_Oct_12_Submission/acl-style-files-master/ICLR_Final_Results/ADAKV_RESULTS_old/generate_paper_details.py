#!/usr/bin/env python3
"""AdaKV paper details: calibration vs full-eval for the fixed-budget candidates, search timings, run configuration.

Writes ADAKV_RESULTS/PAPER_DETAILS.md plus data/calibration_vs_full_eval.csv and data/search_timings.csv.
Run: /storage_data/sravanth/venvs/kv/bin/python3 ADAKV_RESULTS/generate_paper_details.py
"""
import csv
import glob
import os
import re
from datetime import date, datetime

import numpy as np
from scipy.stats import kendalltau, spearmanr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "ADAKV_RESULTS")
DATA = os.path.join(OUT, "data")
os.makedirs(DATA, exist_ok=True)


def p(*a):
    return os.path.join(ROOT, *a)


LB_CATS = ["SINGLE_DOCUMENT_QA", "MULTI_DOCUMENT_QA", "CODE"]
PRETTY = {"SINGLE_DOCUMENT_QA": "Single-Doc QA", "MULTI_DOCUMENT_QA": "Multi-Doc QA", "CODE": "Code"}
CELLS = [("LongBench", c, b, f"{c}_B{b}") for c in LB_CATS for b in (128, 256, 512)] + \
        [("RULER", "RULER_ALL", b, f"RULER_ALL_B{b}") for b in (128, 256, 512, 1024, 1536, 2048)]
ARCHS = ["Uniform", "Winner", "Heuristic", "Random", "BO"]
SAMPLE = {"LongBench": "30%", "RULER": "10%"}
# RULER B1024/B1536/B2048 were launched 2026-08-22, before run_ruler_lamp.py's floor changed 16 -> 64 (2026-08-27).
MIN_BUDGET = {"RULER_ALL_B1024": 16, "RULER_ALL_B1536": 16, "RULER_ALL_B2048": 16}
HFF_RE = re.compile(r"\[HFF\] Config \S+: f1=\S+ f2=\S+ time=([0-9.]+)s")


def group(idx):
    if idx == 0:
        return "Uniform"
    if idx <= 5:
        return "Heuristic"
    if idx == 6:
        return "Winner"
    return "Random" if idx < 64 else "BO"


def label(cell):
    bench, cat, b, _ = cell
    return f"{PRETTY.get(cat, 'RULER')} B{b}"


# ─── 1. Calibration vs full evaluation ───────────────────────────────────────
cal_rows, cell_stats = [], []
for cell in CELLS:
    bench, cat, b, d = cell
    arc = np.loadtxt(p(d, "adakv", "output.txt"))
    X, calib_all = arc[:, :32], -arc[:, -1]
    snap = np.atleast_2d(np.loadtxt(p(d, "adakv", "top_configs", "slice_eval_snapshot_5cat.txt")))
    ev = list(csv.DictReader(open(p(d, "adakv", "top_configs", "eval_results.csv"))))
    cands = []
    for k, (s, e) in enumerate(zip(snap, ev)):
        diff = np.abs(X - s[:32]).max(1)
        j = int(diff.argmin())
        assert diff[j] == 0.0, f"{d}: candidate {k} not found in archive"
        assert group(j) == ARCHS[k], f"{d}: candidate {k} at idx {j} is {group(j)}"
        grp_idx = [i for i in range(len(arc)) if group(i) == ARCHS[k]]
        is_group_best = calib_all[j] >= calib_all[grp_idx].max() - 1e-9
        cands.append({"arch": ARCHS[k], "idx": j, "calib": calib_all[j], "full": float(e["mean_score"]),
                      "group_best": is_group_best})
    c = np.array([x["calib"] for x in cands])
    f = np.array([x["full"] for x in cands])
    rho = spearmanr(c, f).correlation
    tau = kendalltau(c, f).correlation
    pick = int(c.argmax())
    best = int(f.argmax())
    u = cands[0]
    bo = cands[4]
    st = {"cell": cell, "cands": cands, "rho": rho, "tau": tau, "pick": ARCHS[pick], "best": ARCHS[best],
          "hit": pick == best, "regret": f[best] - f[pick],
          "bo_cal_gain": bo["calib"] - u["calib"], "bo_full_gain": bo["full"] - u["full"],
          "bo_optimism": (bo["calib"] - u["calib"]) - (bo["full"] - u["full"]),
          "cal_gap_mean": float(np.mean(c - f))}
    cell_stats.append(st)
    for x in cands:
        cal_rows.append([bench, cat, b, x["arch"], x["idx"], group(x["idx"]), SAMPLE[bench], round(x["calib"], 4),
                         round(x["full"], 4), round(x["calib"] - x["full"], 4), x["group_best"]])

with open(os.path.join(DATA, "calibration_vs_full_eval.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["benchmark", "category", "target_budget", "candidate", "archive_row_idx", "archive_group",
                "calibration_sample", "calibration_score", "full_eval_score", "calibration_minus_full",
                "best_calibration_in_its_group"])
    w.writerows(cal_rows)


# ─── 2. Search timings ───────────────────────────────────────────────────────
def hff_times(files):
    t = []
    for fp in files:
        with open(fp, errors="ignore") as fh:
            t += [float(m.group(1)) for m in HFF_RE.finditer(fh.read())]
    return t


def log_date(fp):
    m = re.search(r"(\d\d)_(\d\d)_(\d{4})", os.path.basename(fp))
    return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1))).date() if m else None


# BO overhead per guided iteration (MLP training + differential evolution), from the one search that
# finished normally and printed LAMP's own wall-clock total.
mdqa_log = p("sravanth_logs", "NAS_LONGBENCH_MULTI_DOCUMENT_QA_B256_adakv_10_09_2026.log")
txt = open(mdqa_log, errors="ignore").read()
wall_total = float(re.search(r"TOTAL NAS SEARCH TIME: .*\(([0-9.]+)s\)", txt).group(1))
mdqa_hff = sum(float(x) for x in HFF_RE.findall(txt))
mdqa_rows = sum(1 for _ in open(p("MULTI_DOCUMENT_QA_B256", "adakv", "output.txt")))
BO_OVERHEAD = (wall_total - mdqa_hff) / (mdqa_rows - 64)

runs = []
for cat in LB_CATS:
    runs.append(("Stage 1", "LongBench", PRETTY[cat], p(cat, "adakv", "output.txt"),
                 [p(cat, "adakv", "nas_run.log")]))
for bench, cat, b, d in CELLS:
    if bench == "LongBench":
        files = sorted(glob.glob(p("sravanth_logs", f"NAS_LONGBENCH_{d}_adakv_*.log")))
    else:
        files = sorted(glob.glob(p("sravanth_logs", f"NAS_RULER_B{b}_adakv_*.log")))
    runs.append(("Stage 4", bench, label((bench, cat, b, d)), p(d, "adakv", "output.txt"), files))

timing = []
for stage, bench, name, arc, files in runs:
    t = hff_times(files)
    rows = sum(1 for _ in open(arc))
    mean = float(np.mean(t))
    archive_gpu_h = rows * mean / 3600
    logged_gpu_h = sum(t) / 3600
    wall_h = (rows * mean + max(rows - 64, 0) * BO_OVERHEAD) / 3600
    dates = [x for x in (log_date(f) for f in files) if x]
    start = min(dates) if dates else None
    end = datetime.fromtimestamp(os.path.getmtime(arc)).date()
    timing.append({"stage": stage, "bench": bench, "run": name, "rows": rows, "guided": max(rows - 64, 0),
                   "timed": len(t), "mean_s": mean, "archive_gpu_h": archive_gpu_h, "logged_gpu_h": logged_gpu_h,
                   "wall_h": wall_h, "sessions": len(files), "start": start, "end": end,
                   "files": [os.path.relpath(f, ROOT) for f in files]})

with open(os.path.join(DATA, "search_timings.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["stage", "benchmark", "run", "archive_rows", "guided_iterations", "timed_evals_in_logs",
                "mean_sec_per_eval", "archive_gpu_hours", "total_logged_gpu_hours_incl_restarts",
                "est_wall_clock_hours", "log_sessions", "first_session", "last_archive_write", "log_files"])
    for r in timing:
        w.writerow([r["stage"], r["bench"], r["run"], r["rows"], r["guided"], r["timed"], round(r["mean_s"], 1),
                    round(r["archive_gpu_h"], 2), round(r["logged_gpu_h"], 2), round(r["wall_h"], 2),
                    r["sessions"], r["start"], r["end"], " ".join(r["files"])])


# ─── Markdown ────────────────────────────────────────────────────────────────
L = []
A = L.append
f2 = lambda x: f"{x:.2f}"
A("# AdaKV: calibration scores, search cost and run configuration")
A("")
A(f"_Generated {date.today().isoformat()} by `ADAKV_RESULTS/generate_paper_details.py` from the search archives, "
  "run logs and code. CSVs: `data/calibration_vs_full_eval.csv`, `data/search_timings.csv`._")
A("")
A("> **Read first: calibration sample sizes.** LongBench AdaKV searches used a **30%** calibration sample. "
  "RULER AdaKV searches used **10%**, the same as SnapKV and H2O on RULER (every `NAS_RULER_B*_adakv_*.log` banner says "
  "`Sample Ratio: 0.1`; `run_nas_ruler_slices.sh` defaults to 0.1). The H2O LongBench Stage-1 logs also show 30%. "
  "So a \"AdaKV 30% vs SnapKV/H2O 10%\" comparison holds only if the SnapKV/H2O numbers come from RULER and the AdaKV numbers from LongBench, "
  "which are different benchmarks. On RULER all three methods used 10%.")
A("")

# 1
A("## 1. Calibration score of every fully evaluated fixed-budget candidate")
A("")
A("Each fixed-budget cell fully evaluated 5 candidates. Each one was matched exactly (max |dx| = 0) to its row in "
  "`<CELL>/adakv/output.txt`; the calibration score is that row's search objective (mean task score on the calibration sample, "
  "`-f2`). Full-eval is the full-benchmark mean from `eval_results.csv` (LongBench: all samples; RULER: 500 per task).")
A("")
A("Archive row groups: 0 = uniform, 1-5 = heuristic shapes, 6 = winner anchor, 7-63 = LHS random, 64+ = BO-guided. "
  "Every Heuristic/Random/BO candidate is the **highest-calibration row in its group**, so candidate selection itself was done on the calibration score.")
A("")
A("| Cell | Sample | Uniform (cal / full) | Winner | Heuristic | Random | BO | Calib pick | Full-eval best | Regret | Spearman ρ | Kendall τ |")
A("|---|---|---|---|---|---|---|---|---|---|---|---|")
for st in cell_stats:
    bench = st["cell"][0]
    cells = [f"{f2(x['calib'])} / {f2(x['full'])}" for x in st["cands"]]
    A(f"| {label(st['cell'])} | {SAMPLE[bench]} | " + " | ".join(cells)
      + f" | {st['pick']} | {st['best']} | {st['regret']:.2f} | {st['rho']:+.2f} | {st['tau']:+.2f} |")
A("")
A("Regret = full-eval score of the best candidate minus full-eval score of the candidate with the highest calibration score. "
  "Archive row of each candidate is in the CSV.")
A("")

A("### Summary by benchmark")
A("")
A("| Benchmark | Calibration sample | Cells | Calib pick = full-eval best | Mean regret | Median Spearman ρ | Mean Spearman ρ | Mean BO calibration gain over uniform | Mean BO full-eval gain over uniform | Mean BO optimism |")
A("|---|---|---|---|---|---|---|---|---|---|")
for bench in ("LongBench", "RULER"):
    ss = [s for s in cell_stats if s["cell"][0] == bench]
    A(f"| {bench} | {SAMPLE[bench]} | {len(ss)} | {sum(s['hit'] for s in ss)}/{len(ss)} | "
      f"{np.mean([s['regret'] for s in ss]):.2f} | {np.median([s['rho'] for s in ss]):+.2f} | {np.mean([s['rho'] for s in ss]):+.2f} | "
      f"{np.mean([s['bo_cal_gain'] for s in ss]):+.2f} | {np.mean([s['bo_full_gain'] for s in ss]):+.2f} | "
      f"{np.mean([s['bo_optimism'] for s in ss]):+.2f} |")
A("")
A("BO optimism = (BO − uniform on calibration) − (BO − uniform on full eval). Positive means the search score over-states BO's real gain.")
A("")
A("### BO over-fitting check, per cell")
A("")
A("| Cell | BO archive row | BO − uniform (calibration) | BO − uniform (full eval) | Optimism | BO calib rank among 5 | BO full-eval rank among 5 |")
A("|---|---|---|---|---|---|---|")
for st in cell_stats:
    c = np.array([x["calib"] for x in st["cands"]])
    f = np.array([x["full"] for x in st["cands"]])
    rc = int((c > c[4]).sum()) + 1
    rf = int((f > f[4]).sum()) + 1
    A(f"| {label(st['cell'])} | {st['cands'][4]['idx']} | {st['bo_cal_gain']:+.2f} | {st['bo_full_gain']:+.2f} | "
      f"{st['bo_optimism']:+.2f} | {rc} | {rf} |")
A("")
A("Notes: with 5 candidates per cell, ρ and τ are coarse (ρ moves in steps of 0.1) and several cells span less than 1 point on full eval, "
  "inside run-to-run noise. LongBench calibration and full-eval scores are on the same scale but the 30% sample is not a subset guarantee "
  "of the full ranking. The RULER random candidate is archive row 56 in every cell: the LHS seed is fixed, so it is the same "
  "x-vector decoded at a different target budget.")
A("")

# 2
A("## 2. Search cost")
A("")
A("All AdaKV searches ran on **one NVIDIA RTX A6000 (48 GB) per search**, evaluating candidates sequentially. "
  "Per-evaluation time is taken from the `[HFF] Config ... time=Xs` line printed for every evaluation.")
A("")
A("- **Archive GPU-h** = rows in the final archive × mean seconds per evaluation. This is the cost of the search as reported.")
A("- **Total logged GPU-h** = sum over every logged evaluation, including sessions that crashed and were restarted from scratch.")
A(f"- **Est. wall-clock h** = archive GPU-h + {BO_OVERHEAD:.0f} s × guided iterations. The {BO_OVERHEAD:.0f} s of per-iteration "
  "optimiser overhead (MLP training + differential evolution) comes from the only search that finished normally and printed LAMP's "
  f"own total (Multi-Doc QA B256: {wall_total / 3600:.1f} h for {mdqa_rows} evaluations).")
A("- Calendar dates span idle gaps and crash recovery, so they are not a cost measure. Stage-1 run dates are not recorded "
  "(the archives were copied to this server on 2026-08-17, which is all the file dates show).")
A("")
A("| Stage | Benchmark | Run | Archive rows | Guided iterations | Mean s / eval | Archive GPU-h | Total logged GPU-h | Est. wall-clock h | Sessions | Calendar |")
A("|---|---|---|---|---|---|---|---|---|---|---|")
for r in timing:
    cal = f"{r['start']} to {r['end']}" if r["start"] else "not recorded"
    A(f"| {r['stage']} | {r['bench']} | {r['run']} | {r['rows']} | {r['guided']} | {r['mean_s']:.0f} | {r['archive_gpu_h']:.1f} | "
      f"{r['logged_gpu_h']:.1f} | {r['wall_h']:.1f} | {r['sessions']} | {cal} |")
tot_a = sum(r["archive_gpu_h"] for r in timing)
tot_l = sum(r["logged_gpu_h"] for r in timing)
A(f"| **Total** | | | {sum(r['rows'] for r in timing)} | | | **{tot_a:.0f}** | **{tot_l:.0f}** | | | |")
A("")
A("Gaps and caveats:")
A("- **RULER Stage 1 (AdaKV)** is not on this server: `RULER_ALL/adakv/` holds only the Stage-2 evaluation, with no archive or search log, so its cost can't be reported from here.")
A("- **LongBench Stage 1** timings come from each category's `nas_run.log`, which matches the final archive row for row. "
  "The July `NAS_*_ADA_KV_*.log` files are from runs before the AdaKV cache fix (`ADAKV_NAS_FIX.md`) and are excluded. "
  "Code has 145 timed evaluations for 149 rows (4 rows came from an earlier session whose log is not kept), so its archive GPU-h is an estimate.")
A("- Summarization is excluded (its Stage 1 used the wrong budget grid and is being rerun).")
A("- Stage 2/3 full evaluations are not included here. They are separate from the search.")
A("")

# 3
A("## 3. Run configuration")
A("")
A("All three methods (SnapKV, H2O, AdaKV) use the same search code, `LAMP.py` + `HFF_mod.py`. The only per-run inputs are environment variables, "
  "and no AdaKV launch overrode `NAS_INIT_POINTS` or `NAS_EVAL_BUDGET` (neither appears in any AdaKV log).")
A("")
A("### Common search procedure")
A("")
A("| Setting | Value | Where |")
A("|---|---|---|")
A("| Decision variables | 32 (one per layer), x ∈ [0,1]^32 | `HFF_mod.call_init` |")
A("| Objectives | f1 = mean per-layer budget (minimise), f2 = −mean calibration task score (minimise) | `run_longbench_lamp.py` / `run_ruler_lamp.py` |")
A("| Initial design | 64 points (`NAS_INIT_POINTS`, default 2×32) = anchors + Latin-hypercube samples | `HFF_mod.call_init`, `LAMP.py` |")
A("| LHS seed | 43 (`rng = 42 + 1`) | `LAMP.py` |")
A("| Guided step | Non-dominated sort → rank-1 points labelled class 0 → `MLPClassifier(hidden_layer_sizes=(32,32))` → "
  "`scipy.optimize.differential_evolution` maximises P(class 0) over [0,1]^32 → **1 new evaluation per iteration** | `LAMP.py` |")
A("| Per-objective branch (γ = 0.333 quantile, 10,000 Sobol points) | Never executes: it runs only when `(iteration+1) % N_switch == 0` and `N_switch = budget + 1` | `LAMP.py`, `HFF_mod.call_init` |")
A("| Evaluation cap | 1000 total evaluations (`NAS_EVAL_BUDGET` default) = 64 initial + up to 936 guided | `HFF_mod.call_init` |")
A("| Seed for data sampling | 42 (`NAS_SEED`) | launch commands |")
A("")
A("### Per-stage settings")
A("")
A("| Setting | LongBench Stage 1 | RULER Stage 1 | Stage 4 (fixed budget), LongBench and RULER |")
A("|---|---|---|---|")
A("| Anchors | **5** uniform: all-64/128/256/512/1024 (x = 0.1, 0.3, 0.5, 0.7, 0.9) | **7** uniform: all-64 … all-4096 | **7**: uniform, ascending ramp, descending ramp, middle-heavy triangle, "
  "edge-heavy triangle, alternating low/high (0.15/0.85), winner anchor (0.05 + 0.9·b/max b) |")
A("| LHS points | **59** | 57 | 57 |")
A("| Budget space | Discrete grid {64, 128, 256, 512, 1024} per layer | Discrete grid {64 … 4096}, 7 options | Continuous: per-layer weights rescaled so the mean equals the target exactly; "
  "floor `NAS_MIN_BUDGET`, cap 4096 |")
A("| Minimum per-layer budget | 64 (grid) | 64 (grid) | 64, except RULER B1024/B1536/B2048 = 16 |")
A("| Calibration sample (AdaKV) | 30% | not on this server | LongBench 30%, RULER 10% |")
A("")
A("Evidence for the anchor counts: rows 0-4 of `SINGLE_DOCUMENT_QA`, `MULTI_DOCUMENT_QA` and `CODE` `/adakv/output.txt` are the 5 uniform points, "
  "and the same holds for every LongBench SnapKV and H2O Stage-1 archive (including Summarization, whose SnapKV/H2O archives max out at 1024). "
  "`RULER_ALL/snapkv/output.txt` starts with the 7 uniform points. The Stage-4 shapes are the `NAS_TARGET_BUDGET > 0` branch of `LAMP.py`, "
  "and in every AdaKV cell archive row 6 is the winner anchor.")
A("")
A("### Evaluations actually run and how each search stopped")
A("")
A("No AdaKV search used a fixed iteration count. LongBench Stage 1 and all AdaKV Stage-4 searches were stopped by hand once the archive "
  "looked settled (the queue doc's rule of thumb is ~150-200 rows) or accepted after a crash. Only Multi-Doc QA B256 ran to the 1000-evaluation cap. "
  "No watcher log exists for any AdaKV slice, and RULER AdaKV archives reach 256 rows, above the watcher's default hard cap of 160, so the watcher "
  "was not used for AdaKV. For SnapKV RULER slices the runbook specifies `watch_slices_and_eval.sh`: stop after 40 evaluations without a new best "
  "calibration score, counted from max(row of best, 64), or at 160 rows.")
A("")
A("| Run | Evaluations | Guided iterations |")
A("|---|---|---|")
for r in timing:
    A(f"| {r['stage']} {r['bench']} {r['run']} | {r['rows']} | {r['guided']} |")
A("")
A("So \"7 anchors / 57 LHS / 100 iterations\" is only partly right: 7 + 57 holds for RULER Stage 1 and every Stage-4 search, "
  "LongBench Stage 1 used 5 + 59, and guided iterations ranged from "
  f"{min(r['guided'] for r in timing)} to {max(r['guided'] for r in timing)} rather than a fixed 100.")
A("")
A("### Does the same configuration cover SnapKV and H2O?")
A("")
A("- **Search procedure, initial design size, anchors per stage and evaluation cap:** yes, same code and defaults. The anchor pattern is confirmed from the SnapKV/H2O archives above.")
A("- **Calibration sample:** not uniform across runs. From the log banners: H2O LongBench Stage 1 = 30%; SnapKV RULER Stage 1 and slices = 10%; "
  "H2O RULER Stage 1 = 10% (a first 30% attempt, `NAS_RULER_ALL_h2o_17_08_2026.log`, was superseded by the `_r10` runs). "
  "No SnapKV LongBench search log is on this server, so its sample size can't be confirmed here.")
A("- **Stopping:** SnapKV RULER slices used the automatic 40-stale / 160-row rule; AdaKV searches were stopped manually.")
A("")

open(os.path.join(OUT, "PAPER_DETAILS.md"), "w").write("\n".join(L))
print("Wrote", os.path.join(OUT, "PAPER_DETAILS.md"))
print(f"BO overhead per iteration: {BO_OVERHEAD:.1f}s")
