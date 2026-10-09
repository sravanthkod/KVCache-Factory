# NAS for Per-Layer KV Cache Budget Allocation — Top Configs

This directory contains Neural Architecture Search (NAS) results for finding optimal per-layer KV cache budget allocations across 4 LongBench task categories. Each NAS run searches over 32-layer budget configurations (one budget per transformer layer) to find Pareto-optimal trade-offs between average KV cache budget and task performance.

---

## Overview

| Item | Details |
|---|---|
| **Model** | Meta-Llama-3-8B-Instruct |
| **Layers** | 32 |
| **Budget Search Space** | {64, 128, 256, 512, 1024} per layer |
| **NAS Method** | Multi-objective optimization (score vs. avg_budget) |
| **Methods Searched** | SnapKV, H2O, AdaKV |
| **Task Categories** | Single-Doc QA, Multi-Doc QA, Code, Summarization |

### Completeness Summary

| Task Category | SnapKV | H2O | AdaKV |
|---|---|---|---|
| **Single-Doc QA** | ✅ 20 configs | ✅ 15 configs | ❌ Incomplete (no top_configs) |
| **Multi-Doc QA** | ✅ 9 configs | ✅ 10 configs | ❌ Incomplete (no top_configs) |
| **Code** | ✅ 11 configs | ✅ 19 configs | ❌ Not run |
| **Summarization** | ✅ 12 configs | ❌ Not run | ❌ Not run |

> AdaKV NAS runs did not complete for any task category. H2O was not run for Summarization. SnapKV completed all 4 categories.

---

## 1. Single-Doc QA (narrativeqa, qasper, multifieldqa_en)

### 1.1 SnapKV — Top Configs (Pareto Front)

| # | Avg Budget | Avg Score | narrativeqa | qasper | multifieldqa_en |
|---|---|---|---|---|---|
| 0 | 64 | 29.61 | 18.51 | 28.46 | 41.86 |
| 1 | 70 | 30.67 | 19.08 | 30.35 | 42.58 |
| 2 | 94 | 32.21 | 19.33 | 33.10 | 44.20 |
| 3 | 112 | 32.64 | 19.21 | 34.56 | 44.14 |
| 4 | 122 | 33.51 | 19.36 | 36.16 | 45.01 |
| 5 | 134 | 32.58 | 18.63 | 35.35 | 43.76 |
| 6 | 180 | 33.60 | 18.45 | 36.76 | 45.58 |
| 7 | 194 | 33.51 | 19.49 | 36.41 | 44.62 |
| 8 | 244 | 33.63 | 18.31 | 37.36 | 45.23 |
| 9 | 246 | 34.19 | 19.22 | 37.59 | 45.76 |
| 10 | 248 | 34.03 | 19.37 | 37.26 | 45.45 |
| 11 | 256 | 35.05 | 19.91 | 39.03 | 46.20 |
| 12 | 284 | 35.21 | 20.53 | 38.93 | 46.18 |
| 13 | 332 | 35.21 | 20.71 | 38.28 | 46.65 |
| 14 | 338 | 34.84 | 20.85 | 37.82 | 45.85 |
| 15 | 374 | 35.80 | 19.66 | 40.74 | 47.01 |
| 16 | 434 | 35.92 | 20.66 | 39.88 | 47.21 |
| 17 | 458 | 36.05 | 19.94 | 40.86 | 47.35 |
| 18 | 506 | 36.08 | 20.85 | 40.25 | 47.13 |
| 19 | 574 | 35.99 | 20.41 | 40.59 | 46.96 |

> **Best score:** Config #18 (avg_budget=506, avg_score=36.08). Config #17 is a close second at lower budget (458).

### 1.2 H2O — Top Configs (Pareto Front)

| # | Avg Budget | Avg Score | narrativeqa | qasper | multifieldqa_en |
|---|---|---|---|---|---|
| 0 | 64 | 25.14 | 17.68 | 25.46 | 32.28 |
| 1 | 76 | 25.32 | 17.33 | 25.84 | 32.78 |
| 2 | 104 | 26.71 | 17.75 | 26.80 | 35.57 |
| 3 | 128 | 28.21 | 17.70 | 31.10 | 35.84 |
| 4 | 188 | 28.06 | 19.76 | 27.13 | 37.30 |
| 5 | 206 | 27.87 | 18.45 | 28.08 | 37.08 |
| 6 | 236 | 28.99 | 18.87 | 30.35 | 37.74 |
| 7 | 262 | 29.42 | 18.61 | 31.33 | 38.33 |
| 8 | 272 | 30.22 | 18.94 | 32.74 | 38.99 |
| 9 | 306 | 30.55 | 16.84 | 34.68 | 40.14 |
| 10 | 312 | 30.53 | 19.28 | 34.00 | 38.31 |
| 11 | 366 | 30.89 | 19.45 | 33.76 | 39.45 |
| 12 | 406 | 31.60 | 19.55 | 34.27 | 40.97 |
| 13 | 496 | 32.20 | 18.13 | 36.16 | 42.30 |
| 14 | 518 | 32.74 | 19.34 | 37.33 | 41.54 |

> **Best score:** Config #14 (avg_budget=518, avg_score=32.74). SnapKV outperforms H2O at every budget level.

### 1.3 AdaKV — ❌ Incomplete

NAS run did not produce top_configs. Only `nas_run.log` and `output.txt` are present.

---

## 2. Multi-Doc QA (hotpotqa, 2wikimqa, musique)

### 2.1 SnapKV — Top Configs (Pareto Front)

| # | Avg Budget | Avg Score | hotpotqa | 2wikimqa | musique |
|---|---|---|---|---|---|
| 0 | 64 | 33.89 | 44.32 | 35.34 | 22.00 |
| 1 | 66 | 34.05 | 44.88 | 35.09 | 22.17 |
| 2 | 74 | 34.23 | 45.57 | 35.48 | 21.63 |
| 3 | 84 | 34.23 | 45.02 | 35.58 | 22.08 |
| 4 | 100 | 34.42 | 45.45 | 35.00 | 22.81 |
| 5 | 130 | 34.87 | 46.44 | 36.12 | 22.05 |
| 6 | 152 | 35.32 | 46.10 | 37.26 | 22.61 |
| 7 | 202 | 35.07 | 46.07 | 36.57 | 22.56 |
| 8 | 274 | 36.14 | 46.72 | 38.49 | 23.21 |

> **Best score:** Config #8 (avg_budget=274, avg_score=36.14). Significant gains from 2wikimqa (35.34→38.49) and musique (22.00→23.21).

### 2.2 H2O — Top Configs (Pareto Front)

| # | Avg Budget | Avg Score | hotpotqa | 2wikimqa | musique |
|---|---|---|---|---|---|
| 0 | 64 | 30.60 | 42.31 | 28.82 | 20.67 |
| 1 | 90 | 30.93 | 43.23 | 29.31 | 20.26 |
| 2 | 104 | 31.81 | 43.32 | 32.74 | 19.38 |
| 3 | 110 | 31.91 | 42.99 | 33.15 | 19.58 |
| 4 | 222 | 32.32 | 44.72 | 32.90 | 19.35 |
| 5 | 264 | 32.21 | 44.11 | 32.75 | 19.76 |
| 6 | 364 | 33.59 | 45.98 | 34.76 | 20.02 |
| 7 | 448 | 34.02 | 45.88 | 35.03 | 21.16 |
| 8 | 460 | 33.69 | 45.70 | 34.80 | 20.57 |
| 9 | 516 | 33.99 | 45.79 | 35.94 | 20.24 |

> **Best score:** Config #7 (avg_budget=448, avg_score=34.02). SnapKV outperforms H2O at every budget level.

### 2.3 AdaKV — ❌ Incomplete

NAS run did not produce top_configs. Only `nas_run.log` and `output.txt` are present.

---

## 3. Code (lcc, repobench-p)

### 3.1 SnapKV — Top Configs (Pareto Front)

| # | Avg Budget | Avg Score | lcc | repobench-p |
|---|---|---|---|---|
| 0 | 64 | 51.74 | 53.36 | 50.12 |
| 1 | 104 | 53.47 | 54.99 | 51.94 |
| 2 | 160 | 54.93 | 55.98 | 53.88 |
| 3 | 174 | 53.80 | 55.81 | 51.79 |
| 4 | 206 | 55.29 | 57.10 | 53.47 |
| 5 | 218 | 55.91 | 57.37 | 54.45 |
| 6 | 240 | 55.95 | 57.89 | 54.00 |
| 7 | 298 | 57.20 | 59.78 | 54.62 |
| 8 | 302 | 57.92 | 59.33 | 56.51 |
| 9 | 430 | 58.26 | 59.74 | 56.78 |
| 10 | 458 | 57.53 | 59.68 | 55.38 |

> **Best score:** Config #9 (avg_budget=430, avg_score=58.26). Code tasks benefit most from higher budgets on specific layers.

### 3.2 H2O — Top Configs (Pareto Front)

| # | Avg Budget | Avg Score | lcc | repobench-p |
|---|---|---|---|---|
| 0 | 64 | 42.59 | 46.21 | 38.96 |
| 1 | 128 | 45.96 | 49.92 | 42.00 |
| 2 | 256 | 49.08 | 53.39 | 44.76 |
| 3 | 312 | 49.38 | 53.20 | 45.55 |
| 4 | 348 | 50.56 | 53.85 | 47.27 |
| 5 | 366 | 49.83 | 53.19 | 46.46 |
| 6 | 374 | 50.73 | 54.58 | 46.88 |
| 7 | 376 | 51.01 | 54.63 | 47.39 |
| 8 | 392 | 51.35 | 54.78 | 47.91 |
| 9 | 398 | 53.45 | 57.52 | 49.38 |
| 10 | 410 | 51.27 | 54.92 | 47.62 |
| 11 | 424 | 52.48 | 56.62 | 48.33 |
| 12 | 508 | 53.73 | 57.59 | 49.87 |
| 13 | 510 | 55.31 | 59.10 | 51.52 |
| 14 | 632 | 55.58 | 58.63 | 52.52 |
| 15 | 646 | 55.49 | 58.95 | 52.02 |
| 16 | 666 | 55.61 | 58.75 | 52.46 |
| 17 | 696 | 55.91 | 58.66 | 53.15 |
| 18 | 1024 | 56.93 | 59.62 | 54.23 |

> **Best score:** Config #18 (avg_budget=1024, avg_score=56.93). SnapKV significantly outperforms H2O on code tasks — SnapKV achieves 58.26 at avg_budget=430 vs H2O's 56.93 at avg_budget=1024.

### 3.3 AdaKV — ❌ Not Run

No AdaKV folder present for Code tasks.

---

## 4. Summarization (gov_report, qmsum, multi_news)

### 4.1 SnapKV — Top Configs (Pareto Front)

| # | Avg Budget | Avg Score | gov_report | qmsum | multi_news |
|---|---|---|---|---|---|
| 0 | 64 | 19.49 | 19.33 | 19.60 | 19.54 |
| 1 | 128 | 21.12 | 20.77 | 20.64 | 21.95 |
| 2 | 252 | 21.37 | 21.47 | 20.33 | 22.32 |
| 3 | 256 | 22.27 | 22.20 | 21.04 | 23.57 |
| 4 | 268 | 22.34 | 22.09 | 21.53 | 23.39 |
| 5 | 312 | 22.58 | 22.81 | 21.09 | 23.85 |
| 6 | 366 | 22.51 | 21.98 | 21.84 | 23.71 |
| 7 | 390 | 22.28 | 21.95 | 21.39 | 23.49 |
| 8 | 398 | 23.16 | 23.45 | 21.28 | 24.75 |
| 9 | 510 | 23.54 | 23.68 | 21.94 | 25.00 |
| 10 | 622 | 24.04 | 24.63 | 21.78 | 25.72 |
| 11 | 732 | 24.43 | 25.30 | 21.69 | 26.31 |

> **Best score:** Config #11 (avg_budget=732, avg_score=24.43). Summarization benefits from higher budgets, especially gov_report and multi_news.

### 4.2 H2O — ❌ Not Run

No H2O folder present for Summarization tasks.

### 4.3 AdaKV — ❌ Not Run

No AdaKV folder present for Summarization tasks.

---

## 5. Key Findings

### SnapKV vs H2O (where both completed)

| Task Category | SnapKV Best Score | SnapKV Best Budget | H2O Best Score | H2O Best Budget | SnapKV Advantage |
|---|---|---|---|---|---|
| Single-Doc QA | 36.08 | 506 | 32.74 | 518 | +3.34 |
| Multi-Doc QA | 36.14 | 274 | 34.02 | 448 | +2.12 |
| Code | 58.26 | 430 | 56.93 | 1024 | +1.33 |

> SnapKV consistently outperforms H2O across all task categories, achieving higher scores at lower average budgets. The advantage is largest on Single-Doc QA (+3.34) and smallest on Code (+1.33).

### Budget Allocation Insights

- **Most layers prefer budget 64** — the NAS consistently assigns budget 64 to the majority of layers, allocating higher budgets only to specific critical layers
- **Layer 15 (0-indexed)** frequently receives high budgets (512 or 1024) across task categories — this appears to be a critical layer
- **Layer 11** also frequently receives elevated budgets, especially for QA tasks
- **Code tasks** benefit from higher budgets on layers 8, 14, 15, 20, and 28
- **Summarization tasks** benefit from higher budgets on layers 2, 8, 10, 14, 15, and 17

---

## 6. Directory Structure

```
NAS_Assets/
├── SINGLE_DOCUMENT_QA/
│   ├── snapkv/
│   │   ├── nas_run.log
│   │   ├── output.txt
│   │   ├── run_files/          (172 run plots)
│   │   └── top_configs/
│   │       ├── summary_20260722_143105.csv
│   │       ├── summary_20260722_143105.json
│   │       ├── objective_values.csv
│   │       └── all_archs_window_lengths_heatmap.png
│   ├── h2o/
│   │   ├── nas_run.log
│   │   ├── output.txt
│   │   ├── run_files/          (101 run plots)
│   │   └── top_configs/
│   │       ├── summary_20260724_194533.csv
│   │       └── summary_20260724_194533.json
│   └── adakv/                  ❌ No top_configs (incomplete)
│       ├── nas_run.log
│       ├── output.txt
│       └── run_files/
├── MULTI_DOCUMENT_QA/
│   ├── snapkv/
│   │   ├── nas_run.log
│   │   ├── output.txt
│   │   ├── run_files/          (159 run plots)
│   │   └── top_configs/
│   │       ├── summary_20260722_145551.csv
│   │       └── summary_20260722_145551.json
│   ├── h2o/
│   │   ├── nas_run.log
│   │   ├── output.txt
│   │   ├── run_files/          (117 run plots)
│   │   └── top_configs/
│   │       ├── summary_20260724_210051.csv
│   │       └── summary_20260724_210051.json
│   └── adakv/                  ❌ No top_configs (incomplete)
│       ├── nas_run.log
│       ├── output.txt
│       └── run_files/
├── CODE/
│   ├── snapkv/
│   │   ├── nas_run.log
│   │   ├── output.txt
│   │   ├── run_files/          (52 run plots)
│   │   └── top_configs/
│   │       ├── summary_20260722_212658.csv
│   │       └── summary_20260722_212658.json
│   └── h2o/
│       ├── nas_run.log
│       ├── output.txt
│       ├── run_files/          (32 run plots)
│       └── top_configs/
│           ├── summary_20260725_083026.csv
│           └── summary_20260725_083026.json
├── SUMMARIZATION/
│   └── snapkv/
│       ├── nas_run.log
│       ├── output.txt
│       ├── top_configs_22_07_2026.log
│       ├── run_files/          (47 run plots)
│       └── top_configs/
│           ├── summary_20260725_012202.csv
│           ├── summary_20260725_012202.json
│           ├── objective_values.csv
│           └── all_archs_window_lengths_heatmap.png
├── run_nas.sh
└── README.md                   ← this file
```

---

*Generated from top_configs summary CSV/JSON files in the NAS_Assets directory. Each config represents a Pareto-optimal per-layer budget allocation found by the NAS search.*
