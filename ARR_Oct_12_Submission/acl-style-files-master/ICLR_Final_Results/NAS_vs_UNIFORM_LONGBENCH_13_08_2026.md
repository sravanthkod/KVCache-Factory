# NAS vs Uniform — LongBench — Meta-Llama-3-8B-Instruct

_Generated 13-08-2026. Uniform sweeps: `Meta-Llama-3-8B-Instruct/<METHOD>_All_Budgets/results_long_bench` (per-layer budget identical across all 32 layers). NAS: LAMP multi-objective search (f1 = avg per-layer budget, f2 = task score) per LongBench category, Pareto-front configs re-evaluated on full data — `NAS_Assets/<CATEGORY>/<method>/top_configs/summary_*.csv` (latest per dir)._

## Validation: harness anchor check

The NAS eval includes an all-64 config; it must reproduce the uniform-64 sweep exactly, otherwise the two pipelines are not comparable.

| method | SINGLE_DOC_QA | MULTI_DOC_QA | SUMMARIZATION | CODE | verdict |
|---|---|---|---|---|---|
| snapkv | +0.00 | +0.00 | +0.01 | +0.00 | ✅ comparable |
| h2o | +0.00 | −0.00 | +0.00 | +0.00 | ✅ comparable |
| adakv | −0.00 | +0.00 | no NAS | +0.00 | ✅ comparable |
| streamingllm | **−5.69** | **−6.83** | no NAS | **−14.23** | ❌ NAS evals invalid (pre-bug-fix; re-run on SGC pending) |
| pyramidkv | — | — | — | — | no NAS run |

## Key results at a glance

| method | category | cheapest NAS ≥ uniform-512 | best searched NAS vs best uniform |
|---|---|---|---|
| SnapKV | SINGLE_DOC_QA | 458 (89% of cache) | 36.08 vs 36.44 (u1024) — below |
| SnapKV | MULTI_DOC_QA | **274 (54%)** | **36.14 vs 35.87 — beats ALL uniforms** |
| SnapKV | SUMMARIZATION | 510 (100%) | 24.43 vs 24.85 (u1024) — below |
| SnapKV | CODE | **298 (58%)** | **58.26 vs 56.73 — beats ALL uniforms** |
| H2O | SINGLE_DOC_QA | — | 32.74 vs 33.60 (u1024) — below |
| H2O | MULTI_DOC_QA | **364 (71%)** | **34.02 vs 33.54 — beats ALL uniforms** |
| H2O | SUMMARIZATION | 464 (91%) | 24.66 vs 24.97 (u1024) — below |
| H2O | CODE | 398 (78%) | 55.91 vs 56.92 (u1024) — below |
| AdaKV | SINGLE_DOC_QA | — (matches u256 at 66%) | 36.40 vs 36.69 (u1024) — below |
| AdaKV | MULTI_DOC_QA | — (matches u256 at 46%) | 35.90 vs 36.30 (u1024) — below |
| AdaKV | CODE | **294 (57%)** | **60.55 vs 58.70 — beats ALL uniforms** |

Pattern: the strongest NAS wins are in MULTI_DOC_QA and CODE — categories where uniform *saturates or degrades*
with budget (uniform-1024 ≤ uniform-512 in 4 of these cells), i.e. exactly where reallocating cache matters more
than adding cache. SINGLE_DOC_QA and SUMMARIZATION keep improving with raw budget, leaving less room for
reallocation. NAS search ranges topped out near avg budget ~500 (SnapKV/AdaKV) so high-budget uniform rungs
(512/1024) are compared against extrapolated-down NAS fronts there.

## SnapKV

### SINGLE_DOCUMENT_QA  (`summary_20260722_143105.csv`)

| config | avg budget | narrativeqa | qasper | multifieldqa_en | mean |
|---|---|---|---|---|---|
| NAS | 64 | 18.51 | 28.46 | 41.86 | **29.61** |
| **uniform-64** | 64 | 18.51 | 28.46 | 41.86 | **29.61** |
| NAS | 70 | 19.08 | 30.35 | 42.58 | **30.67** |
| NAS | 94 | 19.33 | 33.10 | 44.20 | **32.21** |
| NAS | 112 | 19.21 | 34.56 | 44.14 | **32.64** |
| NAS | 122 | 19.36 | 36.16 | 45.01 | **33.51** |
| **uniform-128** | 128 | 18.70 | 35.14 | 45.08 | **32.97** |
| NAS | 134 | 18.63 | 35.35 | 43.76 | **32.58** |
| NAS | 180 | 18.45 | 36.76 | 45.58 | **33.60** |
| NAS | 194 | 19.49 | 36.41 | 44.62 | **33.51** |
| NAS | 244 | 18.31 | 37.36 | 45.23 | **33.63** |
| NAS | 246 | 19.22 | 37.59 | 45.76 | **34.19** |
| NAS | 248 | 19.37 | 37.26 | 45.45 | **34.03** |
| NAS | 256 | 19.91 | 39.03 | 46.20 | **35.05** |
| **uniform-256** | 256 | 19.96 | 39.44 | 46.35 | **35.25** |
| NAS | 284 | 20.53 | 38.93 | 46.18 | **35.21** |
| NAS | 332 | 20.71 | 38.28 | 46.65 | **35.21** |
| NAS | 338 | 20.85 | 37.82 | 45.85 | **34.84** |
| NAS | 374 | 19.66 | 40.74 | 47.01 | **35.80** |
| NAS | 434 | 20.66 | 39.88 | 47.21 | **35.92** |
| NAS | 458 | 19.94 | 40.86 | 47.35 | **36.05** |
| NAS | 506 | 20.85 | 40.25 | 47.13 | **36.08** |
| **uniform-512** | 512 | 19.99 | 41.86 | 46.06 | **35.97** |
| NAS | 574 | 20.41 | 40.59 | 46.96 | **35.99** |
| **uniform-1024** | 1024 | 20.66 | 42.64 | 46.02 | **36.44** |

**Highlights:** matches uniform-128 (32.97) with avg budget 122 (95% of cache, score 33.51); matches uniform-512 (35.97) with avg budget 458 (89% of cache, score 36.05).

### MULTI_DOCUMENT_QA  (`summary_20260722_145551.csv`)

| config | avg budget | hotpotqa | 2wikimqa | musique | mean |
|---|---|---|---|---|---|
| NAS | 64 | 44.32 | 35.34 | 22.00 | **33.89** |
| **uniform-64** | 64 | 44.32 | 35.34 | 22.00 | **33.89** |
| NAS | 66 | 44.88 | 35.09 | 22.17 | **34.05** |
| NAS | 74 | 45.57 | 35.48 | 21.63 | **34.23** |
| NAS | 84 | 45.02 | 35.58 | 22.08 | **34.23** |
| NAS | 100 | 45.45 | 35.00 | 22.81 | **34.42** |
| **uniform-128** | 128 | 45.94 | 36.39 | 22.13 | **34.82** |
| NAS | 130 | 46.44 | 36.12 | 22.05 | **34.87** |
| NAS | 152 | 46.10 | 37.26 | 22.61 | **35.32** |
| NAS | 202 | 46.07 | 36.57 | 22.56 | **35.07** |
| **uniform-256** | 256 | 46.94 | 37.50 | 22.36 | **35.60** |
| NAS | 274 | 46.72 | 38.49 | 23.21 | **36.14** |
| **uniform-512** | 512 | 46.72 | 37.98 | 22.60 | **35.77** |
| **uniform-1024** | 1024 | 47.18 | 38.40 | 22.02 | **35.87** |

**Highlights:** matches uniform-512 (35.77) with avg budget 274 (54% of cache, score 36.14); matches uniform-1024 (35.87) with avg budget 274 (27% of cache, score 36.14); best NAS config (36.14 @ 274) beats ALL uniform budgets (max 35.87).

### SUMMARIZATION  (`summary_20260725_012202.csv`)

| config | avg budget | gov_report | qmsum | multi_news | mean |
|---|---|---|---|---|---|
| NAS | 64 | 19.33 | 19.60 | 19.54 | **19.49** |
| **uniform-64** | 64 | 19.35 | 19.64 | 19.46 | **19.48** |
| NAS | 128 | 20.77 | 20.64 | 21.95 | **21.12** |
| **uniform-128** | 128 | 21.01 | 20.35 | 21.73 | **21.03** |
| NAS | 252 | 21.47 | 20.33 | 22.32 | **21.37** |
| NAS | 256 | 22.20 | 21.04 | 23.57 | **22.27** |
| **uniform-256** | 256 | 22.25 | 21.09 | 23.57 | **22.30** |
| NAS | 268 | 22.09 | 21.53 | 23.39 | **22.34** |
| NAS | 312 | 22.81 | 21.09 | 23.85 | **22.58** |
| NAS | 366 | 21.98 | 21.84 | 23.71 | **22.51** |
| NAS | 390 | 21.95 | 21.39 | 23.49 | **22.28** |
| NAS | 398 | 23.45 | 21.28 | 24.75 | **23.16** |
| NAS | 510 | 23.68 | 21.94 | 25.00 | **23.54** |
| **uniform-512** | 512 | 24.06 | 21.37 | 24.88 | **23.44** |
| NAS | 622 | 24.63 | 21.78 | 25.72 | **24.04** |
| NAS | 732 | 25.30 | 21.69 | 26.31 | **24.43** |
| **uniform-1024** | 1024 | 25.56 | 22.31 | 26.67 | **24.85** |

**Highlights:** matches uniform-512 (23.44) with avg budget 510 (100% of cache, score 23.54).

### CODE  (`summary_20260722_212658.csv`)

| config | avg budget | lcc | repobench-p | mean |
|---|---|---|---|---|
| NAS | 64 | 53.36 | 50.12 | **51.74** |
| **uniform-64** | 64 | 53.36 | 50.12 | **51.74** |
| NAS | 104 | 54.99 | 51.94 | **53.47** |
| **uniform-128** | 128 | 56.90 | 52.73 | **54.81** |
| NAS | 160 | 55.98 | 53.88 | **54.93** |
| NAS | 174 | 55.81 | 51.79 | **53.80** |
| NAS | 206 | 57.10 | 53.47 | **55.28** |
| NAS | 218 | 57.37 | 54.45 | **55.91** |
| NAS | 240 | 57.89 | 54.00 | **55.95** |
| **uniform-256** | 256 | 58.23 | 53.12 | **55.67** |
| NAS | 298 | 59.78 | 54.62 | **57.20** |
| NAS | 302 | 59.33 | 56.51 | **57.92** |
| NAS | 430 | 59.74 | 56.78 | **58.26** |
| NAS | 458 | 59.68 | 55.38 | **57.53** |
| **uniform-512** | 512 | 59.16 | 54.31 | **56.73** |
| **uniform-1024** | 1024 | 58.35 | 53.69 | **56.02** |

**Highlights:** matches uniform-256 (55.67) with avg budget 218 (85% of cache, score 55.91); matches uniform-512 (56.73) with avg budget 298 (58% of cache, score 57.20); matches uniform-1024 (56.02) with avg budget 298 (29% of cache, score 57.20); best NAS config (58.26 @ 430) beats ALL uniform budgets (max 56.73).

## H2O

### SINGLE_DOCUMENT_QA  (`summary_20260801_171738.csv`)

| config | avg budget | narrativeqa | qasper | multifieldqa_en | mean |
|---|---|---|---|---|---|
| NAS | 64 | 17.68 | 25.46 | 32.28 | **25.14** |
| **uniform-64** | 64 | 17.68 | 25.46 | 32.28 | **25.14** |
| NAS | 76 | 17.33 | 25.84 | 32.78 | **25.32** |
| NAS | 104 | 17.75 | 26.80 | 35.57 | **26.71** |
| NAS | 128 | 17.70 | 31.10 | 35.84 | **28.21** |
| **uniform-128** | 128 | 17.70 | 31.10 | 35.84 | **28.21** |
| NAS | 188 | 19.76 | 27.13 | 37.30 | **28.06** |
| NAS | 206 | 18.45 | 28.08 | 37.08 | **27.87** |
| NAS | 236 | 18.87 | 30.35 | 37.74 | **28.99** |
| **uniform-256** | 256 | 18.66 | 32.31 | 38.91 | **29.96** |
| NAS | 262 | 18.61 | 31.33 | 38.33 | **29.42** |
| NAS | 272 | 18.94 | 32.74 | 38.99 | **30.22** |
| NAS | 306 | 16.84 | 34.68 | 40.14 | **30.55** |
| NAS | 312 | 19.28 | 34.00 | 38.31 | **30.53** |
| NAS | 366 | 19.45 | 33.76 | 39.45 | **30.89** |
| NAS | 406 | 19.55 | 34.27 | 40.97 | **31.60** |
| NAS | 496 | 18.13 | 36.16 | 42.30 | **32.20** |
| **uniform-512** | 512 | 19.20 | 35.71 | 42.32 | **32.41** |
| NAS | 518 | 19.34 | 37.33 | 41.54 | **32.74** |
| **uniform-1024** | 1024 | 19.26 | 38.36 | 43.19 | **33.60** |

**Highlights:** no NAS config matches a higher uniform budget at lower cost in this category.

### MULTI_DOCUMENT_QA  (`summary_20260724_210051.csv`)

| config | avg budget | hotpotqa | 2wikimqa | musique | mean |
|---|---|---|---|---|---|
| NAS | 64 | 42.31 | 28.82 | 20.67 | **30.60** |
| **uniform-64** | 64 | 42.31 | 28.82 | 20.67 | **30.60** |
| NAS | 90 | 43.23 | 29.31 | 20.26 | **30.93** |
| NAS | 104 | 43.32 | 32.74 | 19.38 | **31.81** |
| NAS | 110 | 42.99 | 33.15 | 19.58 | **31.91** |
| **uniform-128** | 128 | 43.42 | 33.38 | 20.91 | **32.57** |
| NAS | 222 | 44.72 | 32.90 | 19.35 | **32.32** |
| **uniform-256** | 256 | 44.03 | 33.42 | 19.90 | **32.45** |
| NAS | 264 | 44.11 | 32.75 | 19.76 | **32.21** |
| NAS | 364 | 45.98 | 34.76 | 20.02 | **33.59** |
| NAS | 448 | 45.88 | 35.03 | 21.16 | **34.02** |
| NAS | 460 | 45.70 | 34.80 | 20.57 | **33.69** |
| **uniform-512** | 512 | 43.90 | 34.29 | 20.75 | **32.98** |
| NAS | 516 | 45.79 | 35.94 | 20.24 | **33.99** |
| **uniform-1024** | 1024 | 44.33 | 35.56 | 20.72 | **33.54** |

**Highlights:** matches uniform-512 (32.98) with avg budget 364 (71% of cache, score 33.59); matches uniform-1024 (33.54) with avg budget 364 (36% of cache, score 33.59); best NAS config (34.02 @ 448) beats ALL uniform budgets (max 33.54).

### SUMMARIZATION  (`summary_20260728_194251.csv`)

| config | avg budget | gov_report | qmsum | multi_news | mean |
|---|---|---|---|---|---|
| NAS | 64 | 21.44 | 17.26 | 23.67 | **20.79** |
| **uniform-64** | 64 | 21.44 | 17.26 | 23.66 | **20.79** |
| NAS | 128 | 23.02 | 17.79 | 24.78 | **21.86** |
| **uniform-128** | 128 | 23.02 | 17.79 | 24.82 | **21.88** |
| NAS | 160 | 23.89 | 17.78 | 25.04 | **22.24** |
| NAS | 224 | 24.34 | 18.98 | 25.48 | **22.93** |
| NAS | 256 | 24.78 | 18.94 | 25.77 | **23.16** |
| **uniform-256** | 256 | 24.78 | 18.94 | 25.68 | **23.13** |
| NAS | 268 | 24.89 | 18.51 | 25.91 | **23.10** |
| NAS | 350 | 25.85 | 19.13 | 25.96 | **23.65** |
| NAS | 362 | 26.03 | 18.98 | 26.41 | **23.81** |
| NAS | 372 | 26.29 | 18.92 | 26.54 | **23.92** |
| NAS | 384 | 26.18 | 20.18 | 26.21 | **24.19** |
| NAS | 464 | 26.74 | 19.36 | 26.56 | **24.22** |
| NAS | 490 | 26.70 | 19.48 | 26.35 | **24.18** |
| NAS | 506 | 26.36 | 19.81 | 26.76 | **24.31** |
| NAS | 512 | 27.09 | 19.25 | 26.27 | **24.20** |
| **uniform-512** | 512 | 26.95 | 19.43 | 26.28 | **24.22** |
| NAS | 538 | 26.87 | 20.10 | 26.59 | **24.52** |
| NAS | 540 | 26.86 | 20.07 | 26.58 | **24.50** |
| NAS | 552 | 27.01 | 20.20 | 26.77 | **24.66** |
| **uniform-1024** | 1024 | 27.94 | 20.05 | 26.93 | **24.97** |

**Highlights:** matches uniform-512 (24.22) with avg budget 464 (91% of cache, score 24.22).

### CODE  (`summary_20260725_083026.csv`)

| config | avg budget | lcc | repobench-p | mean |
|---|---|---|---|---|
| NAS | 64 | 46.21 | 38.96 | **42.59** |
| **uniform-64** | 64 | 46.21 | 38.96 | **42.59** |
| NAS | 128 | 49.92 | 42.00 | **45.96** |
| **uniform-128** | 128 | 49.92 | 42.00 | **45.96** |
| NAS | 256 | 53.39 | 44.76 | **49.08** |
| **uniform-256** | 256 | 53.45 | 45.54 | **49.50** |
| NAS | 312 | 53.20 | 45.55 | **49.38** |
| NAS | 348 | 53.85 | 47.27 | **50.56** |
| NAS | 366 | 53.19 | 46.46 | **49.83** |
| NAS | 374 | 54.58 | 46.88 | **50.73** |
| NAS | 376 | 54.63 | 47.39 | **51.01** |
| NAS | 392 | 54.78 | 47.91 | **51.34** |
| NAS | 398 | 57.52 | 49.38 | **53.45** |
| NAS | 410 | 54.92 | 47.62 | **51.27** |
| NAS | 424 | 56.62 | 48.33 | **52.47** |
| NAS | 508 | 57.59 | 49.87 | **53.73** |
| NAS | 510 | 59.10 | 51.52 | **55.31** |
| **uniform-512** | 512 | 55.97 | 49.65 | **52.81** |
| NAS | 632 | 58.63 | 52.52 | **55.58** |
| NAS | 646 | 58.95 | 52.02 | **55.48** |
| NAS | 666 | 58.75 | 52.46 | **55.61** |
| NAS | 696 | 58.66 | 53.15 | **55.91** |
| NAS | 1024 | 59.62 | 54.23 | **56.92** |
| **uniform-1024** | 1024 | 59.62 | 54.23 | **56.92** |

**Highlights:** matches uniform-512 (52.81) with avg budget 398 (78% of cache, score 53.45).

## AdaKV

### SINGLE_DOCUMENT_QA  (`summary_20260803_201801.csv`)

| config | avg budget | narrativeqa | qasper | multifieldqa_en | mean |
|---|---|---|---|---|---|
| NAS | 64 | 18.64 | 30.49 | 43.63 | **30.92** |
| **uniform-64** | 64 | 18.65 | 30.49 | 43.63 | **30.92** |
| NAS | 68 | 18.08 | 30.77 | 43.31 | **30.72** |
| NAS | 70 | 17.58 | 31.62 | 44.94 | **31.38** |
| NAS | 78 | 17.72 | 32.87 | 45.75 | **32.11** |
| NAS | 80 | 18.80 | 32.04 | 44.77 | **31.87** |
| NAS | 82 | 19.87 | 32.76 | 44.90 | **32.51** |
| NAS | 100 | 19.80 | 35.22 | 45.74 | **33.59** |
| NAS | 110 | 18.94 | 36.75 | 46.24 | **33.98** |
| **uniform-128** | 128 | 18.60 | 34.52 | 45.36 | **32.83** |
| NAS | 132 | 20.40 | 36.15 | 46.09 | **34.21** |
| NAS | 136 | 20.48 | 36.16 | 46.23 | **34.29** |
| NAS | 168 | 20.78 | 38.90 | 46.57 | **35.42** |
| NAS | 184 | 20.84 | 38.78 | 47.49 | **35.70** |
| NAS | 214 | 20.09 | 39.35 | 46.36 | **35.27** |
| NAS | 244 | 21.65 | 39.49 | 48.05 | **36.40** |
| **uniform-256** | 256 | 20.09 | 39.10 | 46.04 | **35.08** |
| NAS | 360 | 21.04 | 40.12 | 47.68 | **36.28** |
| NAS | 464 | 20.36 | 40.29 | 47.52 | **36.06** |
| **uniform-512** | 512 | 21.32 | 41.86 | 46.87 | **36.68** |
| **uniform-1024** | 1024 | 20.96 | 42.03 | 47.07 | **36.69** |

**Highlights:** matches uniform-128 (32.83) with avg budget 100 (78% of cache, score 33.59); matches uniform-256 (35.08) with avg budget 168 (66% of cache, score 35.42).

### MULTI_DOCUMENT_QA  (`summary_20260804_011245.csv`)

| config | avg budget | hotpotqa | 2wikimqa | musique | mean |
|---|---|---|---|---|---|
| NAS | 64 | 44.05 | 34.54 | 21.14 | **33.24** |
| **uniform-64** | 64 | 44.05 | 34.54 | 21.14 | **33.24** |
| NAS | 68 | 45.24 | 35.12 | 21.79 | **34.05** |
| NAS | 70 | 44.48 | 35.17 | 21.93 | **33.86** |
| NAS | 74 | 45.53 | 35.47 | 22.15 | **34.38** |
| NAS | 84 | 45.60 | 34.89 | 22.37 | **34.29** |
| NAS | 88 | 46.00 | 36.16 | 22.31 | **34.82** |
| NAS | 102 | 46.27 | 36.71 | 22.82 | **35.27** |
| NAS | 118 | 46.34 | 36.90 | 23.23 | **35.49** |
| **uniform-128** | 128 | 45.50 | 36.81 | 22.67 | **34.99** |
| NAS | 130 | 46.64 | 36.79 | 23.10 | **35.51** |
| NAS | 138 | 46.69 | 36.58 | 23.10 | **35.46** |
| NAS | 142 | 46.69 | 36.58 | 23.14 | **35.47** |
| NAS | 154 | 47.31 | 36.46 | 23.11 | **35.63** |
| NAS | 158 | 47.36 | 36.43 | 23.45 | **35.75** |
| NAS | 172 | 46.65 | 36.96 | 23.42 | **35.68** |
| NAS | 174 | 47.61 | 36.89 | 23.20 | **35.90** |
| NAS | 178 | 46.89 | 36.90 | 23.42 | **35.74** |
| NAS | 188 | 47.32 | 37.03 | 22.85 | **35.73** |
| **uniform-256** | 256 | 46.07 | 37.57 | 22.63 | **35.42** |
| **uniform-512** | 512 | 47.20 | 38.68 | 22.53 | **36.14** |
| **uniform-1024** | 1024 | 47.26 | 38.68 | 22.96 | **36.30** |

**Highlights:** matches uniform-128 (34.99) with avg budget 102 (80% of cache, score 35.27); matches uniform-256 (35.42) with avg budget 118 (46% of cache, score 35.49).

### SUMMARIZATION — no NAS run on this disk

| config | avg budget | gov_report | qmsum | multi_news | mean |
|---|---|---|---|---|---|
| uniform-64 | 64 | 20.27 | 19.87 | 20.52 | **20.22** |
| uniform-128 | 128 | 21.57 | 21.26 | 22.32 | **21.72** |
| uniform-256 | 256 | 22.57 | 21.81 | 23.77 | **22.72** |
| uniform-512 | 512 | 23.88 | 21.86 | 25.12 | **23.62** |
| uniform-1024 | 1024 | 25.62 | 22.34 | 26.61 | **24.86** |

### CODE  (`summary_20260804_215543.csv`)

| config | avg budget | lcc | repobench-p | mean |
|---|---|---|---|---|
| NAS | 64 | 56.36 | 54.44 | **55.40** |
| **uniform-64** | 64 | 56.36 | 54.44 | **55.40** |
| NAS | 128 | 59.83 | 54.77 | **57.30** |
| **uniform-128** | 128 | 59.83 | 54.77 | **57.30** |
| NAS | 216 | 59.78 | 56.30 | **58.04** |
| NAS | 228 | 60.16 | 55.83 | **57.99** |
| **uniform-256** | 256 | 60.02 | 56.36 | **58.19** |
| NAS | 278 | 59.14 | 56.03 | **57.59** |
| NAS | 282 | 60.28 | 56.06 | **58.17** |
| NAS | 294 | 61.40 | 57.08 | **59.24** |
| NAS | 318 | 60.46 | 56.61 | **58.53** |
| NAS | 322 | 60.18 | 56.85 | **58.52** |
| NAS | 338 | 61.15 | 58.54 | **59.84** |
| NAS | 384 | 60.88 | 56.48 | **58.68** |
| NAS | 396 | 62.21 | 58.88 | **60.55** |
| NAS | 470 | 62.60 | 57.87 | **60.23** |
| **uniform-512** | 512 | 61.09 | 56.31 | **58.70** |
| **uniform-1024** | 1024 | 60.00 | 55.96 | **57.98** |

**Highlights:** matches uniform-512 (58.70) with avg budget 294 (57% of cache, score 59.24); matches uniform-1024 (57.98) with avg budget 216 (21% of cache, score 58.04); best NAS config (60.55 @ 396) beats ALL uniform budgets (max 58.70).

## StreamingLLM — ⚠ NAS numbers on this disk are INVALID

The all-64 anchors miss the uniform sweep by −5.7 to −14.2 points (window-derivation bug in the old NAS eval; fixed, re-evaluation running on SGC). Uniform reference (valid):

**SINGLE_DOCUMENT_QA**: uniform-64 = 24.63, uniform-128 = 24.65, uniform-256 = 25.17, uniform-512 = 25.91, uniform-1024 = 28.02

**MULTI_DOCUMENT_QA**: uniform-64 = 30.74, uniform-128 = 31.28, uniform-256 = 31.02, uniform-512 = 30.96, uniform-1024 = 32.28

**SUMMARIZATION**: uniform-64 = 13.72, uniform-128 = 14.21, uniform-256 = 14.63, uniform-512 = 15.35, uniform-1024 = 15.83

**CODE**: uniform-64 = 50.50, uniform-128 = 52.53, uniform-256 = 54.80, uniform-512 = 55.97, uniform-1024 = 56.39

## PyramidKV — uniform only (no NAS run yet)

**SINGLE_DOCUMENT_QA**: uniform-64 = 30.33, uniform-128 = 33.08, uniform-256 = 34.80, uniform-512 = 35.96, uniform-1024 = 36.47

**MULTI_DOCUMENT_QA**: uniform-64 = 33.47, uniform-128 = 35.23, uniform-256 = 35.33, uniform-512 = 35.99, uniform-1024 = 36.04

**SUMMARIZATION**: uniform-64 = 19.65, uniform-128 = 21.16, uniform-256 = 22.43, uniform-512 = 23.67, uniform-1024 = 24.78

**CODE**: uniform-64 = 51.44, uniform-128 = 54.57, uniform-256 = 55.72, uniform-512 = 57.12, uniform-1024 = 57.17

## Gaps / to-do

- AdaKV: SUMMARIZATION NAS missing (not on this disk; other categories rsynced from LLM WS).
- StreamingLLM: post-fix NAS evals pending on SGC (Status.md 13/08/2026); SUMMARIZATION NAS also missing.
- PyramidKV: no NAS at all — decide run vs. drop from the paper table.
- FEW_SHOT_LEARNING / SYNTHETIC categories: no NAS for any method (uniform sweeps exist).
