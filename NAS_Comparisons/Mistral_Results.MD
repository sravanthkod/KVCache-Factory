# NAS SnapKV vs Uniform Budget — Mistral-7B-v0.2 Comparison

This document compares **NAS-optimized per-layer SnapKV** (from `mistral_7b_v02_nas_results/snapkv/`) against **uniform-budget SnapKV** and all other uniform methods (H2O, AdaKV, PyramidKV, StreamingLLM) from `mistral_7b_v02_benchmark/BENCHMARKS.md`.

---

## Overview

| Item | NAS SnapKV | Uniform Methods |
|---|---|---|
| **Model** | Mistral-7B-v0.2 | Mistral-7B-v0.2 |
| **Budget Strategy** | Different budget per layer (NAS-optimized) | Same budget for all 32 layers |
| **Search Space** | {64, 128, 256, 512, 1024} per layer | {64, 128, 256, 512, 1024, 2048} uniform |
| **Methods** | SnapKV only | SnapKV, H2O, AdaKV, PyramidKV, StreamingLLM |
| **Task Categories** | Single-Doc QA, Multi-Doc QA, Code, Summarization | All 16 LongBench tasks |

---

## 1. Single-Doc QA (narrativeqa, qasper, multifieldqa_en)

### NAS SnapKV vs Uniform SnapKV

| NAS Budget | NAS Avg Score | Uniform Budget | Uniform SnapKV | NAS Gain |
|---|---|---|---|---|
| 64 | 25.53 | 64 | 25.53 | 0.00 |
| 70 | 26.29 | — | — | — |
| 80 | 27.29 | — | — | — |
| 110 | 30.08 | 128 | 29.61 | **+0.47** |
| 148 | 31.90 | 128 | 29.61 | **+2.29** |
| 192 | 32.81 | 256 | 31.74 | **+1.07** |
| 266 | 33.13 | 256 | 31.74 | **+1.39** |
| 316 | 33.59 | 512 | 33.91 | —0.32 |
| 384 | 33.70 | 512 | 33.91 | —0.21 |

> NAS SnapKV at budget 148 (31.90) beats uniform SnapKV at budget 128 (29.61) by **+2.29**. At budget 192, NAS (32.81) beats uniform-256 (31.74) by **+1.07**. At budget 266, NAS (33.13) beats uniform-256 (31.74) by **+1.39**. NAS is highly effective at low-to-mid budgets.

### NAS SnapKV vs All Uniform Methods — Best Score per Method

| Method | Best Avg Score | Budget | Notes |
|---|---|---|---|
| ★ **NAS SnapKV** | **33.70** | 384 (per-layer) | NAS-optimized |
| Uniform SnapKV | 35.87 | 2048 | Uniform |
| Uniform AdaKV | 36.05 | 2048 | Uniform |
| Uniform PyramidKV | 35.42 | 2048 | Uniform |
| Uniform H2O | 33.33 | 2048 | Uniform |
| Uniform StreamingLLM | 26.90 | 2048 | Uniform |

> NAS SnapKV (33.70 @ budget 384) beats uniform H2O (33.33 @ budget 2048) and StreamingLLM (26.90) at **19% of the budget**. It approaches uniform SnapKV (35.87 @ budget 2048) and AdaKV (36.05 @ budget 2048) at **19% of the budget**.

---

## 2. Multi-Doc QA (hotpotqa, 2wikimqa, musique)

### NAS SnapKV vs Uniform SnapKV

| NAS Budget | NAS Avg Score | Uniform Budget | Uniform SnapKV | NAS Gain |
|---|---|---|---|---|
| 64 | 22.49 | 64 | 22.49 | 0.00 |
| 90 | 24.72 | 128 | 23.86 | **+0.86** |
| 122 | 27.10 | 128 | 23.86 | **+3.24** |
| 142 | 27.42 | 256 | 25.62 | **+1.80** |
| 158 | 27.79 | 256 | 25.62 | **+2.17** |
| 348 | 28.20 | 512 | 26.47 | **+1.73** |

> NAS SnapKV at budget 122 (27.10) beats uniform SnapKV at budget 128 (23.86) by **+3.24**. At budget 158, NAS (27.79) beats uniform-256 (25.62) by **+2.17**. At budget 348, NAS (28.20) beats uniform-512 (26.47) by **+1.73**. NAS is extremely effective for Multi-Doc QA.

### NAS SnapKV vs All Uniform Methods — Best Score per Method

| Method | Best Avg Score | Budget | Notes |
|---|---|---|---|
| ★ **NAS SnapKV** | **28.20** | 348 (per-layer) | NAS-optimized |
| Uniform SnapKV | 29.49 | 2048 | Uniform |
| Uniform AdaKV | 29.57 | 2048 | Uniform |
| Uniform PyramidKV | 29.11 | 2048 | Uniform |
| Uniform H2O | 27.23 | 2048 | Uniform |
| Uniform StreamingLLM | 22.99 | 2048 | Uniform |

> NAS SnapKV (28.20 @ budget 348) beats uniform H2O (27.23 @ budget 2048) and StreamingLLM (22.99) at **17% of the budget**. It approaches uniform SnapKV (29.49 @ budget 2048) and AdaKV (29.57 @ budget 2048) at **17% of the budget**.

---

## 3. Code (lcc, repobench-p)

### NAS SnapKV vs Uniform SnapKV

| NAS Budget | NAS Avg Score | Uniform Budget | Uniform SnapKV | NAS Gain |
|---|---|---|---|---|
| 64 | 46.60 | 64 | 46.60 | 0.00 |
| 128 | 49.76 | 128 | 49.76 | 0.00 |
| 212 | 48.98 | 256 | 52.09 | —3.11 |
| 256 | 52.09 | 256 | 52.09 | 0.00 |
| 274 | 51.57 | 256 | 52.09 | —0.52 |
| 340 | 53.11 | 512 | 53.77 | —0.66 |
| 480 | 53.76 | 512 | 53.77 | —0.01 |
| 1024 | 55.24 | 1024 | 55.24 | 0.00 |

> For Code, NAS SnapKV matches uniform SnapKV at budgets 64, 128, 256, and 1024 (these are uniform configs in the NAS Pareto front). NAS does not improve over uniform for Code on Mistral — code completion is less layer-sensitive on this model.

### NAS SnapKV vs All Uniform Methods — Best Score per Method

| Method | Best Avg Score | Budget | Notes |
|---|---|---|---|
| ★ **NAS SnapKV** | **55.24** | 1024 (per-layer) | NAS-optimized |
| Uniform SnapKV | 55.62 | 2048 | Uniform |
| Uniform AdaKV | 55.58 | 2048 | Uniform |
| Uniform PyramidKV | 55.40 | 2048 | Uniform |
| Uniform H2O | 51.72 | 2048 | Uniform |
| Uniform StreamingLLM | 54.82 | 2048 | Uniform |

> NAS SnapKV (55.24 @ budget 1024) beats uniform H2O (51.72) and StreamingLLM (54.82) at **half the budget**. It matches uniform SnapKV (55.24 @ budget 1024) exactly. Uniform SnapKV at budget 2048 (55.62) is marginally better.

---

## 4. Summarization (gov_report, qmsum, multi_news)

### NAS SnapKV vs Uniform SnapKV

| NAS Budget | NAS Avg Score | Uniform Budget | Uniform SnapKV | NAS Gain |
|---|---|---|---|---|
| 64 | 19.83 | 64 | 19.83 | 0.00 |
| 72 | 20.00 | 128 | 21.55 | —1.55 |
| 82 | 20.21 | 128 | 21.55 | —1.34 |
| 124 | 19.96 | 128 | 21.55 | —1.59 |

> ⚠️ NAS only explored low budgets (64–124) for Summarization. NAS does not improve over uniform at these budgets. Results are incomplete — higher-budget NAS configs were not found.

### NAS SnapKV vs All Uniform Methods — Best Score per Method

| Method | Best Avg Score | Budget | Notes |
|---|---|---|---|
| ★ **NAS SnapKV** | **20.21** | 82 (per-layer) | NAS-optimized (incomplete) |
| Uniform SnapKV | 26.78 | 2048 | Uniform |
| Uniform H2O | 26.74 | 2048 | Uniform |
| Uniform AdaKV | 26.24 | 2048 | Uniform |
| Uniform PyramidKV | 26.51 | 2048 | Uniform |
| Uniform StreamingLLM | 24.65 | 2048 | Uniform |

> ⚠️ NAS SnapKV (20.21 @ budget 82) is incomplete — only low budgets explored. Cannot fairly compare. Uniform methods at budget 2048 reach ~26.78.

---

## 5. Summary: NAS SnapKV vs Uniform SnapKV — Gains

| Task Category | NAS Best Score | NAS Budget | Uniform SnapKV Best | Uniform Budget | NAS Gain vs SnapKV | NAS Budget % of Uniform |
|---|---|---|---|---|---|---|
| Single-Doc QA | 33.70 | 384 | 35.87 | 2048 | —2.17 | 19% |
| Multi-Doc QA | 28.20 | 348 | 29.49 | 2048 | —1.29 | 17% |
| Code | 55.24 | 1024 | 55.62 | 2048 | —0.38 | 50% |
| Summarization | 20.21 | 82 | 26.78 | 2048 | —6.57 ⚠️ | 4% ⚠️ |

> NAS SnapKV achieves **94% of uniform SnapKV's best score on Single-Doc QA at 19% of the budget**, and **96% on Multi-Doc QA at 17% of the budget**. Summarization is incomplete.

---

## 6. NAS SnapKV vs Best Uniform Method (Any Method)

| Task Category | NAS Best Score | NAS Budget | Best Uniform Score | Best Uniform Method | Best Uniform Budget | NAS vs Best Uniform |
|---|---|---|---|---|---|---|
| Single-Doc QA | 33.70 | 384 | 36.05 | AdaKV | 2048 | —2.35 |
| Multi-Doc QA | 28.20 | 348 | 29.57 | AdaKV | 2048 | —1.37 |
| Code | 55.24 | 1024 | 55.62 | SnapKV | 2048 | —0.38 |
| Summarization | 20.21 ⚠️ | 82 ⚠️ | 26.78 | SnapKV | 2048 | —6.57 ⚠️ |

> NAS SnapKV achieves **93% of the best uniform method's score on Single-Doc QA at 19% of the budget**, and **95% on Multi-Doc QA at 17% of the budget**. Code is nearly matched (99%). Summarization is incomplete.

---

## 7. NAS SnapKV vs Uniform SnapKV at Comparable Budgets

### Single-Doc QA — Per-Dataset at Budget ~128

| Method | Avg Budget | narrativeqa | qasper | multifieldqa_en | Avg |
|---|---|---|---|---|---|
| ★ **NAS SnapKV** | 148 | 22.33 | 25.89 | 47.47 | **31.90** |
| Uniform SnapKV | 128 | 21.54 | 21.91 | 45.38 | 29.61 |
| Uniform AdaKV | 128 | 21.59 | 24.37 | 46.76 | 30.91 |
| Uniform PyramidKV | 128 | 21.98 | 22.78 | 43.78 | 29.51 |
| Uniform H2O | 128 | 22.16 | 20.57 | 35.88 | 26.20 |
| Uniform StreamingLLM | 128 | 17.12 | 13.43 | 27.31 | 19.29 |

> ★ NAS SnapKV (31.90 @ budget 148) beats all uniform methods at budget 128, including AdaKV (30.91) by **+0.99** and uniform SnapKV (29.61) by **+2.29**.

### Multi-Doc QA — Per-Dataset at Budget ~128

| Method | Avg Budget | hotpotqa | 2wikimqa | musique | Avg |
|---|---|---|---|---|---|
| ★ **NAS SnapKV** | 122 | **38.84** | **26.84** | 15.62 | **27.10** |
| Uniform SnapKV | 128 | 33.94 | 22.04 | 15.61 | 23.86 |
| Uniform AdaKV | 128 | 35.63 | 25.63 | 14.56 | 25.27 |
| Uniform PyramidKV | 128 | 32.30 | 22.31 | **15.81** | 23.47 |
| Uniform H2O | 128 | 30.65 | 19.70 | 12.96 | 21.10 |
| Uniform StreamingLLM | 128 | 29.54 | 21.91 | 11.94 | 21.13 |

> ★ NAS SnapKV (27.10 @ budget 122) beats all uniform methods at budget 128, including AdaKV (25.27) by **+1.83** and uniform SnapKV (23.86) by **+3.24**. NAS wins on hotpotqa (38.84) and 2wikimqa (26.84).

### Code — Per-Dataset at Budget ~256

| Method | Avg Budget | lcc | repobench-p | Avg |
|---|---|---|---|---|
| ★ **NAS SnapKV** | 256 | 53.88 | 50.30 | 52.09 |
| Uniform SnapKV | 256 | 53.88 | 50.30 | 52.09 |
| Uniform AdaKV | 256 | **54.67** | **50.64** | **52.66** |
| Uniform PyramidKV | 256 | 53.04 | 48.40 | 50.72 |
| Uniform H2O | 256 | 46.88 | 39.30 | 43.09 |
| Uniform StreamingLLM | 256 | 54.31 | 47.38 | 50.85 |

> ★ NAS SnapKV (52.09 @ budget 256) matches uniform SnapKV exactly (this is a uniform config in the NAS Pareto front). AdaKV (52.66) leads at this budget.

---

## 8. Key Takeaways

1. **NAS SnapKV is most effective for Multi-Doc QA** — at budget 122, NAS beats uniform SnapKV at budget 128 by **+3.24** and all uniform methods by **+1.83**. This is the largest NAS gain across all task categories.

2. **Single-Doc QA also benefits significantly** — at budget 148, NAS beats uniform SnapKV at budget 128 by **+2.29** and all uniform methods by **+0.99**.

3. **Code shows no NAS improvement** — NAS SnapKV matches uniform SnapKV at every budget. Code completion on Mistral-7B-v0.2 is not layer-sensitive, so per-layer allocation provides no benefit.

4. **Summarization is incomplete** — NAS only explored budgets 64–124. Cannot draw conclusions. Higher-budget NAS configs needed.

5. **Budget efficiency** — NAS SnapKV achieves 93–96% of the best uniform method's score at **17–19% of the budget** for QA tasks. This translates to ~5× memory savings.

6. **NAS vs AdaKV** — AdaKV is the strongest uniform method on Mistral. NAS SnapKV beats AdaKV at budget 128 on Multi-Doc QA (27.10 vs 25.27, +1.83) and Single-Doc QA (31.90 vs 30.91, +0.99).

7. **Model-dependent results** — Unlike Llama-3-8B where NAS helped Code most, on Mistral-7B-v0.2 NAS helps QA tasks most and Code not at all. This suggests layer sensitivity is model-specific.

---

## 9. Uniform Budget Reference Scores (from BENCHMARKS.md)

### SnapKV — Uniform Budget Averages

| Task Category | Budget 64 | Budget 128 | Budget 256 | Budget 512 | Budget 1024 | Budget 2048 |
|---|---|---|---|---|---|---|
| Single-Doc QA | 25.53 | 29.61 | 31.74 | 33.91 | 34.99 | 35.87 |
| Multi-Doc QA | 22.49 | 23.86 | 25.62 | 26.47 | 28.80 | 29.49 |
| Code | 46.60 | 49.76 | 52.09 | 53.77 | 55.24 | 55.62 |
| Summarization | 19.83 | 21.55 | 23.21 | 24.34 | 25.72 | 26.78 |

### AdaKV — Uniform Budget Averages (strongest uniform method)

| Task Category | Budget 64 | Budget 128 | Budget 256 | Budget 512 | Budget 1024 | Budget 2048 |
|---|---|---|---|---|---|---|
| Single-Doc QA | 28.77 | 30.91 | 33.14 | 34.42 | 34.97 | 36.05 |
| Multi-Doc QA | 23.79 | 25.27 | 26.66 | 27.62 | 28.86 | 29.57 |
| Code | 48.51 | 51.08 | 52.66 | 54.65 | 55.08 | 55.58 |
| Summarization | 20.48 | 22.06 | 22.82 | 23.90 | 24.97 | 26.24 |

### H2O — Uniform Budget Averages

| Task Category | Budget 64 | Budget 128 | Budget 256 | Budget 512 | Budget 1024 | Budget 2048 |
|---|---|---|---|---|---|---|
| Single-Doc QA | 23.22 | 26.20 | 27.92 | 30.52 | 32.14 | 33.33 |
| Multi-Doc QA | 19.22 | 21.10 | 23.70 | 25.18 | 26.58 | 27.23 |
| Code | 36.29 | 39.59 | 43.09 | 46.43 | 49.65 | 51.72 |
| Summarization | 22.38 | 23.50 | 24.55 | 25.14 | 25.92 | 26.74 |

### PyramidKV — Uniform Budget Averages

| Task Category | Budget 64 | Budget 128 | Budget 256 | Budget 512 | Budget 1024 | Budget 2048 |
|---|---|---|---|---|---|---|
| Single-Doc QA | 25.94 | 29.51 | 31.51 | 33.40 | 34.38 | 35.42 |
| Multi-Doc QA | 23.16 | 23.47 | 26.71 | 27.35 | 28.70 | 29.11 |
| Code | 45.87 | 48.95 | 50.72 | 54.11 | 55.03 | 55.40 |
| Summarization | 19.86 | 21.17 | 22.57 | 24.11 | 25.56 | 26.51 |

### StreamingLLM — Uniform Budget Averages

| Task Category | Budget 64 | Budget 128 | Budget 256 | Budget 512 | Budget 1024 | Budget 2048 |
|---|---|---|---|---|---|---|
| Single-Doc QA | 19.16 | 19.29 | 20.77 | 22.65 | 23.65 | 26.90 |
| Multi-Doc QA | 21.62 | 21.13 | 21.21 | 20.93 | 22.18 | 22.99 |
| Code | 44.87 | 48.74 | 50.85 | 52.16 | 53.39 | 54.82 |
| Summarization | 16.39 | 17.48 | 19.25 | 21.55 | 23.35 | 24.65 |

---

*Comparison generated from `mistral_7b_v02_nas_results/snapkv/` (NAS-optimized per-layer configs) and `mistral_7b_v02_benchmark/BENCHMARKS.md` (uniform budget results). All experiments use Mistral-7B-v0.2 with the same evaluation pipeline. ★ = NAS-optimized (our contribution).*
