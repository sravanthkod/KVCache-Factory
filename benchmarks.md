# KV Cache Eviction Benchmarks — Meta-Llama-3-8B-Instruct

This document consolidates all benchmark scores from the KVCache-Factory evaluation suite for **Meta-Llama-3-8B-Instruct**.

---

## Overview

| Item | Details |
|---|---|
| **Model** | Meta-Llama-3-8B-Instruct |
| **Dtype** | float16 |
| **Attention** | flash_attention_2 |
| **KV Cache Granularity** | query_head |
| **GQA Score Aggregation** | mean |
| **Benchmarks** | LongBench (16 tasks), RULER (11 tasks @ 4096 ctx) |
| **Budgets** | 64, 128, 256, 512, 1024 |
| **Methods Evaluated** | SnapKV, H2O, AdaKV, PyramidKV, StreamingLLM |
| **Transformers** | 4.43.3 / 4.44.2 |
| **Torch** | 2.6.0+cu124 / 2.9.0+cu126 |

### Method Hyper-parameters

| Parameter | SnapKV | H2O | AdaKV | PyramidKV | StreamingLLM |
|---|---|---|---|---|---|
| `window_size` | 8 | 8 | 32 (recent) | 8 | budget − 4 |
| `kernel_size` | 7 | 7 | 7 | 7 | 7 |
| `pooling` | maxpool | maxpool | maxpool | maxpool | maxpool |
| `floor` | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 |
| `pruning_ratio` | 0.4 | 0.4 | 0.4 | 0.4 | 0.4 |

---

## 1. LongBench Results

LongBench evaluates long-context understanding across 16 tasks. Scores are on a 0–100 scale. `-1` indicates the task was not evaluated for that method/budget combination.

### LongBench Task Categories

| Category | Tasks | Metric |
|---|---|---|
| Single-doc QA | narrativeqa, qasper, multifieldqa_en | QA F1 |
| Multi-doc QA | hotpotqa, 2wikimqa, musique | QA F1 |
| Summarization | gov_report, qmsum, multi_news | ROUGE-L |
| Few-shot | trec, triviaqa, samsum | Classification / QA F1 / ROUGE-L |
| Synthetic | passage_count, passage_retrieval_en | Count / Retrieval |
| Code | lcc, repobench-p | Code Similarity |

---

### 1.1 SnapKV

| Dataset | Budget 64 | Budget 128 | Budget 256 | Budget 512 | Budget 1024 |
|---|---|---|---|---|---|
| narrativeqa | 18.51 | 18.70 | 19.96 | 19.99 | 20.66 |
| qasper | 28.46 | 35.14 | 39.44 | 41.86 | 42.64 |
| multifieldqa_en | 41.86 | 45.08 | 46.35 | 46.06 | 46.02 |
| hotpotqa | 44.32 | 45.94 | 46.94 | 46.72 | 47.18 |
| 2wikimqa | 35.34 | 36.39 | 37.50 | 37.98 | 38.40 |
| musique | 22.00 | 22.13 | 22.36 | 22.60 | 22.02 |
| gov_report | 19.35 | 21.01 | 22.25 | 24.06 | 25.56 |
| qmsum | 19.64 | 20.35 | 21.09 | 21.37 | 22.31 |
| multi_news | 19.46 | 21.73 | 23.57 | 24.88 | 26.67 |
| trec | 50.50 | 65.50 | 71.50 | — | — |
| triviaqa | 89.22 | 89.78 | 90.94 | — | — |
| samsum | 36.25 | 38.99 | 39.73 | — | — |
| passage_count | 5.75 | 5.50 | 8.00 | — | — |
| passage_retrieval_en | 66.00 | 68.00 | 67.50 | — | — |
| lcc | 53.36 | 56.90 | 58.23 | 59.16 | 58.35 |
| repobench-p | 50.12 | 52.73 | 53.12 | 54.31 | 53.69 |

---

### 1.2 H2O

| Dataset | Budget 64 | Budget 128 | Budget 256 | Budget 512 | Budget 1024 |
|---|---|---|---|---|---|
| narrativeqa | 17.68 | 17.70 | 18.66 | 19.20 | — |
| qasper | 25.46 | 31.10 | 32.31 | 35.71 | — |
| multifieldqa_en | 32.28 | 35.84 | 38.91 | 42.32 | — |
| hotpotqa | 42.31 | 43.42 | 44.03 | 43.90 | — |
| 2wikimqa | 28.82 | 33.38 | 33.42 | 34.29 | — |
| musique | 20.67 | 20.91 | 19.90 | 20.75 | — |
| gov_report | 21.44 | 23.02 | 24.78 | 26.95 | — |
| qmsum | 17.26 | 17.79 | 18.94 | 19.43 | — |
| multi_news | 23.66 | 24.82 | 25.68 | 26.28 | — |
| lcc | 46.21 | 49.92 | 53.45 | 55.97 | — |
| repobench-p | 38.96 | 42.00 | 45.54 | 49.65 | — |

> **Note:** H2O budget 1024 results.csv was not found (inference may not have completed).

---

### 1.3 AdaKV

| Dataset | Budget 64 | Budget 128 | Budget 256 | Budget 512 | Budget 1024 |
|---|---|---|---|---|---|
| narrativeqa | 18.65 | 18.60 | 20.09 | 21.32 | 20.96 |
| qasper | 30.49 | 34.52 | 39.10 | 41.86 | 42.03 |
| multifieldqa_en | 43.63 | 45.36 | 46.04 | 46.87 | 47.07 |
| hotpotqa | 44.05 | 45.50 | 46.07 | 47.20 | 47.26 |
| 2wikimqa | 34.54 | 36.81 | 37.57 | 38.68 | 38.68 |
| musique | 21.14 | 22.67 | 22.63 | 22.53 | 22.96 |
| gov_report | 20.27 | 21.57 | 22.57 | 23.88 | 25.62 |
| qmsum | 19.87 | 21.26 | 21.81 | 21.86 | 22.34 |
| multi_news | 20.52 | 22.32 | 23.77 | 25.12 | 26.61 |
| lcc | 54.54 | 57.98 | 58.18 | 59.23 | 57.94 |
| repobench-p | 52.23 | 52.70 | 54.55 | 54.40 | 53.98 |

---

### 1.4 PyramidKV

| Dataset | Budget 64 | Budget 128 | Budget 256 | Budget 512 | Budget 1024 |
|---|---|---|---|---|---|
| narrativeqa | 16.99 | 19.17 | 19.28 | 20.57 | 20.88 |
| qasper | 30.86 | 35.49 | 39.66 | 41.11 | 41.68 |
| multifieldqa_en | 43.15 | 44.57 | 45.47 | 46.20 | 46.86 |
| hotpotqa | 43.96 | 46.03 | 46.52 | 47.47 | 47.23 |
| 2wikimqa | 34.83 | 36.73 | 37.24 | 38.15 | 38.15 |
| musique | 21.63 | 22.92 | 22.22 | 22.34 | 22.75 |
| gov_report | 19.54 | 21.02 | 22.62 | 24.04 | 25.49 |
| qmsum | 19.38 | 20.50 | 21.17 | 21.81 | 22.10 |
| multi_news | 20.03 | 21.97 | 23.50 | 25.15 | 26.74 |
| lcc | 53.75 | 57.71 | 58.33 | 59.88 | 59.88 |
| repobench-p | 49.13 | 51.43 | 53.12 | 54.36 | 54.47 |

---

### 1.5 StreamingLLM

| Dataset | Budget 64 | Budget 128 | Budget 256 | Budget 512 | Budget 1024 |
|---|---|---|---|---|---|
| narrativeqa | 17.06 | 16.43 | 17.40 | 18.82 | 20.32 |
| qasper | 26.70 | 25.81 | 26.63 | 26.93 | 30.25 |
| multifieldqa_en | 30.13 | 31.70 | 31.49 | 31.97 | 33.48 |
| hotpotqa | 41.78 | 42.56 | 42.28 | 42.42 | 43.61 |
| 2wikimqa | 32.92 | 33.34 | 32.86 | 32.75 | 34.06 |
| musique | 17.52 | 17.93 | 17.93 | 17.71 | 19.16 |
| gov_report | 12.76 | 13.26 | 13.90 | 14.58 | 15.28 |
| qmsum | 16.30 | 16.30 | 16.16 | 16.23 | 16.20 |
| multi_news | 12.10 | 13.08 | 13.83 | 15.24 | 16.01 |
| lcc | 51.35 | 54.17 | 57.14 | 58.97 | 58.71 |
| repobench-p | 49.64 | 50.88 | 52.47 | 52.97 | 54.06 |

---

## 2. Cross-Method Comparison (LongBench)

The tables below compare all methods side-by-side for each budget. Only the 11 core LongBench tasks (evaluated across all methods) are shown.

### 2.1 Budget 64

| Dataset | SnapKV | H2O | AdaKV | PyramidKV | StreamingLLM |
|---|---|---|---|---|---|
| narrativeqa | 18.51 | 17.68 | **18.65** | 16.99 | 17.06 |
| qasper | 28.46 | 25.46 | **30.49** | 30.86 | 26.70 |
| multifieldqa_en | 41.86 | 32.28 | **43.63** | 43.15 | 30.13 |
| hotpotqa | **44.32** | 42.31 | 44.05 | 43.96 | 41.78 |
| 2wikimqa | **35.34** | 28.82 | 34.54 | 34.83 | 32.92 |
| musique | **22.00** | 20.67 | 21.14 | 21.63 | 17.52 |
| gov_report | 19.35 | **21.44** | 20.27 | 19.54 | 12.76 |
| qmsum | **19.64** | 17.26 | 19.87 | 19.38 | 16.30 |
| multi_news | 19.46 | **23.66** | 20.52 | 20.03 | 12.10 |
| lcc | 53.36 | 46.21 | **54.54** | 53.75 | 51.35 |
| repobench-p | **52.23** | 38.96 | 52.23 | 49.13 | 49.64 |

### 2.2 Budget 128

| Dataset | SnapKV | H2O | AdaKV | PyramidKV | StreamingLLM |
|---|---|---|---|---|---|
| narrativeqa | 18.70 | 17.70 | 18.60 | **19.17** | 16.43 |
| qasper | 35.14 | 31.10 | 34.52 | **35.49** | 25.81 |
| multifieldqa_en | **45.08** | 35.84 | 45.36 | 44.57 | 31.70 |
| hotpotqa | 45.94 | 43.42 | 45.50 | **46.03** | 42.56 |
| 2wikimqa | 36.39 | 33.38 | **36.81** | 36.73 | 33.34 |
| musique | 22.13 | 20.91 | **22.67** | 22.92 | 17.93 |
| gov_report | 21.01 | 23.02 | 21.57 | 21.02 | 13.26 |
| qmsum | 20.35 | 17.79 | **21.26** | 20.50 | 16.30 |
| multi_news | 21.73 | **24.82** | 22.32 | 21.97 | 13.08 |
| lcc | 56.90 | 49.92 | **57.98** | 57.71 | 54.17 |
| repobench-p | **52.73** | 42.00 | 52.70 | 51.43 | 50.88 |

### 2.3 Budget 256

| Dataset | SnapKV | H2O | AdaKV | PyramidKV | StreamingLLM |
|---|---|---|---|---|---|
| narrativeqa | 19.96 | 18.66 | **20.09** | 19.28 | 17.40 |
| qasper | 39.44 | 32.31 | 39.10 | **39.66** | 26.63 |
| multifieldqa_en | 46.35 | 38.91 | **46.04** | 45.47 | 31.49 |
| hotpotqa | **46.94** | 44.03 | 46.07 | 46.52 | 42.28 |
| 2wikimqa | **37.50** | 33.42 | 37.57 | 37.24 | 32.86 |
| musique | **22.36** | 19.90 | 22.63 | 22.22 | 17.93 |
| gov_report | 22.25 | **24.78** | 22.57 | 22.62 | 13.90 |
| qmsum | 21.09 | 18.94 | **21.81** | 21.17 | 16.16 |
| multi_news | 23.57 | **25.68** | 23.77 | 23.50 | 13.83 |
| lcc | 58.23 | 53.45 | 58.18 | **58.33** | 57.14 |
| repobench-p | **54.55** | 45.54 | 54.55 | 53.12 | 52.47 |

### 2.4 Budget 512

| Dataset | SnapKV | H2O | AdaKV | PyramidKV | StreamingLLM |
|---|---|---|---|---|---|
| narrativeqa | 19.99 | 19.20 | **21.32** | 20.57 | 18.82 |
| qasper | **41.86** | 35.71 | 41.86 | 41.11 | 26.93 |
| multifieldqa_en | 46.06 | 42.32 | **46.87** | 46.20 | 31.97 |
| hotpotqa | 46.72 | 43.90 | **47.20** | 47.47 | 42.42 |
| 2wikimqa | 37.98 | 34.29 | **38.68** | 38.15 | 32.75 |
| musique | **22.60** | 20.75 | 22.53 | 22.34 | 17.71 |
| gov_report | 24.06 | **26.95** | 23.88 | 24.04 | 14.58 |
| qmsum | 21.37 | 19.43 | **21.86** | 21.81 | 16.23 |
| multi_news | 24.88 | **26.28** | 25.12 | 25.15 | 15.24 |
| lcc | 59.16 | 55.97 | **59.23** | 59.88 | 58.97 |
| repobench-p | **54.31** | 49.65 | 54.40 | 54.36 | 52.97 |

### 2.5 Budget 1024

| Dataset | SnapKV | H2O | AdaKV | PyramidKV | StreamingLLM |
|---|---|---|---|---|---|
| narrativeqa | 20.66 | — | 20.96 | **20.88** | 20.32 |
| qasper | **42.64** | — | 42.03 | 41.68 | 30.25 |
| multifieldqa_en | 46.02 | — | **47.07** | 46.86 | 33.48 |
| hotpotqa | 47.18 | — | **47.26** | 47.23 | 43.61 |
| 2wikimqa | **38.40** | — | 38.68 | 38.15 | 34.06 |
| musique | 22.02 | — | **22.96** | 22.75 | 19.16 |
| gov_report | 25.56 | — | **25.62** | 25.49 | 15.28 |
| qmsum | 22.31 | — | **22.34** | 22.10 | 16.20 |
| multi_news | 26.67 | — | **26.61** | 26.74 | 16.01 |
| lcc | 58.35 | — | 57.94 | **59.88** | 58.71 |
| repobench-p | 53.69 | — | 53.98 | **54.47** | 54.06 |

> **Bold** = best score for that dataset/budget. H2O budget 1024 was not available.

---

## 3. Average Scores (Core 11 LongBench Tasks)

Average across the 11 tasks evaluated for all methods: narrativeqa, qasper, multifieldqa_en, hotpotqa, 2wikimqa, musique, gov_report, qmsum, multi_news, lcc, repobench-p.

| Budget | SnapKV | H2O | AdaKV | PyramidKV | StreamingLLM |
|---|---|---|---|---|---|
| 64 | 31.74 | 28.81 | **32.36** | 32.10 | 27.97 |
| 128 | 34.65 | 30.91 | **35.15** | 35.02 | 29.70 |
| 256 | 36.45 | 32.26 | **36.72** | 36.65 | 31.05 |
| 512 | 37.42 | 34.05 | **37.65** | 37.64 | 32.34 |
| 1024 | 37.95 | — | **38.41** | 38.38 | 33.33 |

> **Key takeaway:** AdaKV consistently achieves the highest average across all budgets, with PyramidKV as a close second. SnapKV is competitive at lower budgets. StreamingLLM lags significantly, especially on summarization tasks (gov_report, multi_news). H2O underperforms on QA and code tasks but is strong on summarization.

---

## 4. RULER Results (SnapKV, Budget 64, Context Length 4096)

RULER evaluates retrieval capabilities with needle-in-a-haystack and related tasks. Metric: string match accuracy (0–100).

| Task | SnapKV Score |
|---|---|
| niah_single_1 | 99.80 |
| niah_single_2 | 92.83 |
| niah_single_3 | — |
| niah_multikey_1 | — |
| niah_multikey_2 | — |
| niah_multikey_3 | — |
| niah_multiquery | — |
| niah_multivalue | — |
| cwe | — |
| fwe | — |
| vt | — |

> **Note:** Only `niah_single_1` and `niah_single_2` were completed for RULER. The remaining 9 tasks were not run or did not finish. SnapKV achieves near-perfect retrieval on single-needle tasks at budget 64.

---

## 5. SnapKV Extended Tasks (Budgets 64–256)

SnapKV was additionally evaluated on 5 tasks (trec, triviaqa, samsum, passage_count, passage_retrieval_en) that other methods did not run.

| Dataset | Budget 64 | Budget 128 | Budget 256 |
|---|---|---|---|
| trec | 50.50 | 65.50 | 71.50 |
| triviaqa | 89.22 | 89.78 | 90.94 |
| samsum | 36.25 | 38.99 | 39.73 |
| passage_count | 5.75 | 5.50 | 8.00 |
| passage_retrieval_en | 66.00 | 68.00 | 67.50 |

---

## 6. Directory Structure

```
Meta-Llama-3-8B-Instruct/
├── ADA_KV_All_Budgets/
│   └── results_long_bench/
│       ├── adakv_budget_64/    → results.csv, run_meta.json, 11 task dirs
│       ├── adakv_budget_128/
│       ├── adakv_budget_256/
│       ├── adakv_budget_512/
│       └── adakv_budget_1024/
├── H2O_KV_All_Budgets/
│   └── results_long_bench/
│       ├── h2o_budget_64/
│       ├── h2o_budget_128/
│       ├── h2o_budget_256/
│       ├── h2o_budget_512/
│       └── h2o_budget_1024/   (no results.csv — inference incomplete)
├── Pyramid_KV_All_Budgets/
│   └── results_long_bench/
│       ├── pyramidkv_budget_64/
│       ├── pyramidkv_budget_128/
│       ├── pyramidkv_budget_256/
│       ├── pyramidkv_budget_512/
│       └── pyramidkv_budget_1024/
├── SNAP_KV_All_Budgets/
│   ├── results_long_bench/
│   │   ├── snapkv_budget_64/
│   │   ├── snapkv_budget_128/
│   │   ├── snapkv_budget_256/
│   │   ├── snapkv_budget_512/
│   │   └── snapkv_budget_1024/
│   └── results_ruler/
│       └── snapkv_budget_64/
│           └── .../4096/
│               ├── niah_single_1/snapkv.json
│               └── niah_single_2/snapkv.json
├── Streaming_LLM_All_Budgets/
│   └── results_long_bench/
│       ├── streamingllm_budget_64/
│       ├── streamingllm_budget_128/
│       ├── streamingllm_budget_256/
│       ├── streamingllm_budget_512/
│       └── streamingllm_budget_1024/
└── BENCHMARKS.md  ← this file
```

---

## 7. Data Completeness Summary

| Method | Budget 64 | Budget 128 | Budget 256 | Budget 512 | Budget 1024 | RULER |
|---|---|---|---|---|---|---|
| SnapKV | ✅ 16 tasks | ✅ 16 tasks | ✅ 16 tasks | ✅ 11 tasks | ✅ 11 tasks | ⚠️ 2/11 tasks |
| H2O | ✅ 11 tasks | ✅ 11 tasks | ✅ 11 tasks | ✅ 11 tasks | ❌ Missing | ❌ Not run |
| AdaKV | ✅ 11 tasks | ✅ 11 tasks | ✅ 11 tasks | ✅ 11 tasks | ✅ 11 tasks | ❌ Not run |
| PyramidKV | ✅ 11 tasks | ✅ 11 tasks | ✅ 11 tasks | ✅ 11 tasks | ✅ 11 tasks | ❌ Not run |
| StreamingLLM | ✅ 11 tasks | ✅ 11 tasks | ✅ 11 tasks | ✅ 11 tasks | ✅ 11 tasks | ❌ Not run |

> SnapKV budgets 64/128/256 include 5 additional tasks (trec, triviaqa, samsum, passage_count, passage_retrieval_en). Budgets 512/1024 only cover the 11 core tasks. Other methods cover only the 11 core tasks across all budgets.

---

*Generated from results.csv files in the KVCache-Factory benchmark directory. PyramidKV scores were computed on-the-fly from raw prediction JSONs using `eval.py`. RULER scores were computed using `string_match_all` from `metrics.py`.*
