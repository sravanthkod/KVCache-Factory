## B2 — One search, many budgets (rescaled Step-2 winner vs uniform, full-data)

Each winner shape was found once by the unconstrained Step-1 search and picked on full data in Step 2, then proportionally rescaled to every target budget (`0.05 + 0.9·b/max(b)`, continuous decode) with **no further search**. EvolKV, by contrast, re-runs its full CMA-ES search per target budget.

| Benchmark | Category | Method | Winner's natural avg budget | Budget | Floor | Uniform | Rescaled winner | Δ |
|---|---|---|---|---|---|---|---|---|
| longbench | CODE | h2o | 2456 | 128 | 64 | 45.96 | 46.59 | +0.63 |
| longbench | CODE | h2o | 2456 | 256 | 64 | 49.49 | 50.59 | +1.10 |
| longbench | CODE | h2o | 2456 | 512 | 64 | 52.81 | 54.03 | +1.22 |
| longbench | CODE | h2o | 2456 | 1024 | 64 | 56.92 | 56.15 | -0.77 |
| longbench | CODE | snapkv | 430 | 128 | 64 | 54.81 | 55.86 | +1.05 |
| longbench | CODE | snapkv | 430 | 256 | 64 | 55.67 | 57.33 | +1.66 |
| longbench | CODE | snapkv | 430 | 512 | 64 | 56.73 | 58.16 | +1.43 |
| longbench | CODE | snapkv | 430 | 1024 | 64 | 56.02 | 58.52 | +2.49 |
| longbench | MULTI_DOCUMENT_QA | h2o | 448 | 128 | 64 | 32.57 | 32.16 | -0.41 |
| longbench | MULTI_DOCUMENT_QA | h2o | 448 | 256 | 64 | 32.45 | 32.86 | +0.41 |
| longbench | MULTI_DOCUMENT_QA | h2o | 448 | 512 | 64 | 32.98 | 34.33 | +1.35 |
| longbench | MULTI_DOCUMENT_QA | h2o | 448 | 1024 | 64 | 33.54 | 34.38 | +0.84 |
| longbench | MULTI_DOCUMENT_QA | snapkv | 274 | 128 | 64 | 34.82 | 35.02 | +0.20 |
| longbench | MULTI_DOCUMENT_QA | snapkv | 274 | 256 | 64 | 35.60 | 36.31 | +0.71 |
| longbench | MULTI_DOCUMENT_QA | snapkv | 274 | 512 | 64 | 35.77 | 35.73 | -0.04 |
| longbench | MULTI_DOCUMENT_QA | snapkv | 274 | 1024 | 64 | 35.87 | 36.26 | +0.39 |
| longbench | SINGLE_DOCUMENT_QA | h2o | 518 | 128 | 64 | 28.21 | 29.72 | +1.51 |
| longbench | SINGLE_DOCUMENT_QA | h2o | 518 | 256 | 64 | 29.96 | 30.70 | +0.74 |
| longbench | SINGLE_DOCUMENT_QA | h2o | 518 | 512 | 64 | 32.41 | 32.21 | -0.20 |
| longbench | SINGLE_DOCUMENT_QA | h2o | 518 | 1024 | 64 | 33.60 | 34.20 | +0.59 |
| longbench | SINGLE_DOCUMENT_QA | snapkv | 506 | 128 | 64 | 32.97 | 33.51 | +0.54 |
| longbench | SINGLE_DOCUMENT_QA | snapkv | 506 | 256 | 64 | 35.25 | 34.51 | -0.74 |
| longbench | SINGLE_DOCUMENT_QA | snapkv | 506 | 512 | 64 | 35.97 | 36.33 | +0.36 |
| longbench | SINGLE_DOCUMENT_QA | snapkv | 506 | 1024 | 64 | 36.44 | 36.46 | +0.02 |
| longbench | SUMMARIZATION | h2o | 552 | 128 | 64 | 21.88 | 22.02 | +0.14 |
| longbench | SUMMARIZATION | h2o | 552 | 256 | 64 | 23.13 | 23.17 | +0.04 |
| longbench | SUMMARIZATION | h2o | 552 | 512 | 64 | 24.22 | 24.35 | +0.13 |
| longbench | SUMMARIZATION | h2o | 552 | 1024 | 64 | 24.97 | 25.11 | +0.13 |
| longbench | SUMMARIZATION | snapkv | 732 | 128 | 64 | 21.03 | 21.15 | +0.12 |
| longbench | SUMMARIZATION | snapkv | 732 | 256 | 64 | 22.30 | 22.41 | +0.11 |
| longbench | SUMMARIZATION | snapkv | 732 | 512 | 64 | 23.44 | 23.71 | +0.27 |
| longbench | SUMMARIZATION | snapkv | 732 | 1024 | 64 | 24.85 | 25.10 | +0.26 |
| ruler | RULER_ALL | h2o | 2180 | 128 | 64 | 12.19 | 12.22 | +0.03 |
| ruler | RULER_ALL | h2o | 2180 | 1024 | 16 | 44.35 | 53.42 | +9.07 |
| ruler | RULER_ALL | h2o | 2180 | 1536 | 16 | 53.39 | 70.88 | +17.49 |
| ruler | RULER_ALL | h2o | 2180 | 2048 | 64 | 62.82 | 88.31 | +25.49 |
| ruler | RULER_ALL | snapkv | 1756 | 64 | 16 | 34.64 | 44.99 | +10.35 |
| ruler | RULER_ALL | snapkv | 1756 | 128 | 64 | 51.56 | 58.37 | +6.80 |
| ruler | RULER_ALL | snapkv | 1756 | 256 | 64 | 68.06 | 72.28 | +4.21 |
| ruler | RULER_ALL | snapkv | 1756 | 512 | 16 | 78.62 | 81.76 | +3.14 |
| ruler | RULER_ALL | snapkv | 1756 | 1024 | 16 | 85.67 | 91.46 | +5.79 |
| ruler | RULER_ALL | snapkv | 1756 | 1536 | 16 | 88.62 | 98.35 | +9.73 |
| ruler | RULER_ALL | snapkv | 1756 | 2048 | 16 | 92.93 | 98.91 | +5.98 |

**Summary per (category, method)**

| Benchmark | Category | Method | Natural avg budget | Budgets where winner > uniform | Mean Δ |
|---|---|---|---|---|---|
| longbench | CODE | h2o | 2456 | 3/4 | +0.54 |
| longbench | CODE | snapkv | 430 | 4/4 | +1.66 |
| longbench | MULTI_DOCUMENT_QA | h2o | 448 | 3/4 | +0.55 |
| longbench | MULTI_DOCUMENT_QA | snapkv | 274 | 3/4 | +0.32 |
| longbench | SINGLE_DOCUMENT_QA | h2o | 518 | 3/4 | +0.66 |
| longbench | SINGLE_DOCUMENT_QA | snapkv | 506 | 3/4 | +0.04 |
| longbench | SUMMARIZATION | h2o | 552 | 4/4 | +0.11 |
| longbench | SUMMARIZATION | snapkv | 732 | 4/4 | +0.19 |
| ruler | RULER_ALL | h2o | 2180 | 4/4 | +13.02 |
| ruler | RULER_ALL | snapkv | 1756 | 7/7 | +6.57 |

**Overall: rescaled winner beats uniform at 38/43 (category, method, budget) cells.**
