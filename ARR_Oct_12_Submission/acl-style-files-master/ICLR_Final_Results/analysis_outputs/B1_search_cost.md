## B1 — Search cost: our Step-4 slice search vs EvolKV reproduction

Same machine (local A100-40GB), same model/harness. EvolKV: 60 generations × popsize 10 = 600 fitness evals (+1 final) per budget, 30 calibration samples/eval. Ours (Step 4): capped at `NAS_EVAL_BUDGET` (200 for H2O; SnapKV LongBench ran to saturation), 10% calibration subsample/eval. `~` = wall-clock estimated as rows × this cell's median eval time (a later relaunch overwrote part of its log); `≈` = no timing lines at all, estimated from the median eval time of the same category/method at other budgets. SnapKV run lengths (125-1000 evals) were set by the saturation watchdog, not by design, so the last column normalizes to the 200-eval cap used for all later runs.

| Category | Budget | EvolKV evals | EvolKV samples/eval | EvolKV GPU-h | Ours evals (actual) | Ours samples/eval | Ours GPU-h (actual) | Ours GPU-h @200 evals |
|---|---|---|---|---|---|---|---|---|
| CODE | 128 | 601 | 30 | 12.7 | 542 | 100 | ≈37.6 | 13.9 |
| CODE | 512 | 601 | 30 | 12.9 | 148 | 100 | 9.8 | 13.8 |
| CODE | 1024 | 601 | 30 | 12.7 | 125 | 100 | 8.4 | 13.9 |
| SINGLE_DOCUMENT_QA | 128 | 601 | 30 | 5.2 | 1000 | 55 | 15.3 | 3.0 |
| SINGLE_DOCUMENT_QA | 512 | 601 | 30 | 5.1 | 152 | 55 | 2.5 | 3.4 |
| SINGLE_DOCUMENT_QA | 1024 | 601 | 30 | 5.1 | 211 | 55 | ~3.2 | 3.0 |
| **Total (6 cells)** | | | | **53.7** | | | **76.9** | **51.1** |

Per-sample throughput is identical for both searches (≈2.5 s/sample on CODE, ≈1.0 s/sample on SINGLE_DOCUMENT_QA), so cost per budget is set by evals × samples/eval: EvolKV does many cheap, noisy evals; ours does fewer evals on a 2-3× larger subsample.

**One-time, budget-independent cost (ours only): Step 1 unconstrained search**

| Category | Method | Step-1 evals | Step-1 GPU-h |
|---|---|---|---|
| SINGLE_DOCUMENT_QA | snapkv | 331 | 16.5 |
| SINGLE_DOCUMENT_QA | h2o | 165 | 23.8 |
| MULTI_DOCUMENT_QA | snapkv | 444 | (no timing lines in log) |
| MULTI_DOCUMENT_QA | h2o | 181 | 29.6 |
| SUMMARIZATION | snapkv | 111 | ~60.3 |
| SUMMARIZATION | h2o | 192 | 95.0 |
| RULER_ALL | snapkv | 198 | 25.2 |
| RULER_ALL | h2o | 212 | 46.8 |
| CODE | snapkv/h2o | (Step-1 raw logs lost in the 2026-09-10 `rm -rf`; Step-2 winner survived) | — |

Step 1 runs once per (category, method) and its winner is reused at every budget (see B2); EvolKV has no equivalent amortized stage — its full cost recurs per budget.
