## A5 — Calibration-vs-test gap

Calibration = score during search (10% subsample, `NAS_SAMPLE_RATIO=0.1`); test = full-data (`sample_ratio=1.0`) re-eval of the same config.

| Benchmark | Category | Budget | Method | Floor | Mean gap (calib − test) | Kendall τ (calib vs test ranking) | Calib-picked config | Its test score | Test-best config | Its test score | Regret |
|---|---|---|---|---|---|---|---|---|---|---|---|
| longbench | CODE | 128 | h2o | 64 | +2.86 | +0.00 | random | 46.41 | bo | 47.13 | 0.73 |
| longbench | CODE | 128 | snapkv | 64 | +6.94 | +0.40 | bo | 56.09 | bo | 56.09 | 0.00 |
| longbench | CODE | 256 | h2o | 64 | +3.94 | +0.20 | random | 50.31 | winner | 50.59 | 0.28 |
| longbench | CODE | 256 | snapkv | 64 | +6.64 | +0.00 | random | 55.99 | winner | 57.33 | 1.34 |
| longbench | CODE | 512 | h2o | 64 | +3.48 | -0.60 | random | 52.52 | heuristic | 54.51 | 1.99 |
| longbench | CODE | 512 | snapkv | 64 | +5.23 | -0.20 | bo | 55.66 | winner | 58.16 | 2.50 |
| longbench | CODE | 1024 | h2o | 64 | +4.95 | +0.00 | heuristic | 55.45 | random | 57.23 | 1.78 |
| longbench | CODE | 1024 | snapkv | 64 | +5.13 | +0.40 | random | 58.91 | random | 58.91 | 0.00 |
| longbench | MULTI_DOCUMENT_QA | 128 | h2o | 64 | +7.29 | -0.80 | bo | 31.00 | uniform | 32.57 | 1.57 |
| longbench | MULTI_DOCUMENT_QA | 128 | snapkv | 64 | +7.36 | -0.80 | bo | 34.30 | winner | 35.02 | 0.72 |
| longbench | MULTI_DOCUMENT_QA | 256 | h2o | 64 | +8.40 | +0.00 | bo | 32.76 | random | 32.92 | 0.16 |
| longbench | MULTI_DOCUMENT_QA | 256 | snapkv | 64 | +7.46 | -0.11 | bo | 35.22 | winner | 36.31 | 1.09 |
| longbench | MULTI_DOCUMENT_QA | 512 | h2o | 64 | +7.56 | -0.40 | random | 32.94 | winner | 34.33 | 1.39 |
| longbench | MULTI_DOCUMENT_QA | 512 | snapkv | 64 | +7.34 | -0.33 | random | 35.55 | uniform | 35.77 | 0.21 |
| longbench | MULTI_DOCUMENT_QA | 1024 | h2o | 64 | +8.23 | +0.80 | bo | 34.93 | bo | 34.93 | 0.00 |
| longbench | MULTI_DOCUMENT_QA | 1024 | snapkv | 64 | +6.90 | -0.11 | bo | 35.88 | winner | 36.26 | 0.38 |
| longbench | SINGLE_DOCUMENT_QA | 128 | h2o | 64 | +3.74 | +0.56 | random | 28.32 | random | 28.32 | 0.00 |
| longbench | SINGLE_DOCUMENT_QA | 128 | snapkv | 64 | +3.42 | +0.40 | bo | 33.45 | heuristic | 33.67 | 0.22 |
| longbench | SINGLE_DOCUMENT_QA | 256 | h2o | 64 | +3.46 | -0.20 | bo | 30.09 | random | 30.92 | 0.83 |
| longbench | SINGLE_DOCUMENT_QA | 256 | snapkv | 64 | +4.52 | +0.80 | uniform | 35.25 | uniform | 35.25 | 0.00 |
| longbench | SINGLE_DOCUMENT_QA | 512 | h2o | 64 | +2.74 | -0.40 | bo | 32.07 | heuristic | 32.80 | 0.73 |
| longbench | SINGLE_DOCUMENT_QA | 512 | snapkv | 64 | +3.65 | +0.40 | random | 35.28 | winner | 36.33 | 1.04 |
| longbench | SINGLE_DOCUMENT_QA | 1024 | h2o | 64 | +2.38 | -0.40 | random | 33.50 | heuristic | 34.69 | 1.20 |
| longbench | SINGLE_DOCUMENT_QA | 1024 | snapkv | 64 | +3.21 | +0.00 | random | 37.01 | random | 37.01 | 0.00 |
| longbench | SUMMARIZATION | 128 | h2o | 64 | -0.01 | +0.60 | random | 22.05 | bo | 22.31 | 0.26 |
| longbench | SUMMARIZATION | 128 | snapkv | 64 | +0.23 | -0.40 | random | 20.89 | winner | 21.15 | 0.26 |
| longbench | SUMMARIZATION | 256 | h2o | 64 | +0.20 | +0.00 | uniform | 23.13 | random | 23.33 | 0.20 |
| longbench | SUMMARIZATION | 512 | h2o | 64 | +0.48 | +0.00 | random | 24.21 | winner | 24.35 | 0.14 |
| longbench | SUMMARIZATION | 1024 | h2o | 64 | +0.55 | +0.60 | random | 25.29 | heuristic | 25.32 | 0.03 |
| ruler | RULER_ALL | 128 | h2o | 64 | +1.30 | +0.60 | bo | 15.39 | bo | 15.39 | 0.00 |
| ruler | RULER_ALL | 128 | snapkv | 64 | -0.01 | +1.00 | winner | 58.37 | winner | 58.37 | 0.00 |
| ruler | RULER_ALL | 256 | snapkv | 64 | -0.37 | +1.00 | winner | 72.28 | winner | 72.28 | 0.00 |
| ruler | RULER_ALL | 1024 | h2o | 16 | -0.16 | +1.00 | bo | 62.52 | bo | 62.52 | 0.00 |
| ruler | RULER_ALL | 1024 | snapkv | 16 | -0.25 | +1.00 | bo | 93.80 | bo | 93.80 | 0.00 |
| ruler | RULER_ALL | 1536 | h2o | 16 | -1.01 | +0.67 | bo | 86.05 | bo | 86.05 | 0.00 |
| ruler | RULER_ALL | 1536 | snapkv | 16 | +0.07 | +1.00 | winner | 98.35 | winner | 98.35 | 0.00 |
| ruler | RULER_ALL | 2048 | h2o | 64 | -0.07 | +1.00 | bo | 96.14 | bo | 96.14 | 0.00 |
| ruler | RULER_ALL | 2048 | snapkv | 16 | -0.18 | +1.00 | winner | 98.91 | winner | 98.91 | 0.00 |

**Aggregate**

| Benchmark | Method | Cells | Mean gap | Mean Kendall τ | Calib picks test-best | Mean regret |
|---|---|---|---|---|---|---|
| longbench | h2o | 16 | +3.77 | -0.00 | 2/16 | 0.71 |
| longbench | snapkv | 13 | +5.23 | +0.03 | 4/13 | 0.60 |
| ruler | h2o | 4 | +0.09 | +0.82 | 4/4 | 0.00 |
| ruler | snapkv | 5 | -0.16 | +1.00 | 5/5 | 0.00 |

## B4 — NAS vs uniform, per cell (full-data scores)

| Benchmark | Category | Budget | Method | Floor | Uniform | Best non-uniform | Best label | Δ vs uniform | NAS wins? |
|---|---|---|---|---|---|---|---|---|---|
| longbench | CODE | 128 | h2o | 64 | 45.96 | 47.13 | bo | +1.17 | yes |
| longbench | CODE | 128 | snapkv | 64 | 54.81 | 56.09 | bo | +1.28 | yes |
| longbench | CODE | 256 | h2o | 64 | 49.49 | 50.59 | winner | +1.10 | yes |
| longbench | CODE | 256 | snapkv | 64 | 55.67 | 57.33 | winner | +1.66 | yes |
| longbench | CODE | 512 | h2o | 64 | 52.81 | 54.51 | heuristic | +1.70 | yes |
| longbench | CODE | 512 | snapkv | 64 | 56.73 | 58.16 | winner | +1.43 | yes |
| longbench | CODE | 1024 | h2o | 64 | 56.92 | 57.23 | random | +0.30 | yes |
| longbench | CODE | 1024 | snapkv | 64 | 56.02 | 58.91 | random | +2.89 | yes |
| longbench | MULTI_DOCUMENT_QA | 128 | h2o | 64 | 32.57 | 32.16 | winner | -0.41 | **no** |
| longbench | MULTI_DOCUMENT_QA | 128 | snapkv | 64 | 34.82 | 35.02 | winner | +0.20 | yes |
| longbench | MULTI_DOCUMENT_QA | 256 | h2o | 64 | 32.45 | 32.92 | random | +0.47 | yes |
| longbench | MULTI_DOCUMENT_QA | 256 | snapkv | 64 | 35.60 | 36.31 | winner | +0.71 | yes |
| longbench | MULTI_DOCUMENT_QA | 512 | h2o | 64 | 32.98 | 34.33 | winner | +1.35 | yes |
| longbench | MULTI_DOCUMENT_QA | 512 | snapkv | 64 | 35.77 | 35.73 | winner | -0.04 | **no** |
| longbench | MULTI_DOCUMENT_QA | 1024 | h2o | 64 | 33.54 | 34.93 | bo | +1.39 | yes |
| longbench | MULTI_DOCUMENT_QA | 1024 | snapkv | 64 | 35.87 | 36.26 | winner | +0.39 | yes |
| longbench | SINGLE_DOCUMENT_QA | 128 | h2o | 64 | 28.21 | 29.72 | winner | +1.51 | yes |
| longbench | SINGLE_DOCUMENT_QA | 128 | snapkv | 64 | 32.97 | 33.67 | heuristic | +0.70 | yes |
| longbench | SINGLE_DOCUMENT_QA | 256 | h2o | 64 | 29.96 | 30.92 | random | +0.96 | yes |
| longbench | SINGLE_DOCUMENT_QA | 256 | snapkv | 64 | 35.25 | 34.51 | random | -0.74 | **no** |
| longbench | SINGLE_DOCUMENT_QA | 512 | h2o | 64 | 32.41 | 32.80 | heuristic | +0.39 | yes |
| longbench | SINGLE_DOCUMENT_QA | 512 | snapkv | 64 | 35.97 | 36.33 | winner | +0.36 | yes |
| longbench | SINGLE_DOCUMENT_QA | 1024 | h2o | 64 | 33.60 | 34.69 | heuristic | +1.09 | yes |
| longbench | SINGLE_DOCUMENT_QA | 1024 | snapkv | 64 | 36.44 | 37.01 | random | +0.57 | yes |
| longbench | SUMMARIZATION | 128 | h2o | 64 | 21.88 | 22.31 | bo | +0.44 | yes |
| longbench | SUMMARIZATION | 128 | snapkv | 64 | 21.03 | 21.15 | winner | +0.12 | yes |
| longbench | SUMMARIZATION | 256 | h2o | 64 | 23.13 | 23.33 | random | +0.20 | yes |
| longbench | SUMMARIZATION | 512 | h2o | 64 | 24.22 | 24.35 | winner | +0.13 | yes |
| longbench | SUMMARIZATION | 1024 | h2o | 64 | 24.97 | 25.32 | heuristic | +0.34 | yes |
| ruler | RULER_ALL | 128 | h2o | 64 | 12.19 | 15.39 | bo | +3.19 | yes |
| ruler | RULER_ALL | 128 | snapkv | 64 | 51.56 | 58.37 | winner | +6.80 | yes |
| ruler | RULER_ALL | 256 | snapkv | 64 | 68.06 | 72.28 | winner | +4.21 | yes |
| ruler | RULER_ALL | 1024 | h2o | 16 | 44.35 | 62.52 | bo | +18.17 | yes |
| ruler | RULER_ALL | 1024 | snapkv | 16 | 85.67 | 93.80 | bo | +8.13 | yes |
| ruler | RULER_ALL | 1536 | h2o | 16 | 53.39 | 86.05 | bo | +32.66 | yes |
| ruler | RULER_ALL | 1536 | snapkv | 16 | 88.62 | 98.35 | winner | +9.73 | yes |
| ruler | RULER_ALL | 2048 | h2o | 64 | 62.82 | 96.14 | bo | +33.32 | yes |
| ruler | RULER_ALL | 2048 | snapkv | 16 | 92.93 | 98.91 | winner | +5.98 | yes |

**NAS beats uniform in 35/38 cells.**

**Which 5-way component is the overall best, and its mean gain over uniform**

| Component | # cells where it is overall best | Mean Δ vs uniform (all cells it appears in) | # cells |
|---|---|---|---|
| uniform | 3 | — | — |
| heuristic | 5 | +1.11 | 34 |
| winner | 15 | +2.64 | 38 |
| random | 6 | +2.16 | 37 |
| bo | 9 | +2.62 | 36 |

**Same, longbench only**

| Component | # cells overall best | Mean Δ vs uniform | Median Δ vs uniform |
|---|---|---|---|
| uniform | 3 | — | — |
| heuristic | 5 | +0.23 | +0.12 |
| winner | 11 | +0.54 | +0.41 |
| random | 6 | +0.15 | +0.13 |
| bo | 4 | -0.20 | -0.26 |

**Same, ruler only**

| Component | # cells overall best | Mean Δ vs uniform | Median Δ vs uniform |
|---|---|---|---|
| uniform | 0 | — | — |
| heuristic | 0 | +6.21 | -0.11 |
| winner | 4 | +9.40 | +6.80 |
| random | 0 | +9.43 | +8.24 |
| bo | 5 | +14.32 | +8.13 |
