# AdaKV: calibration scores, search cost and run configuration

_Generated 2026-09-29 by `ADAKV_RESULTS/generate_paper_details.py` from the search archives, run logs and code. CSVs: `data/calibration_vs_full_eval.csv`, `data/search_timings.csv`._

> **Read first: calibration sample sizes.** LongBench AdaKV searches used a **30%** calibration sample. RULER AdaKV searches used **10%**, the same as SnapKV and H2O on RULER (every `NAS_RULER_B*_adakv_*.log` banner says `Sample Ratio: 0.1`; `run_nas_ruler_slices.sh` defaults to 0.1). The H2O LongBench Stage-1 logs also show 30%. So a "AdaKV 30% vs SnapKV/H2O 10%" comparison holds only if the SnapKV/H2O numbers come from RULER and the AdaKV numbers from LongBench, which are different benchmarks. On RULER all three methods used 10%.

## 1. Calibration score of every fully evaluated fixed-budget candidate

Each fixed-budget cell fully evaluated 5 candidates. Each one was matched exactly (max |dx| = 0) to its row in `<CELL>/adakv/output.txt`; the calibration score is that row's search objective (mean task score on the calibration sample, `-f2`). Full-eval is the full-benchmark mean from `eval_results.csv` (LongBench: all samples; RULER: 500 per task).

Archive row groups: 0 = uniform, 1-5 = heuristic shapes, 6 = winner anchor, 7-63 = LHS random, 64+ = BO-guided. Every Heuristic/Random/BO candidate is the **highest-calibration row in its group**, so candidate selection itself was done on the calibration score.

| Cell | Sample | Uniform (cal / full) | Winner | Heuristic | Random | BO | Calib pick | Full-eval best | Regret | Spearman ρ | Kendall τ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Single-Doc QA B128 | 30% | 33.62 / 32.83 | 33.65 / 33.16 | 35.68 / 34.63 | 36.02 / 34.60 | 35.73 / 34.64 | Random | BO | 0.04 | +0.70 | +0.60 |
| Single-Doc QA B256 | 30% | 35.42 / 35.08 | 37.10 / 35.33 | 36.44 / 35.98 | 37.94 / 35.26 | 36.38 / 35.00 | Random | Heuristic | 0.72 | +0.50 | +0.20 |
| Single-Doc QA B512 | 30% | 37.56 / 36.68 | 37.87 / 36.45 | 37.60 / 35.22 | 38.36 / 36.49 | 38.19 / 36.28 | Random | Uniform | 0.20 | -0.10 | +0.00 |
| Multi-Doc QA B128 | 30% | 34.70 / 34.99 | 35.89 / 35.38 | 35.32 / 35.19 | 35.79 / 35.37 | 36.87 / 35.96 | BO | BO | 0.00 | +1.00 | +1.00 |
| Multi-Doc QA B256 | 30% | 34.62 / 35.42 | 36.43 / 36.14 | 35.84 / 35.71 | 36.20 / 35.95 | 37.18 / 36.05 | BO | Winner | 0.09 | +0.90 | +0.80 |
| Multi-Doc QA B512 | 30% | 36.13 / 36.14 | 35.06 / 35.69 | 35.74 / 36.04 | 36.72 / 36.33 | 37.00 / 35.33 | BO | Random | 0.99 | +0.00 | +0.20 |
| Code B128 | 30% | 58.21 / 57.30 | 59.51 / 56.94 | 60.50 / 58.28 | 60.68 / 57.38 | 59.63 / 57.48 | Random | Heuristic | 0.90 | +0.60 | +0.40 |
| Code B256 | 30% | 58.87 / 58.19 | 61.14 / 58.78 | 61.13 / 59.62 | 61.05 / 59.10 | 61.64 / 58.95 | BO | Heuristic | 0.68 | +0.20 | +0.20 |
| Code B512 | 30% | 58.66 / 58.70 | 61.44 / 59.61 | 61.34 / 60.30 | 62.52 / 60.62 | 63.20 / 60.68 | BO | BO | 0.00 | +0.90 | +0.80 |
| RULER B128 | 10% | 51.19 / 50.87 | 55.33 / 55.32 | 56.49 / 55.10 | 57.15 / 57.40 | 55.11 / 55.14 | Random | Random | 0.00 | +0.70 | +0.60 |
| RULER B256 | 10% | 68.52 / 68.01 | 68.05 / 68.74 | 68.32 / 69.51 | 71.86 / 72.10 | 69.85 / 69.89 | Random | Random | 0.00 | +0.70 | +0.60 |
| RULER B512 | 10% | 77.40 / 78.22 | 78.65 / 78.50 | 79.08 / 79.85 | 83.28 / 83.08 | 80.98 / 80.35 | Random | Random | 0.00 | +1.00 | +1.00 |
| RULER B1024 | 10% | 86.70 / 86.87 | 86.91 / 87.10 | 88.77 / 89.08 | 90.34 / 90.10 | 90.71 / 93.78 | BO | BO | 0.00 | +1.00 | +1.00 |
| RULER B1536 | 10% | 90.05 / 89.75 | 93.38 / 94.76 | 97.45 / 97.56 | 98.48 / 97.99 | 93.77 / 94.05 | Random | Random | 0.00 | +0.90 | +0.80 |
| RULER B2048 | 10% | 92.97 / 93.90 | 98.00 / 98.17 | 98.68 / 98.65 | 98.77 / 98.56 | 98.09 / 97.96 | Random | Heuristic | 0.09 | +0.80 | +0.60 |

Regret = full-eval score of the best candidate minus full-eval score of the candidate with the highest calibration score. Archive row of each candidate is in the CSV.

### Summary by benchmark

| Benchmark | Calibration sample | Cells | Calib pick = full-eval best | Mean regret | Median Spearman ρ | Mean Spearman ρ | Mean BO calibration gain over uniform | Mean BO full-eval gain over uniform | Mean BO optimism |
|---|---|---|---|---|---|---|---|---|---|
| LongBench | 30% | 9 | 2/9 | 0.40 | +0.60 | +0.52 | +2.00 | +0.56 | +1.44 |
| RULER | 10% | 6 | 5/6 | 0.02 | +0.85 | +0.85 | +3.61 | +3.93 | -0.31 |

BO optimism = (BO − uniform on calibration) − (BO − uniform on full eval). Positive means the search score over-states BO's real gain.

### BO over-fitting check, per cell

| Cell | BO archive row | BO − uniform (calibration) | BO − uniform (full eval) | Optimism | BO calib rank among 5 | BO full-eval rank among 5 |
|---|---|---|---|---|---|---|
| Single-Doc QA B128 | 75 | +2.11 | +1.82 | +0.29 | 2 | 1 |
| Single-Doc QA B256 | 94 | +0.96 | -0.08 | +1.04 | 4 | 5 |
| Single-Doc QA B512 | 244 | +0.63 | -0.41 | +1.04 | 2 | 4 |
| Multi-Doc QA B128 | 119 | +2.17 | +0.97 | +1.20 | 1 | 1 |
| Multi-Doc QA B256 | 835 | +2.56 | +0.62 | +1.94 | 1 | 2 |
| Multi-Doc QA B512 | 211 | +0.87 | -0.80 | +1.67 | 1 | 5 |
| Code B128 | 90 | +1.42 | +0.18 | +1.24 | 3 | 2 |
| Code B256 | 289 | +2.77 | +0.76 | +2.02 | 1 | 3 |
| Code B512 | 275 | +4.54 | +1.98 | +2.56 | 1 | 1 |
| RULER B128 | 115 | +3.92 | +4.27 | -0.36 | 4 | 3 |
| RULER B256 | 64 | +1.34 | +1.88 | -0.54 | 2 | 2 |
| RULER B512 | 114 | +3.57 | +2.13 | +1.44 | 2 | 2 |
| RULER B1024 | 77 | +4.01 | +6.91 | -2.90 | 1 | 1 |
| RULER B1536 | 122 | +3.72 | +4.30 | -0.58 | 3 | 4 |
| RULER B2048 | 98 | +5.12 | +4.05 | +1.06 | 3 | 4 |

Notes: with 5 candidates per cell, ρ and τ are coarse (ρ moves in steps of 0.1) and several cells span less than 1 point on full eval, inside run-to-run noise. LongBench calibration and full-eval scores are on the same scale but the 30% sample is not a subset guarantee of the full ranking. The RULER random candidate is archive row 56 in every cell: the LHS seed is fixed, so it is the same x-vector decoded at a different target budget.

## 2. Search cost

All AdaKV searches ran on **one NVIDIA RTX A6000 (48 GB) per search**, evaluating candidates sequentially. Per-evaluation time is taken from the `[HFF] Config ... time=Xs` line printed for every evaluation.

- **Archive GPU-h** = rows in the final archive × mean seconds per evaluation. This is the cost of the search as reported.
- **Total logged GPU-h** = sum over every logged evaluation, including sessions that crashed and were restarted from scratch.
- **Est. wall-clock h** = archive GPU-h + 66 s × guided iterations. The 66 s of per-iteration optimiser overhead (MLP training + differential evolution) comes from the only search that finished normally and printed LAMP's own total (Multi-Doc QA B256: 104.6 h for 1000 evaluations).
- Calendar dates span idle gaps and crash recovery, so they are not a cost measure. Stage-1 run dates are not recorded (the archives were copied to this server on 2026-08-17, which is all the file dates show).

| Stage | Benchmark | Run | Archive rows | Guided iterations | Mean s / eval | Archive GPU-h | Total logged GPU-h | Est. wall-clock h | Sessions | Calendar |
|---|---|---|---|---|---|---|---|---|---|---|
| Stage 1 | LongBench | Single-Doc QA | 450 | 386 | 269 | 33.6 | 33.5 | 40.7 | 1 | not recorded |
| Stage 1 | LongBench | Multi-Doc QA | 400 | 336 | 289 | 32.1 | 32.1 | 38.2 | 1 | not recorded |
| Stage 1 | LongBench | Code | 149 | 85 | 867 | 35.9 | 34.9 | 37.5 | 1 | not recorded |
| Stage 4 | LongBench | Single-Doc QA B128 | 141 | 77 | 563 | 22.0 | 21.6 | 23.4 | 1 | 2026-09-07 to 2026-09-08 |
| Stage 4 | LongBench | Single-Doc QA B256 | 147 | 83 | 536 | 21.9 | 21.3 | 23.4 | 1 | 2026-09-07 to 2026-09-08 |
| Stage 4 | LongBench | Single-Doc QA B512 | 253 | 189 | 361 | 25.4 | 30.0 | 28.8 | 3 | 2026-09-08 to 2026-09-10 |
| Stage 4 | LongBench | Multi-Doc QA B128 | 166 | 102 | 548 | 25.3 | 32.0 | 27.1 | 5 | 2026-09-08 to 2026-09-11 |
| Stage 4 | LongBench | Multi-Doc QA B256 | 1000 | 936 | 315 | 87.4 | 87.4 | 104.6 | 1 | 2026-09-10 to 2026-09-15 |
| Stage 4 | LongBench | Multi-Doc QA B512 | 212 | 148 | 309 | 18.2 | 18.2 | 20.9 | 1 | 2026-09-15 to 2026-09-16 |
| Stage 4 | LongBench | Code B128 | 97 | 33 | 966 | 26.0 | 26.0 | 26.6 | 1 | 2026-09-15 to 2026-09-16 |
| Stage 4 | LongBench | Code B256 | 359 | 295 | 978 | 97.5 | 97.0 | 102.9 | 3 | 2026-09-16 to 2026-09-21 |
| Stage 4 | LongBench | Code B512 | 307 | 243 | 882 | 75.2 | 75.0 | 79.7 | 1 | 2026-09-18 to 2026-09-21 |
| Stage 4 | RULER | RULER B128 | 204 | 140 | 1577 | 89.4 | 88.5 | 91.9 | 1 | 2026-08-27 to 2026-08-31 |
| Stage 4 | RULER | RULER B256 | 108 | 44 | 1610 | 48.3 | 59.9 | 49.1 | 5 | 2026-08-27 to 2026-09-02 |
| Stage 4 | RULER | RULER B512 | 206 | 142 | 1572 | 90.0 | 89.1 | 92.6 | 1 | 2026-08-27 to 2026-08-31 |
| Stage 4 | RULER | RULER B1024 | 256 | 192 | 1586 | 112.8 | 112.4 | 116.3 | 2 | 2026-08-22 to 2026-08-31 |
| Stage 4 | RULER | RULER B1536 | 199 | 135 | 1510 | 83.5 | 83.1 | 86.0 | 1 | 2026-08-22 to 2026-08-25 |
| Stage 4 | RULER | RULER B2048 | 194 | 130 | 1545 | 83.3 | 83.3 | 85.6 | 1 | 2026-08-22 to 2026-08-25 |
| **Total** | | | 4848 | | | **1008** | **1025** | | | |

Gaps and caveats:
- **RULER Stage 1 (AdaKV)** is not on this server: `RULER_ALL/adakv/` holds only the Stage-2 evaluation, with no archive or search log, so its cost can't be reported from here.
- **LongBench Stage 1** timings come from each category's `nas_run.log`, which matches the final archive row for row. The July `NAS_*_ADA_KV_*.log` files are from runs before the AdaKV cache fix (`ADAKV_NAS_FIX.md`) and are excluded. Code has 145 timed evaluations for 149 rows (4 rows came from an earlier session whose log is not kept), so its archive GPU-h is an estimate.
- Summarization is excluded (its Stage 1 used the wrong budget grid and is being rerun).
- Stage 2/3 full evaluations are not included here. They are separate from the search.

## 3. Run configuration

All three methods (SnapKV, H2O, AdaKV) use the same search code, `LAMP.py` + `HFF_mod.py`. The only per-run inputs are environment variables, and no AdaKV launch overrode `NAS_INIT_POINTS` or `NAS_EVAL_BUDGET` (neither appears in any AdaKV log).

### Common search procedure

| Setting | Value | Where |
|---|---|---|
| Decision variables | 32 (one per layer), x ∈ [0,1]^32 | `HFF_mod.call_init` |
| Objectives | f1 = mean per-layer budget (minimise), f2 = −mean calibration task score (minimise) | `run_longbench_lamp.py` / `run_ruler_lamp.py` |
| Initial design | 64 points (`NAS_INIT_POINTS`, default 2×32) = anchors + Latin-hypercube samples | `HFF_mod.call_init`, `LAMP.py` |
| LHS seed | 43 (`rng = 42 + 1`) | `LAMP.py` |
| Guided step | Non-dominated sort → rank-1 points labelled class 0 → `MLPClassifier(hidden_layer_sizes=(32,32))` → `scipy.optimize.differential_evolution` maximises P(class 0) over [0,1]^32 → **1 new evaluation per iteration** | `LAMP.py` |
| Per-objective branch (γ = 0.333 quantile, 10,000 Sobol points) | Never executes: it runs only when `(iteration+1) % N_switch == 0` and `N_switch = budget + 1` | `LAMP.py`, `HFF_mod.call_init` |
| Evaluation cap | 1000 total evaluations (`NAS_EVAL_BUDGET` default) = 64 initial + up to 936 guided | `HFF_mod.call_init` |
| Seed for data sampling | 42 (`NAS_SEED`) | launch commands |

### Per-stage settings

| Setting | LongBench Stage 1 | RULER Stage 1 | Stage 4 (fixed budget), LongBench and RULER |
|---|---|---|---|
| Anchors | **5** uniform: all-64/128/256/512/1024 (x = 0.1, 0.3, 0.5, 0.7, 0.9) | **7** uniform: all-64 … all-4096 | **7**: uniform, ascending ramp, descending ramp, middle-heavy triangle, edge-heavy triangle, alternating low/high (0.15/0.85), winner anchor (0.05 + 0.9·b/max b) |
| LHS points | **59** | 57 | 57 |
| Budget space | Discrete grid {64, 128, 256, 512, 1024} per layer | Discrete grid {64 … 4096}, 7 options | Continuous: per-layer weights rescaled so the mean equals the target exactly; floor `NAS_MIN_BUDGET`, cap 4096 |
| Minimum per-layer budget | 64 (grid) | 64 (grid) | 64, except RULER B1024/B1536/B2048 = 16 |
| Calibration sample (AdaKV) | 30% | not on this server | LongBench 30%, RULER 10% |

Evidence for the anchor counts: rows 0-4 of `SINGLE_DOCUMENT_QA`, `MULTI_DOCUMENT_QA` and `CODE` `/adakv/output.txt` are the 5 uniform points, and the same holds for every LongBench SnapKV and H2O Stage-1 archive (including Summarization, whose SnapKV/H2O archives max out at 1024). `RULER_ALL/snapkv/output.txt` starts with the 7 uniform points. The Stage-4 shapes are the `NAS_TARGET_BUDGET > 0` branch of `LAMP.py`, and in every AdaKV cell archive row 6 is the winner anchor.

### Evaluations actually run and how each search stopped

No AdaKV search used a fixed iteration count. LongBench Stage 1 and all AdaKV Stage-4 searches were stopped by hand once the archive looked settled (the queue doc's rule of thumb is ~150-200 rows) or accepted after a crash. Only Multi-Doc QA B256 ran to the 1000-evaluation cap. No watcher log exists for any AdaKV slice, and RULER AdaKV archives reach 256 rows, above the watcher's default hard cap of 160, so the watcher was not used for AdaKV. For SnapKV RULER slices the runbook specifies `watch_slices_and_eval.sh`: stop after 40 evaluations without a new best calibration score, counted from max(row of best, 64), or at 160 rows.

| Run | Evaluations | Guided iterations |
|---|---|---|
| Stage 1 LongBench Single-Doc QA | 450 | 386 |
| Stage 1 LongBench Multi-Doc QA | 400 | 336 |
| Stage 1 LongBench Code | 149 | 85 |
| Stage 4 LongBench Single-Doc QA B128 | 141 | 77 |
| Stage 4 LongBench Single-Doc QA B256 | 147 | 83 |
| Stage 4 LongBench Single-Doc QA B512 | 253 | 189 |
| Stage 4 LongBench Multi-Doc QA B128 | 166 | 102 |
| Stage 4 LongBench Multi-Doc QA B256 | 1000 | 936 |
| Stage 4 LongBench Multi-Doc QA B512 | 212 | 148 |
| Stage 4 LongBench Code B128 | 97 | 33 |
| Stage 4 LongBench Code B256 | 359 | 295 |
| Stage 4 LongBench Code B512 | 307 | 243 |
| Stage 4 RULER RULER B128 | 204 | 140 |
| Stage 4 RULER RULER B256 | 108 | 44 |
| Stage 4 RULER RULER B512 | 206 | 142 |
| Stage 4 RULER RULER B1024 | 256 | 192 |
| Stage 4 RULER RULER B1536 | 199 | 135 |
| Stage 4 RULER RULER B2048 | 194 | 130 |

So "7 anchors / 57 LHS / 100 iterations" is only partly right: 7 + 57 holds for RULER Stage 1 and every Stage-4 search, LongBench Stage 1 used 5 + 59, and guided iterations ranged from 33 to 936 rather than a fixed 100.

### Does the same configuration cover SnapKV and H2O?

- **Search procedure, initial design size, anchors per stage and evaluation cap:** yes, same code and defaults. The anchor pattern is confirmed from the SnapKV/H2O archives above.
- **Calibration sample:** not uniform across runs. From the log banners: H2O LongBench Stage 1 = 30%; SnapKV RULER Stage 1 and slices = 10%; H2O RULER Stage 1 = 10% (a first 30% attempt, `NAS_RULER_ALL_h2o_17_08_2026.log`, was superseded by the `_r10` runs). No SnapKV LongBench search log is on this server, so its sample size can't be confirmed here.
- **Stopping:** SnapKV RULER slices used the automatic 40-stale / 160-row rule; AdaKV searches were stopped manually.
