# Grouped-CMA-ES Ablation (EvolKV-style Reproduction) — SnapKV

Implements the core recipe of EvolKV (Xu et al., EMNLP Findings 2025) as a baseline
ablation for TODOS #38: group the 32 layers into `n_g = 8`-layer blocks (4 groups),
optimize each group's budget with real CMA-ES (the `cma` PyPI package) instead of our
MLP-surrogate + differential-evolution BO search, at a matched target average budget.
Script: `NAS_Assets/run_evolkv_reproduction.py`.

**Settings (all 6 runs):** `group_size=8` (4 groups/32 layers), `λ=0.3`, `γ=0.2`,
`σ₀=0.3`, `M=15` CMA-ES iterations per group, `calib_samples_total=30`. After the
per-group CMA-ES search, budgets are rescaled ("KV Budget Completion") to land the
32-layer average exactly on the target budget before final scoring.

**Grid:** SnapKV × {CODE, SINGLE_DOCUMENT_QA} × {128, 512, 1024} = 6 runs, all
completed 2026-09-12 (GPU2, `sravanth_logs/EVOLKV_GRID_10_09_2026.log`).

## Full-data re-evaluation (2026-09-29) — use THIS table, not the calibration one below

Each run's `completed_budgets` re-scored on the full test set (`sample_ratio=1.0`) with the
same scoring path as the Step-4 table (`NAS_Assets/eval_evolkv_repro_full_data.py`, results in
`NAS_Assets/<CATEGORY>/snapkv_evolkv_repro/B<budget>/full_data_eval_result.json`). Our columns
are the matching 5-way full-data configs (`ICLR_Final_Results/analysis_outputs/cells.csv`).

| Category | Budget | Uniform | EvolKV (grouped CMA-ES) | Ours: rescaled Step-2 winner | Ours: best BO | Ours: best of 5 † |
|---|---|---|---|---|---|---|
| CODE | 128 | 54.81 | 54.92 | **55.86** | 56.09 | 56.09 |
| CODE | 512 | 56.73 | 57.02 | **58.16** | 55.67 | 58.16 |
| CODE | 1024 | 56.02 | 57.20 | **58.52** | 57.91 | 58.91 |
| SINGLE_DOCUMENT_QA | 128 | 32.97 | 33.50 | **33.51** | 33.45 | 33.67 |
| SINGLE_DOCUMENT_QA | 512 | 35.97 | 36.28 | **36.33** | 35.13 | 36.33 |
| SINGLE_DOCUMENT_QA | 1024 | 36.44 | 36.40 | **36.46** | 35.26 | 37.01 |

- EvolKV beats uniform at 5/6 cells, but only by +0.1 to +1.2 — its calibration-only scores
  (63-66 on CODE, ~43 on SINGLE_DOC, table below) were inflated by +7 to +9 pts.
- **Our rescaled Step-2 winner (a single pre-committed config, no budget-specific search) is ≥
  EvolKV at 6/6 cells**: +0.94/+1.14/+1.32 on CODE, effectively tied on SINGLE_DOC (+0.01 to +0.06).
- Our best BO config is *below* EvolKV at 4/6 cells — consistent with
  `Analysis_Results.md` finding 3 (on LongBench, BO over-fits the noisy 10% calibration subsample).
- † Best-of-5 is selected on the full test data itself, so it is optimistically biased; the fair
  single-config comparison is the rescaled-winner column.

## EvolKV "search once, expand" variant (2026-09-30)

EvolKV's published protocol (Yu & Chai, Findings EMNLP 2025, Sec. 3.2 / Fig. 4b) optimizes once at
a source budget and extends the allocation to other targets by proportional rescaling ("KV Budget
Completion"), *without* re-running CMA-ES. The table above used their *direct* variant (fresh
search per budget) at every cell. This table adds the *expanded* variant — the B128 EvolKV
allocation (`snapkv_evolkv_repro/B128/result.json`'s `completed_budgets`) rescaled to B256/512/1024
with no further optimization — the correct like-for-like comparison against **our** rescaled
Step-2 winner, which is also search-once (`NAS_Assets/eval_evolkv_expansion.py`, results in
`NAS_Assets/<CATEGORY>/snapkv_evolkv_expanded/B<budget>/full_data_eval_result.json`).

| Category | Budget | Uniform | EvolKV (direct, per-budget search) | EvolKV (expanded from B128) | Ours: rescaled Step-2 winner |
|---|---|---|---|---|---|
| CODE | 256 | 55.67 | — | 55.99 | **57.33** |
| CODE | 512 | 56.73 | 57.02 | 56.82 | **58.16** |
| CODE | 1024 | 56.02 | 57.20 | 56.42 | **58.52** |
| SINGLE_DOCUMENT_QA | 256 | 35.25 | — | 35.43 | 34.51 |
| SINGLE_DOCUMENT_QA | 512 | 35.97 | 36.28 | 36.14 | **36.33** |
| SINGLE_DOCUMENT_QA | 1024 | 36.44 | 36.40 | 36.38 | **36.46** |

- The expanded variant tracks the direct variant closely (within 0.2-0.8 pts at B512/B1024) and
  both sit close to uniform — expanding without re-optimizing costs little relative to a fresh
  per-budget EvolKV search, which is expected since EvolKV's own ablations report low sensitivity
  to re-optimization at this scale.
- **Our rescaled winner is ≥ the expanded EvolKV variant at 5/6 cells** (+1.34 to +2.10 on CODE,
  +0.08 to +0.19 on SINGLE_DOCUMENT_QA B512/B1024), the one exception being SINGLE_DOCUMENT_QA
  B256, where our winner (34.51) trails both uniform (35.25) and expanded EvolKV (35.43) — see
  `Analysis_Results.md` B4 for the 3 cells where NAS underperforms uniform.
- No B128 row here: that's the existing *direct* EvolKV result (54.92 CODE / 33.50 SINGLE_DOC),
  since it's the source allocation being expanded, not a separate target.

**⚠️ Superseded below (kept for history): calibration-only EvolKV scores — NOT directly
comparable to `LONGBENCH_STEP4_Results.md` in absolute terms.** `final_task_score` below is
computed on each dataset's calibration subsample (`sample_ratio` scaled per-dataset
to hit `calib_samples_total=30`, the same scoring path used during the CMA-ES search
itself), not the full test set (`sample_ratio=1.0`) used throughout the Step-4 table.
The comparison columns below therefore show relative ranking / gap direction, not a
strict apples-to-apples delta — a full-data re-eval of each run's `G_best_budgets` on
`eval_top_configs_longbench.py --sample_ratio 1.0` would be needed for a rigorous
paper-table number. (GPU1/GPU2 are currently idle — this re-eval can be launched on
request.)

---

## Summary — grouped-CMA-ES vs. full per-layer NAS (Step 4)

Full per-layer NAS columns are full-data (`sample_ratio=1.0`) scores from
`LONGBENCH_STEP4_Results.md`, included for directional reference only (see caveat
above — different eval protocol).

```
┌─────────────────────┬────────┬───────────────────┬─────────────────┬──────────────────────┬───────────────────────┐
│ Category             │ Budget │ Grouped-CMA-ES     │ Full NAS Uniform │ Full NAS Best (any)  │ Full NAS Best BO      │
│                       │        │ (calib, this run)  │ (full data)      │ (full data)          │ (full data)           │
├─────────────────────┼────────┼───────────────────┼─────────────────┼──────────────────────┼───────────────────────┤
│ CODE                 │ 128    │ 63.80              │ 54.82            │ 56.10 (BO)           │ 56.10                 │
│ CODE                 │ 512    │ 65.30              │ 56.74            │ 58.17 (Winner)       │ 55.67                 │
│ CODE                 │ 1024   │ 66.34              │ 56.02            │ 58.91 (Random)       │ 57.91                 │
│ SINGLE_DOCUMENT_QA   │ 128    │ 43.31              │ 32.97            │ 33.67 (Heuristic)    │ 33.45                 │
│ SINGLE_DOCUMENT_QA   │ 512    │ 43.67              │ 35.97            │ 36.33 (Winner)       │ 35.13                 │
│ SINGLE_DOCUMENT_QA   │ 1024   │ 43.09              │ 36.44            │ 37.01 (Random)       │ 35.26                 │
└─────────────────────┴────────┴───────────────────┴─────────────────┴──────────────────────┴───────────────────────┘
```

Note the grouped-CMA-ES column sits well above the full-data columns for both
categories — consistent with calibration-subsample scores running optimistic
relative to full-data scores (smaller, potentially easier sample; same effect noted
elsewhere in this project whenever Step-1 fitness is compared to Step-2+ full-data
eval). Not evidence that grouped-CMA-ES beats the real per-layer NAS until re-run
on full data.

---

## Run details

```
┌─────────────────────┬────────┬────────────────┬──────────────┬───────────────┬──────────────┬───────────────┐
│ Category             │ Target │ Completed Avg  │ Final Task   │ Final Cache   │ Final        │ G_best        │
│                       │ Budget │ Budget         │ Score (calib)│ Score         │ Fitness      │ Fitness       │
├─────────────────────┼────────┼────────────────┼──────────────┼───────────────┼──────────────┼───────────────┤
│ CODE                 │ 128    │ 128.44         │ 63.80        │ 0.9966        │ 82.87        │ 84.48         │
│ CODE                 │ 512    │ 512.50         │ 65.30        │ 0.9990        │ 84.87        │ 87.09         │
│ CODE                 │ 1024   │ 1024.34        │ 66.34        │ 0.9997        │ 86.23        │ 86.55         │
│ SINGLE_DOCUMENT_QA   │ 128    │ 128.56         │ 43.31        │ 0.9956        │ 56.25        │ 57.83         │
│ SINGLE_DOCUMENT_QA   │ 512    │ 512.47         │ 43.67        │ 0.9991        │ 56.76        │ 59.15         │
│ SINGLE_DOCUMENT_QA   │ 1024   │ 1024.50        │ 43.09        │ 0.9995        │ 56.01        │ 58.12         │
└─────────────────────┴────────┴────────────────┴──────────────┴───────────────┴──────────────┴───────────────┘
```

`Final Fitness` = post budget-completion-rescale fitness (`f(S) + cache_score` blend,
per EvolKV's objective); `G_best Fitness` is the CMA-ES search's own best fitness
*before* the final rescale-to-exact-target-budget step, so it is not directly the
same quantity as `Final Fitness` — expected to differ slightly given the rescale
nudges every layer's budget.

Per-layer `G_best_budgets`/`completed_budgets` (32 values each) are stored in the
source `result.json` files:
`NAS_Assets/<CATEGORY>/snapkv_evolkv_repro/B<budget>/result.json`.

---

## Status

All 6 planned runs complete, and full-data re-evaluation done 2026-09-29 (table at top).
Remaining open decision: extend the grid to MULTI_DOCUMENT_QA / SUMMARIZATION or to H2O,
or keep the ablation scoped to this 2-category/3-budget SnapKV grid.
