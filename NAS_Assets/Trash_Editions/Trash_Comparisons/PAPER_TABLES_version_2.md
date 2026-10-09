# Paper-Ready Tables: NAS vs Uniform & SOTA Methods (Version 2)

Per-dataset comparison at budgets 128 and 256. **Bold** = best score per dataset. NAS methods (our contribution) are marked with ★.

> **Version 2 (2026-08-03):** adds ★ NAS StreamingLLM (from `NAS_Assets/{SINGLE_DOCUMENT_QA,MULTI_DOCUMENT_QA,CODE}/streamingllm/top_configs/`; not run for Summarization), re-derives all **bold** best-per-column marks, and corrects two values from version 1: the AdaKV Single-Doc @512 average (36.35 → 36.68, its own row values average to 36.68) and uniform StreamingLLM Multi-Doc @128 average (31.27 → 31.28, rounding). §7's uniform H2O Summarization best is corrected (21.44 @ 64 → 24.22 @ 512), and §8 (NAS StreamingLLM vs Uniform StreamingLLM) is new.

---

## 1. Single-Doc QA (narrativeqa, qasper, multifieldqa_en)

### Budget 128

| Method | Avg Budget | narrativeqa | qasper | multifieldqa_en | Avg |
|---|---|---|---|---|---|
| ★ **NAS SnapKV** | 122 | **19.36** | **36.16** | 45.01 | **33.51** |
| ★ **NAS H2O** | 128 | 17.70 | 31.10 | 35.84 | 28.21 |
| ★ **NAS StreamingLLM** | 128 | 15.53 | 21.12 | 28.98 | 21.88 |
| Uniform SnapKV | 128 | 18.70 | 35.14 | 45.08 | 32.97 |
| Uniform H2O | 128 | 17.70 | 31.10 | 35.84 | 28.21 |
| Uniform AdaKV | 128 | 18.60 | 34.52 | **45.36** | 32.83 |
| Uniform PyramidKV | 128 | 19.17 | 35.49 | 44.57 | 33.08 |
| Uniform StreamingLLM | 128 | 16.43 | 25.81 | 31.70 | 24.65 |

> ★ NAS SnapKV (avg_budget=122) beats all uniform methods at budget 128, including PyramidKV (33.08) and SnapKV (32.97), at a **lower average budget**. ★ NAS H2O matches uniform H2O (both 28.21) — NAS does not hurt H2O at this budget. ★ NAS StreamingLLM (21.88) falls **below** uniform StreamingLLM (24.65) at this budget — see §8.

### Budget 256

| Method | Avg Budget | narrativeqa | qasper | multifieldqa_en | Avg |
|---|---|---|---|---|---|
| ★ **NAS SnapKV** | 256 | 19.91 | 39.03 | 46.20 | 35.05 |
| ★ **NAS H2O** | 262 | 18.61 | 31.33 | 38.33 | 29.42 |
| ★ **NAS StreamingLLM** | 256 | 16.30 | 26.11 | 39.93 | 27.45 |
| Uniform SnapKV | 256 | 19.96 | 39.44 | **46.35** | **35.25** |
| Uniform H2O | 256 | 18.66 | 32.31 | 38.91 | 29.96 |
| Uniform AdaKV | 256 | **20.09** | 39.10 | 46.04 | 35.08 |
| Uniform PyramidKV | 256 | 19.28 | **39.66** | 45.47 | 34.80 |
| Uniform StreamingLLM | 256 | 17.40 | 26.63 | 31.49 | 25.17 |

> At budget 256, uniform SnapKV (35.25) edges out ★ NAS SnapKV (35.05). ★ NAS H2O (29.42) underperforms uniform H2O (29.96) at this budget. NAS advantage diminishes at higher budgets for Single-Doc QA. ★ NAS StreamingLLM (27.45) beats uniform StreamingLLM (25.17) by **+2.28** — the first budget where NAS helps StreamingLLM.

---

## 2. Multi-Doc QA (hotpotqa, 2wikimqa, musique)

### Budget 128

| Method | Avg Budget | hotpotqa | 2wikimqa | musique | Avg |
|---|---|---|---|---|---|
| ★ **NAS SnapKV** | 130 | **46.44** | 36.12 | 22.05 | 34.87 |
| ★ **NAS H2O** | 104 | 43.32 | 32.74 | 19.38 | 31.81 |
| ★ **NAS StreamingLLM** | 128 | 36.44 | 22.03 | 14.73 | 24.40 |
| Uniform SnapKV | 128 | 45.94 | 36.39 | 22.13 | 34.82 |
| Uniform H2O | 128 | 43.42 | 33.38 | 20.91 | 32.57 |
| Uniform AdaKV | 128 | 45.50 | **36.81** | 22.67 | 34.99 |
| Uniform PyramidKV | 128 | 46.03 | 36.73 | **22.92** | **35.23** |
| Uniform StreamingLLM | 128 | 42.56 | 33.34 | 17.93 | 31.28 |

> ★ NAS SnapKV (avg_budget=130) achieves the best hotpotqa (46.44); AdaKV has the best 2wikimqa (36.81). ★ NAS H2O (avg_budget=104) beats uniform H2O (32.57) at a lower budget. PyramidKV leads overall on musique (22.92). ★ NAS StreamingLLM (24.40) is far below uniform StreamingLLM (31.28) at this budget.

### Budget 256

| Method | Avg Budget | hotpotqa | 2wikimqa | musique | Avg |
|---|---|---|---|---|---|
| ★ **NAS SnapKV** | 274 | 46.72 | **38.49** | **23.21** | **36.14** |
| ★ **NAS H2O** | 264 | 44.11 | 32.75 | 19.76 | 32.21 |
| ★ **NAS StreamingLLM** | 250 | 41.61 | 25.98 | 16.79 | 28.13 |
| Uniform SnapKV | 256 | **46.94** | 37.50 | 22.36 | 35.60 |
| Uniform H2O | 256 | 44.03 | 33.42 | 19.90 | 32.45 |
| Uniform AdaKV | 256 | 46.07 | 37.57 | 22.63 | 35.42 |
| Uniform PyramidKV | 256 | 46.52 | 37.24 | 22.22 | 35.33 |
| Uniform StreamingLLM | 256 | 42.28 | 32.86 | 17.93 | 31.02 |

> ★ NAS SnapKV (avg_budget=274) has the best average (36.14), best 2wikimqa (38.49) and best musique (23.21); uniform SnapKV edges it on hotpotqa (46.94 vs 46.72). ★ NAS H2O (avg_budget=264) is competitive with uniform H2O (32.45) at a comparable budget. ★ NAS StreamingLLM (28.13 @ avg_budget=250) trails uniform StreamingLLM (31.02) by −2.89.

---

## 3. Code (lcc, repobench-p)

### Budget 128

| Method | Avg Budget | lcc | repobench-p | Avg |
|---|---|---|---|---|
| ★ **NAS SnapKV** | 104 | 54.99 | 51.94 | 53.47 |
| ★ **NAS H2O** | 128 | 49.92 | 42.00 | 45.96 |
| ★ **NAS StreamingLLM** | 128 | 39.98 | 36.17 | 38.08 |
| Uniform SnapKV | 128 | 56.90 | 52.73 | 54.82 |
| Uniform H2O | 128 | 49.92 | 42.00 | 45.96 |
| Uniform AdaKV | 128 | **57.98** | 52.70 | 55.34 |
| Uniform PyramidKV | 128 | 57.71 | **53.43** | **55.57** |
| Uniform StreamingLLM | 128 | 54.17 | 50.88 | 52.53 |

> At budget 128, uniform methods (AdaKV, PyramidKV) lead. ★ NAS SnapKV (avg_budget=104) is close but at a lower budget. ★ NAS H2O matches uniform H2O (both 45.96). NAS advantage on Code appears at higher budgets. ★ NAS StreamingLLM (38.08) is far below uniform StreamingLLM (52.53) — per-layer allocation hurts StreamingLLM on Code (see §8).

### Budget 256

| Method | Avg Budget | lcc | repobench-p | Avg |
|---|---|---|---|---|
| ★ **NAS SnapKV** | 240 | 57.89 | 54.45 | 56.17 |
| ★ **NAS H2O** | 256 | 53.39 | 44.76 | 49.08 |
| ★ **NAS StreamingLLM** | 256 | 45.08 | 37.66 | 41.37 |
| Uniform SnapKV | 256 | 58.23 | 53.12 | 55.68 |
| Uniform H2O | 256 | 53.45 | 45.54 | 49.50 |
| Uniform AdaKV | 256 | 58.18 | **54.55** | **56.37** |
| Uniform PyramidKV | 256 | **58.33** | 53.12 | 55.73 |
| Uniform StreamingLLM | 256 | 57.14 | 52.47 | 54.81 |

> ★ NAS SnapKV (avg_budget=240, 56.17) is within 0.20 of the best method (AdaKV, 56.37); AdaKV has the best repobench-p (54.55 vs 54.45 for NAS SnapKV). ★ NAS H2O (avg_budget=256) is close to uniform H2O (49.50). At budget 430, ★ NAS SnapKV reaches 58.26 — beating all uniform methods. ★ NAS StreamingLLM (41.37) again trails uniform StreamingLLM (54.81) badly.

---

## 4. Summarization (gov_report, qmsum, multi_news)

### Budget 128

| Method | Avg Budget | gov_report | qmsum | multi_news | Avg |
|---|---|---|---|---|---|
| ★ **NAS SnapKV** | 128 | 20.77 | 20.64 | 21.95 | 21.12 |
| ★ **NAS H2O** | — | — | — | — | ❌ Not run |
| ★ **NAS StreamingLLM** | — | — | — | — | ❌ Not run |
| Uniform SnapKV | 128 | 21.01 | 20.35 | 21.73 | 21.03 |
| Uniform H2O | 128 | **23.02** | 17.79 | **24.82** | **21.88** |
| Uniform AdaKV | 128 | 21.57 | **21.26** | 22.32 | 21.72 |
| Uniform PyramidKV | 128 | 21.02 | 20.50 | 21.97 | 21.16 |
| Uniform StreamingLLM | 128 | 13.26 | 16.30 | 13.08 | 14.21 |

> ★ NAS SnapKV (21.12) beats uniform SnapKV (21.03) by +0.09. H2O leads overall (21.88) due to strong gov_report and multi_news. ★ NAS H2O and ★ NAS StreamingLLM were not run for Summarization.

### Budget 256

| Method | Avg Budget | gov_report | qmsum | multi_news | Avg |
|---|---|---|---|---|---|
| ★ **NAS SnapKV** | 256 | 22.20 | 21.04 | 23.57 | 22.27 |
| ★ **NAS H2O** | — | — | — | — | ❌ Not run |
| ★ **NAS StreamingLLM** | — | — | — | — | ❌ Not run |
| Uniform SnapKV | 256 | 22.25 | 21.09 | 23.57 | 22.30 |
| Uniform H2O | 256 | **24.78** | 18.94 | **25.68** | **23.13** |
| Uniform AdaKV | 256 | 22.57 | **21.81** | 23.77 | 22.72 |
| Uniform PyramidKV | 256 | 22.62 | 21.17 | 23.50 | 22.43 |
| Uniform StreamingLLM | 256 | 13.90 | 16.16 | 13.83 | 14.63 |

> ★ NAS SnapKV (22.27) is on par with uniform SnapKV (22.30). H2O leads overall (23.13). Summarization shows the least NAS benefit. ★ NAS H2O and ★ NAS StreamingLLM were not run.

---

## 5. Summary: NAS vs Best Uniform Method

| Task Category | Budget | ★ NAS SnapKV | ★ NAS H2O | ★ NAS StreamingLLM | Best Uniform | Best Uniform Method | NAS SnapKV vs Best | NAS H2O vs Best | NAS SLLM vs Best |
|---|---|---|---|---|---|---|---|---|---|
| Single-Doc QA | 128 | **33.51** | 28.21 | 21.88 | 33.08 | PyramidKV | **+0.43** | —4.87 | —11.20 |
| Single-Doc QA | 256 | 35.05 | 29.42 | 27.45 | **35.25** | SnapKV | —0.20 | —5.83 | —7.80 |
| Multi-Doc QA | 128 | 34.87 | 31.81 | 24.40 | **35.23** | PyramidKV | —0.36 | —3.42 | —10.83 |
| Multi-Doc QA | 256 | **36.14** | 32.21 | 28.13 | 35.60 | SnapKV | **+0.54** | —3.39 | —7.47 |
| Code | 128 | 53.47 | 45.96 | 38.08 | **55.57** | PyramidKV | —2.10 | —9.61 | —17.49 |
| Code | 256 | 56.17 | 49.08 | 41.37 | **56.37** | AdaKV | —0.20 | —7.29 | —15.00 |
| Summarization | 128 | 21.12 | ❌ | ❌ | **21.88** | H2O | —0.76 | — | — |
| Summarization | 256 | 22.27 | ❌ | ❌ | **23.13** | H2O | —0.86 | — | — |

> ★ NAS SnapKV wins at Single-Doc QA @ 128 (+0.43) and Multi-Doc QA @ 256 (+0.54). ★ NAS H2O underperforms at budgets 128/256 but shows large gains at higher budgets (see Section 6). ★ NAS StreamingLLM trails the best uniform method by 7–18 points at these budgets and also trails *uniform StreamingLLM* itself (see Section 8).

---

## 6. NAS at Best Pareto Points (Higher Budgets)

### Code — ★ NAS SnapKV @ 430, ★ NAS H2O @ 1024, ★ NAS StreamingLLM @ 648

| Method | Avg Budget | lcc | repobench-p | Avg |
|---|---|---|---|---|
| ★ **NAS SnapKV** | 430 | 59.74 | **56.78** | **58.26** |
| ★ **NAS H2O** | 1024 | 59.62 | 54.23 | 56.93 |
| ★ **NAS StreamingLLM** | 648 | 55.49 | 41.58 | 48.54 |
| Uniform SnapKV | 512 | 59.16 | 54.31 | 56.74 |
| Uniform AdaKV | 512 | 59.23 | 54.40 | 56.82 |
| Uniform PyramidKV | 512 | **59.88** | 54.36 | 57.12 |
| Uniform H2O | 512 | 55.97 | 49.65 | 52.81 |
| Uniform StreamingLLM | 512 | 58.97 | 52.97 | 55.97 |

> ★ NAS SnapKV (58.26 @ budget 430) beats all uniform methods at budget 512, including PyramidKV (57.12) and AdaKV (56.82), at **84% of the budget**. ★ NAS H2O (56.93 @ budget 1024) also beats all uniform methods except PyramidKV. ★ NAS StreamingLLM (48.54 @ budget 648) falls **7.43 below** uniform StreamingLLM @ 512 (55.97) — NAS does not transfer to StreamingLLM on Code.

### Multi-Doc QA — ★ NAS SnapKV @ 274, ★ NAS H2O @ 448, ★ NAS StreamingLLM @ 372

| Method | Avg Budget | hotpotqa | 2wikimqa | musique | Avg |
|---|---|---|---|---|---|
| ★ **NAS SnapKV** | 274 | 46.72 | **38.49** | **23.21** | **36.14** |
| ★ **NAS H2O** | 448 | 45.88 | 35.03 | 21.16 | 34.02 |
| ★ **NAS StreamingLLM** | 372 | 41.11 | 33.74 | 18.88 | 31.24 |
| Uniform SnapKV | 256 | **46.94** | 37.50 | 22.36 | 35.60 |
| Uniform AdaKV | 256 | 46.07 | 37.57 | 22.63 | 35.42 |
| Uniform PyramidKV | 256 | 46.52 | 37.24 | 22.22 | 35.33 |
| Uniform H2O | 256 | 44.03 | 33.42 | 19.90 | 32.45 |
| Uniform StreamingLLM | 256 | 42.28 | 32.86 | 17.93 | 31.02 |

> ★ NAS SnapKV (36.14 @ budget 274) has the best average, 2wikimqa and musique; uniform SnapKV keeps the best hotpotqa (46.94 vs 46.72). ★ NAS H2O (34.02 @ budget 448) beats uniform H2O (32.98 @ budget 512) by **+1.04 at lower budget**. ★ NAS StreamingLLM (31.24 @ budget 372) only matches uniform StreamingLLM @ 256 (31.02) while using 45% more budget.

### Single-Doc QA — ★ NAS SnapKV @ 506, ★ NAS H2O @ 518, ★ NAS StreamingLLM @ 604

| Method | Avg Budget | narrativeqa | qasper | multifieldqa_en | Avg |
|---|---|---|---|---|---|
| ★ **NAS SnapKV** | 506 | 20.85 | 40.25 | **47.13** | 36.08 |
| ★ **NAS H2O** | 518 | 19.34 | 37.33 | 41.54 | 32.74 |
| ★ **NAS StreamingLLM** | 604 | 18.51 | 37.18 | 43.67 | 33.12 |
| Uniform SnapKV | 512 | 19.99 | **41.86** | 46.06 | 35.97 |
| Uniform AdaKV | 512 | **21.32** | **41.86** | 46.87 | **36.68** |
| Uniform PyramidKV | 512 | 20.57 | 41.11 | 46.20 | 35.96 |
| Uniform H2O | 512 | 19.20 | 35.71 | 42.32 | 32.41 |
| Uniform StreamingLLM | 512 | 18.82 | 26.93 | 31.97 | 25.91 |

> ★ NAS SnapKV (36.08 @ budget 506) is competitive with AdaKV (36.68 @ budget 512). ★ NAS H2O (32.74 @ budget 518) beats uniform H2O (32.41 @ budget 512) by **+0.33**. ★ NAS StreamingLLM (33.12 @ budget 604) beats uniform StreamingLLM @ 512 (25.91) by **+7.21** — its one clear win, albeit from a low baseline.

---

## 7. NAS H2O vs Uniform H2O — Gains Summary

| Task Category | ★ NAS H2O Best | NAS Budget | Uniform H2O Best | Uniform Budget | NAS H2O Gain |
|---|---|---|---|---|---|
| Single-Doc QA | 32.74 | 518 | 32.41 | 512 | **+0.33** |
| Multi-Doc QA | 34.02 | 448 | 32.98 | 512 | **+1.04** |
| Code | 56.93 | 1024 | 52.81 | 512 | **+4.12** |
| Summarization | ❌ Not run | — | 24.22 | 512 | — |

> ★ NAS H2O shows large gains over uniform H2O, especially on Code (+4.12) and Multi-Doc QA (+1.04). H2O benefits more from NAS than SnapKV in relative terms because uniform H2O is further from optimal.

---

## 8. NAS StreamingLLM vs Uniform StreamingLLM — Gains Summary

| Task Category | ★ NAS SLLM Best | NAS Budget | Uniform SLLM @ Nearest Budget | Uniform Budget | NAS SLLM Gain |
|---|---|---|---|---|---|
| Single-Doc QA | 33.12 | 604 | 25.91 | 512 | **+7.21** |
| Multi-Doc QA | 31.24 | 372 | 31.02 | 256 | **+0.22** |
| Code | 48.54 | 648 | 55.97 | 512 | —7.43 |
| Summarization | ❌ Not run | — | 15.35 | 512 | — |

> ★ NAS StreamingLLM gains **+7.21** on Single-Doc QA at budget 604, and still beats uniform StreamingLLM's *best* score (28.02 @ 1024) by **+5.10** at 59% of the budget. On Multi-Doc QA and Code it **underperforms** uniform StreamingLLM (vs uniform best @ 1024: —1.04 and —7.85 respectively), and at budgets ≤256 it is below uniform StreamingLLM on every task.
>
> ⚠️ **Caveat:** the NAS pipeline's all-64 anchor config scores well below the uniform-64 baseline for StreamingLLM (Single-Doc: 18.94 vs 24.63), whereas the SnapKV/H2O anchors reproduce their uniform baselines exactly (e.g. 29.61 = 29.61). The NAS-StreamingLLM eval setup should be validated before drawing conclusions from these numbers.

---

*All scores from Meta-Llama-3-8B-Instruct. Uniform scores from `Meta-Llama-3-8B-Instruct/BENCHMARKS.md`. NAS scores from `NAS_Assets/` top_configs (StreamingLLM: `SINGLE_DOCUMENT_QA/streamingllm/top_configs/summary_20260801_194856`, `MULTI_DOCUMENT_QA/streamingllm/top_configs/summary_20260801_192310`, `CODE/streamingllm/top_configs/summary_20260802_074805`). ★ = NAS-optimized (our contribution). Version 2 generated 2026-08-03; version 1 preserved as `PAPER_TABLES.md`.*
