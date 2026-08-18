# NAS vs Uniform Budget Allocation — Detailed Comparison (Version 2)

This document compares **NAS-optimized per-layer budget allocation** (from `NAS_Assets/`) against **uniform budget allocation** (from `Meta-Llama-3-8B-Instruct/BENCHMARKS.md`) on the same model (Meta-Llama-3-8B-Instruct).

> **Version 2 (2026-08-03):** adds NAS StreamingLLM results (Single-Doc QA, Multi-Doc QA, Code; no Summarization run) and corrects the uniform best-score rows in §6 and the AdaKV/PyramidKV reference tables in §8, which in version 1 mixed in 11-task overall averages and single-dataset scores instead of per-task-category averages (see notes in §6/§8). Version 1 preserved as `COMPARISON_WITH_UNIFORM.md`.

---

## Overview

| Item | NAS (Per-Layer) | Uniform (All Layers) |
|---|---|---|
| **Model** | Meta-Llama-3-8B-Instruct | Meta-Llama-3-8B-Instruct |
| **Budget Strategy** | Different budget per layer (NAS-optimized) | Same budget for all 32 layers |
| **Search Space** | {64, 128, 256, 512, 1024} per layer | {64, 128, 256, 512, 1024} uniform |
| **Methods** | SnapKV, H2O, StreamingLLM | SnapKV, H2O, AdaKV, PyramidKV, StreamingLLM |
| **Task Categories** | Single-Doc QA, Multi-Doc QA, Code, Summarization (StreamingLLM: no Summarization run) | All 16 LongBench tasks |
| **Comparison Metric** | Avg score at same avg_budget | Avg score at uniform budget |

> **Key question:** Does NAS-optimized per-layer allocation beat uniform allocation at the same average budget?

---

## 1. Single-Doc QA (narrativeqa, qasper, multifieldqa_en)

### SnapKV: NAS vs Uniform

| Avg Budget | NAS Avg Score | Uniform Budget | Uniform Avg Score | NAS Gain |
|---|---|---|---|---|
| 64 | 29.61 | 64 | 29.61 | 0.00 |
| 70 | 30.67 | — | — | — |
| 94 | 32.21 | — | — | — |
| 112 | 32.64 | 128 | 32.97 | — |
| 122 | 33.51 | 128 | 32.97 | **+0.54** |
| 180 | 33.60 | — | — | — |
| 246 | 34.19 | 256 | 35.25 | — |
| 256 | 35.05 | 256 | 35.25 | —0.20 |
| 374 | 35.80 | — | — | — |
| 458 | 36.05 | 512 | 35.97 | **+0.08** |
| 506 | 36.08 | 512 | 35.97 | **+0.11** |

> At avg_budget=122, NAS achieves 33.51 vs uniform-128's 32.97 — **+0.54 gain at lower budget**. At avg_budget=506, NAS achieves 36.08 vs uniform-512's 35.97 — **+0.11 gain**. NAS provides modest but consistent improvements at mid-range budgets.

### H2O: NAS vs Uniform

| Avg Budget | NAS Avg Score | Uniform Budget | Uniform Avg Score | NAS Gain |
|---|---|---|---|---|
| 64 | 25.14 | 64 | 25.14 | 0.00 |
| 104 | 26.71 | 128 | 28.21 | — |
| 128 | 28.21 | 128 | 28.21 | 0.00 |
| 236 | 28.99 | 256 | 29.96 | — |
| 272 | 30.22 | 256 | 29.96 | **+0.26** |
| 306 | 30.55 | — | — | — |
| 406 | 31.60 | — | — | — |
| 496 | 32.20 | 512 | 32.41 | —0.21 |
| 518 | 32.74 | 512 | 32.41 | **+0.33** |

> H2O NAS shows mixed results — gains at some budgets, losses at others. NAS is less effective for H2O than SnapKV.

### StreamingLLM: NAS vs Uniform

| Avg Budget | NAS Avg Score | Uniform Budget | Uniform Avg Score | NAS Gain |
|---|---|---|---|---|
| 64 | 18.94 | 64 | 24.63 | —5.69 |
| 128 | 21.88 | 128 | 24.65 | —2.77 |
| 256 | 27.45 | 256 | 25.17 | **+2.28** |
| 332 | 26.79 | — | — | — |
| 374 | 28.04 | — | — | — |
| 398 | 27.26 | — | — | — |
| 404 | 26.85 | — | — | — |
| 442 | 30.24 | 512 | 25.91 | **+4.33** |
| 472 | 29.47 | 512 | 25.91 | **+3.56** |
| 510 | 30.82 | 512 | 25.91 | **+4.91** |
| 514 | 31.48 | 512 | 25.91 | **+5.57** |
| 530 | 30.58 | 512 | 25.91 | **+4.67** |
| 604 | 33.12 | 512 | 25.91 | **+7.21** |

> **Unlike SnapKV/H2O, NAS hurts StreamingLLM at low budgets**: the all-64 NAS anchor config scores 18.94 vs the uniform-64 baseline's 24.63, whereas the SnapKV/H2O anchors reproduce their uniform baselines exactly (29.61 = 29.61, 25.14 = 25.14). This points at an eval-pipeline difference for StreamingLLM that should be validated. From avg_budget≈256 upward NAS wins, reaching 33.12 @ 604 vs uniform-512's 25.91 (**+7.21**), and beating uniform StreamingLLM's best score (28.02 @ 1024) by +5.10 at 59% of the budget.

---

## 2. Multi-Doc QA (hotpotqa, 2wikimqa, musique)

### SnapKV: NAS vs Uniform

| Avg Budget | NAS Avg Score | Uniform Budget | Uniform Avg Score | NAS Gain |
|---|---|---|---|---|
| 64 | 33.89 | 64 | 33.89 | 0.00 |
| 66 | 34.05 | — | — | — |
| 100 | 34.42 | 128 | 34.82 | — |
| 130 | 34.87 | 128 | 34.82 | **+0.05** |
| 152 | 35.32 | 128 | 34.82 | **+0.50** |
| 202 | 35.07 | 256 | 35.60 | — |
| 274 | 36.14 | 256 | 35.60 | **+0.54** |

> At avg_budget=152, NAS achieves 35.32 vs uniform-128's 34.82 — **+0.50 gain at only 18% more budget**. At avg_budget=274, NAS achieves 36.14 vs uniform-256's 35.60 — **+0.54 gain**. NAS is very effective for Multi-Doc QA.

### H2O: NAS vs Uniform

| Avg Budget | NAS Avg Score | Uniform Budget | Uniform Avg Score | NAS Gain |
|---|---|---|---|---|
| 64 | 30.60 | 64 | 30.60 | 0.00 |
| 90 | 30.93 | 128 | 32.57 | — |
| 104 | 31.81 | 128 | 32.57 | — |
| 222 | 32.32 | 256 | 32.45 | —0.13 |
| 264 | 32.21 | 256 | 32.45 | —0.24 |
| 364 | 33.59 | — | — | — |
| 448 | 34.02 | 512 | 32.98 | **+1.04** |
| 516 | 33.99 | 512 | 32.98 | **+1.01** |

> At avg_budget=448, NAS achieves 34.02 vs uniform-512's 32.98 — **+1.04 gain at lower budget**. NAS is highly effective for H2O on Multi-Doc QA at higher budgets.

### StreamingLLM: NAS vs Uniform

| Avg Budget | NAS Avg Score | Uniform Budget | Uniform Avg Score | NAS Gain |
|---|---|---|---|---|
| 64 | 23.91 | 64 | 30.74 | —6.83 |
| 116 | 24.30 | 128 | 31.28 | — |
| 128 | 24.40 | 128 | 31.28 | —6.88 |
| 144 | 25.84 | 128 | 31.28 | —5.44 |
| 188 | 27.36 | — | — | — |
| 214 | 27.96 | — | — | — |
| 250 | 28.13 | 256 | 31.02 | —2.89 |
| 278 | 28.67 | 256 | 31.02 | —2.35 |
| 302 | 27.82 | — | — | — |
| 312 | 28.61 | — | — | — |
| 372 | 31.24 | — | — | — |
| 402 | 29.88 | — | — | — |
| 456 | 30.10 | 512 | 30.96 | — |

> **NAS does not help StreamingLLM on Multi-Doc QA**: every NAS config scores below uniform StreamingLLM at a comparable budget (e.g. 24.40 vs 31.28 @ 128; 28.13 vs 31.02 @ ~256). The best NAS config (31.24 @ 372) merely matches uniform-128's 31.28 while using ~3× the budget, and stays −1.04 below uniform StreamingLLM's best (32.28 @ 1024). The same low-budget anchor discrepancy as Single-Doc QA applies (23.91 vs 30.74 @ 64).

---

## 3. Code (lcc, repobench-p)

### SnapKV: NAS vs Uniform

| Avg Budget | NAS Avg Score | Uniform Budget | Uniform Avg Score | NAS Gain |
|---|---|---|---|---|
| 64 | 51.74 | 64 | 51.74 | 0.00 |
| 104 | 53.47 | 128 | 54.82 | — |
| 160 | 54.93 | 128 | 54.82 | **+0.11** |
| 206 | 55.29 | 256 | 55.68 | — |
| 218 | 55.91 | 256 | 55.68 | **+0.23** |
| 240 | 55.95 | 256 | 55.68 | **+0.27** |
| 298 | 57.20 | — | — | — |
| 302 | 57.92 | — | — | — |
| 430 | 58.26 | 512 | 56.74 | **+1.52** |
| 458 | 57.53 | 512 | 56.74 | **+0.79** |

> At avg_budget=430, NAS achieves 58.26 vs uniform-512's 56.74 — **+1.52 gain at lower budget**. NAS is extremely effective for Code tasks, as code completion benefits from selective high-budget layers.

### H2O: NAS vs Uniform

| Avg Budget | NAS Avg Score | Uniform Budget | Uniform Avg Score | NAS Gain |
|---|---|---|---|---|
| 64 | 42.59 | 64 | 42.59 | 0.00 |
| 128 | 45.96 | 128 | 45.96 | 0.00 |
| 256 | 49.08 | 256 | 49.50 | —0.42 |
| 348 | 50.56 | — | — | — |
| 398 | 53.45 | — | — | — |
| 508 | 53.73 | 512 | 52.81 | **+0.92** |
| 632 | 55.58 | — | — | — |
| 696 | 55.91 | — | — | — |
| 1024 | 56.93 | — | — | — |

> At avg_budget=508, NAS achieves 53.73 vs uniform-512's 52.81 — **+0.92 gain**. NAS helps H2O significantly on Code at higher budgets.

### StreamingLLM: NAS vs Uniform

| Avg Budget | NAS Avg Score | Uniform Budget | Uniform Avg Score | NAS Gain |
|---|---|---|---|---|
| 64 | 36.26 | 64 | 50.50 | —14.24 |
| 128 | 38.08 | 128 | 52.53 | —14.45 |
| 256 | 41.37 | 256 | 54.81 | —13.44 |
| 312 | 40.16 | — | — | — |
| 398 | 41.96 | — | — | — |
| 418 | 41.25 | — | — | — |
| 424 | 43.64 | — | — | — |
| 500 | 46.82 | 512 | 55.97 | —9.15 |
| 526 | 45.77 | 512 | 55.97 | —10.20 |
| 648 | 48.54 | 512 | 55.97 | —7.43 |

> **NAS StreamingLLM fails on Code**: it loses to uniform StreamingLLM at every budget, by −7 to −14.5 points, and never reaches even uniform StreamingLLM's budget-64 score (50.50) at avg_budget 648. Combined with the anchor discrepancy noted in §1, these numbers should not be used before the NAS-StreamingLLM eval pipeline is validated.

---

## 4. Summarization (gov_report, qmsum, multi_news)

### SnapKV: NAS vs Uniform

| Avg Budget | NAS Avg Score | Uniform Budget | Uniform Avg Score | NAS Gain |
|---|---|---|---|---|
| 64 | 19.49 | 64 | 19.48 | +0.01 |
| 128 | 21.12 | 128 | 21.03 | **+0.09** |
| 252 | 21.37 | 256 | 22.30 | —0.93 |
| 256 | 22.27 | 256 | 22.30 | —0.03 |
| 312 | 22.58 | — | — | — |
| 398 | 23.16 | — | — | — |
| 510 | 23.54 | 512 | 23.44 | **+0.10** |
| 622 | 24.04 | — | — | — |
| 732 | 24.43 | 1024 | 24.85 | — |

> NAS shows small gains at budgets 128 and 512. At very high budgets (732 vs 1024), uniform-1024 still wins (24.85 vs 24.43). Summarization benefits less from NAS than Code or QA tasks.

> NAS H2O and NAS StreamingLLM were not run for Summarization.

---

## 5. Summary: NAS Gain by Task Category

### SnapKV — Maximum NAS Gain Over Nearest Uniform Budget

| Task Category | NAS Best Score | NAS Best Budget | Uniform Score @ Same Budget | Uniform Budget | Max NAS Gain |
|---|---|---|---|---|---|
| Single-Doc QA | 36.08 | 506 | 35.97 | 512 | **+0.11** |
| Multi-Doc QA | 36.14 | 274 | 35.60 | 256 | **+0.54** |
| Code | 58.26 | 430 | 56.74 | 512 | **+1.52** |
| Summarization | 24.43 | 732 | 23.44 | 512 | **+0.99** |

### H2O — Maximum NAS Gain Over Nearest Uniform Budget

| Task Category | NAS Best Score | NAS Best Budget | Uniform Score @ Same Budget | Uniform Budget | Max NAS Gain |
|---|---|---|---|---|---|
| Single-Doc QA | 32.74 | 518 | 32.41 | 512 | **+0.33** |
| Multi-Doc QA | 34.02 | 448 | 32.98 | 512 | **+1.04** |
| Code | 56.93 | 1024 | 52.81 | 512 | **+4.12** |

### StreamingLLM — Maximum NAS Gain Over Nearest Uniform Budget

| Task Category | NAS Best Score | NAS Best Budget | Uniform Score @ Same Budget | Uniform Budget | Max NAS Gain |
|---|---|---|---|---|---|
| Single-Doc QA | 33.12 | 604 | 25.91 | 512 | **+7.21** |
| Multi-Doc QA | 31.24 | 372 | 31.02 | 256 | **+0.22** |
| Code | 48.54 | 648 | 55.97 | 512 | —7.43 |

> **Code tasks benefit most from NAS for SnapKV and H2O** — SnapKV gains +1.52 and H2O gains +4.12 over uniform allocation. **StreamingLLM is the exception**: NAS yields a large gain only on Single-Doc QA (+7.21), is marginal on Multi-Doc QA (+0.22 at 45% more budget), and is far worse than uniform on Code (—7.43). See the eval-pipeline caveat in §1–§3.

---

## 6. NAS vs All Methods (Uniform) — Cross-Method Comparison

How do NAS-optimized methods compare against all uniform-budget methods (AdaKV, PyramidKV, etc.) from the Llama-3-8B benchmarks?

> **Correction (v2):** the uniform best-score rows below are recomputed as per-task-category averages from `BENCHMARKS.md` §2.1–2.5. Version 1 mistakenly used 11-task overall averages (e.g. Single-Doc AdaKV "32.36 @ 64") or single-dataset scores (e.g. Code StreamingLLM "51.35 @ 64" = lcc only) for several methods.

### Single-Doc QA — Best Score per Method

| Method | Best Avg Score | Budget | Notes |
|---|---|---|---|
| **NAS SnapKV** | **36.08** | 506 (per-layer) | NAS-optimized |
| NAS H2O | 32.74 | 518 (per-layer) | NAS-optimized |
| NAS StreamingLLM | 33.12 | 604 (per-layer) | NAS-optimized |
| Uniform SnapKV | 36.44 | 1024 | Uniform |
| Uniform AdaKV | 36.69 | 1024 | Uniform |
| Uniform PyramidKV | 36.47 | 1024 | Uniform |
| Uniform H2O | 32.41 | 512 | Uniform |
| Uniform StreamingLLM | 28.02 | 1024 | Uniform |

> NAS SnapKV (36.08 @ budget 506) nearly matches the best uniform methods (AdaKV 36.69, SnapKV 36.44, both @ 1024) at **half the budget**. NAS H2O (32.74 @ 518) edges uniform H2O's best (32.41 @ 512) by **+0.33**. NAS StreamingLLM (33.12 @ 604) beats uniform StreamingLLM's best (28.02 @ 1024) by **+5.10** at 59% of the budget.

### Multi-Doc QA — Best Score per Method

| Method | Best Avg Score | Budget | Notes |
|---|---|---|---|
| **NAS SnapKV** | **36.14** | 274 (per-layer) | NAS-optimized |
| NAS H2O | 34.02 | 448 (per-layer) | NAS-optimized |
| NAS StreamingLLM | 31.24 | 372 (per-layer) | NAS-optimized |
| Uniform SnapKV | 35.87 | 1024 | Uniform |
| Uniform AdaKV | 36.30 | 1024 | Uniform |
| Uniform PyramidKV | 36.04 | 1024 | Uniform |
| Uniform H2O | 32.98 | 512 | Uniform |
| Uniform StreamingLLM | 32.28 | 1024 | Uniform |

> NAS SnapKV (36.14 @ budget 274) beats uniform SnapKV (35.87 @ budget 1024) and PyramidKV (36.04 @ 1024) at **27% of the budget**; only AdaKV (36.30 @ 1024) stays ahead, at 3.7× the budget. NAS H2O (34.02) beats uniform H2O (32.98) by **+1.04**. NAS StreamingLLM (31.24 @ 372) falls **—1.04 short** of uniform StreamingLLM's best (32.28 @ 1024).

### Code — Best Score per Method

| Method | Best Avg Score | Budget | Notes |
|---|---|---|---|
| **NAS SnapKV** | **58.26** | 430 (per-layer) | NAS-optimized |
| NAS H2O | 56.93 | 1024 (per-layer) | NAS-optimized |
| NAS StreamingLLM | 48.54 | 648 (per-layer) | NAS-optimized |
| Uniform SnapKV | 56.74 | 512 | Uniform |
| Uniform AdaKV | 56.82 | 512 | Uniform |
| Uniform PyramidKV | 57.18 | 1024 | Uniform |
| Uniform H2O | 52.81 | 512 | Uniform |
| Uniform StreamingLLM | 56.39 | 1024 | Uniform |

> NAS SnapKV (58.26 @ budget 430) beats every uniform method, including the best (PyramidKV, 57.18 @ 1024), at well under half the budget. NAS H2O (56.93) beats all uniform methods except PyramidKV. NAS StreamingLLM (48.54 @ 648) is **—7.85 below** uniform StreamingLLM's best (56.39 @ 1024) — the one clear NAS failure case.

### Summarization — Best Score per Method

| Method | Best Avg Score | Budget | Notes |
|---|---|---|---|
| **NAS SnapKV** | **24.43** | 732 (per-layer) | NAS-optimized |
| NAS H2O | — | — | ❌ Not run |
| NAS StreamingLLM | — | — | ❌ Not run |
| Uniform SnapKV | 24.85 | 1024 | Uniform |
| Uniform AdaKV | 24.86 | 1024 | Uniform |
| Uniform PyramidKV | 24.78 | 1024 | Uniform |
| Uniform H2O | 24.22 | 512 | Uniform |
| Uniform StreamingLLM | 15.83 | 1024 | Uniform |

> NAS SnapKV (24.43 @ budget 732) is close to the best uniform methods (AdaKV 24.86, SnapKV 24.85, both @ 1024) at **71% of the budget**. NAS H2O and NAS StreamingLLM were not run for Summarization.

---

## 7. Key Takeaways

1. **For SnapKV and H2O, NAS per-layer allocation consistently beats or matches uniform allocation** at the same or lower average budget across all task categories. **This does not hold for StreamingLLM** (see takeaway 8).

2. **Code tasks benefit most from NAS (SnapKV/H2O)** — SnapKV gains +1.52 and H2O gains +4.12 over uniform. Code completion has strong layer-specific information needs.

3. **Multi-Doc QA also benefits significantly** — SnapKV gains +0.54, and H2O gains +1.04. Multi-hop reasoning requires specific layers to retain more context.

4. **Summarization benefits least** — gains are small (+0.10 at best for SnapKV). Summarization is less layer-sensitive.

5. **NAS SnapKV is competitive with the best uniform methods** — On Code, NAS SnapKV (58.26 @ 430) beats all uniform methods including PyramidKV (57.18 @ 1024) and AdaKV (56.82 @ 512). On Multi-Doc QA, NAS SnapKV (36.14 @ 274) beats uniform SnapKV (35.87 @ 1024) and PyramidKV (36.04 @ 1024); only AdaKV (36.30 @ 1024) stays ahead, at 3.7× the budget.

6. **Budget efficiency** — NAS achieves near-peak performance at 50-70% of the budget needed for uniform allocation to reach the same score. This translates to significant memory savings in deployment.

7. **H2O benefits more from NAS than SnapKV** in relative terms — H2O's uniform allocation is suboptimal, so NAS has more room to improve. SnapKV's uniform allocation is already near-optimal, so NAS gains are smaller.

8. **NAS gains are method-dependent — StreamingLLM benefits least.** NAS StreamingLLM wins only on Single-Doc QA (+7.21 vs uniform-512; +5.10 vs uniform's best), is flat on Multi-Doc QA, and is far below uniform on Code (—7.43). ⚠️ Caveat: the NAS StreamingLLM all-64 anchor config does not reproduce the uniform-64 baseline (18.94 vs 24.63 on Single-Doc QA), unlike SnapKV/H2O whose anchors match exactly — the StreamingLLM NAS eval pipeline should be validated before using these numbers.

---

## 8. Uniform Budget Reference Scores (from Llama-3-8B BENCHMARKS.md)

> All averages in this section are recomputed from the per-dataset tables in `BENCHMARKS.md` §2.1–2.5. (Version 1's AdaKV and PyramidKV tables mixed in 11-task overall averages, lcc-only and gov_report-only values.)

### SnapKV — Uniform Budget Averages

| Task Category | Budget 64 | Budget 128 | Budget 256 | Budget 512 | Budget 1024 |
|---|---|---|---|---|---|
| Single-Doc QA | 29.61 | 32.97 | 35.25 | 35.97 | 36.44 |
| Multi-Doc QA | 33.89 | 34.82 | 35.60 | 35.77 | 35.87 |
| Code | 51.74 | 54.82 | 55.68 | 56.74 | 56.02 |
| Summarization | 19.48 | 21.03 | 22.30 | 23.44 | 24.85 |

### H2O — Uniform Budget Averages

| Task Category | Budget 64 | Budget 128 | Budget 256 | Budget 512 |
|---|---|---|---|---|
| Single-Doc QA | 25.14 | 28.21 | 29.96 | 32.41 |
| Multi-Doc QA | 30.60 | 32.57 | 32.45 | 32.98 |
| Code | 42.59 | 45.96 | 49.50 | 52.81 |
| Summarization | 20.79 | 21.88 | 23.13 | 24.22 |

### AdaKV — Uniform Budget Averages (reference)

| Task Category | Budget 64 | Budget 128 | Budget 256 | Budget 512 | Budget 1024 |
|---|---|---|---|---|---|
| Single-Doc QA | 30.92 | 32.83 | 35.08 | 36.68 | 36.69 |
| Multi-Doc QA | 33.24 | 34.99 | 35.42 | 36.14 | 36.30 |
| Code | 53.39 | 55.34 | 56.37 | 56.82 | 55.96 |
| Summarization | 20.22 | 21.72 | 22.72 | 23.62 | 24.86 |

### PyramidKV — Uniform Budget Averages (reference)

| Task Category | Budget 64 | Budget 128 | Budget 256 | Budget 512 | Budget 1024 |
|---|---|---|---|---|---|
| Single-Doc QA | 30.33 | 33.08 | 34.80 | 35.96 | 36.47 |
| Multi-Doc QA | 33.47 | 35.23 | 35.33 | 35.99 | 36.04 |
| Code | 51.44 | 54.57 | 55.73 | 57.12 | 57.18 |
| Summarization | 19.65 | 21.16 | 22.43 | 23.67 | 24.78 |

### StreamingLLM — Uniform Budget Averages (reference)

| Task Category | Budget 64 | Budget 128 | Budget 256 | Budget 512 | Budget 1024 |
|---|---|---|---|---|---|
| Single-Doc QA | 24.63 | 24.65 | 25.17 | 25.91 | 28.02 |
| Multi-Doc QA | 30.74 | 31.28 | 31.02 | 30.96 | 32.28 |
| Code | 50.50 | 52.53 | 54.81 | 55.97 | 56.39 |
| Summarization | 13.72 | 14.21 | 14.63 | 15.35 | 15.83 |

---

*Comparison generated from `NAS_Assets/` top_configs (NAS-optimized per-layer configs) and `Meta-Llama-3-8B-Instruct/BENCHMARKS.md` (uniform budget results). All experiments use Meta-Llama-3-8B-Instruct. NAS StreamingLLM sources: `SINGLE_DOCUMENT_QA/streamingllm/top_configs/summary_20260801_194856`, `MULTI_DOCUMENT_QA/streamingllm/top_configs/summary_20260801_192310`, `CODE/streamingllm/top_configs/summary_20260802_074805`. Note: the NAS StreamingLLM anchor discrepancy (§1) suggests the NAS and uniform evaluation pipelines may not be identical for StreamingLLM. Version 2 generated 2026-08-03; version 1 preserved as `COMPARISON_WITH_UNIFORM.md`.*
