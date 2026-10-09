# LongBench Step-4 (Budget-Constrained Slice NAS) Results — SnapKV

Legend for dataset abbreviations used in the per-dataset tables below:
`SINGLE_DOCUMENT_QA: nqa=narrativeqa, qas=qasper, mfqa=multifieldqa_en` · `MULTI_DOCUMENT_QA: hqa=hotpotqa, 2wm=2wikimqa, msq=musique` · `CODE: lcc=lcc, rbp=repobench-p`

All scores are the per-dataset LongBench metric (F1/ROUGE per the standard LongBench scoring script) on the full dataset (`--sample_ratio 1.0`), mean over each category's 3 (or 2, for CODE) datasets = the summary score below.

This is Step 4 only (the budget-constrained slice search — LAMP.py run with `NAS_TARGET_BUDGET` pinned to each budget below), evaluated on real full data, **not** Step 1's calibration-subsample fitness. Each category/budget's `output.txt` was seeded with the same 7 shape anchors used throughout this project (uniform, 2 ramps, 2 triangles, alternating, and the category's own unconstrained-search winner shape) plus 57 LHS random points, then real BO search on top.

**Methodology note — this table's "Best BO" is genuinely isolated, unlike the equivalent RULER tables.** `RULER_Results.md` documents a real issue where SnapKV/H2O's "Best BO" column there is actually `best_overall` (the automated pipeline's argmin across *all* rows, not restricted to the true BO-search rows) — verified to be mislabeled in 2 of 6 checked cases. This table does not have that problem: every row here was selected with `NAS_Assets/select_5way_snapshot.py`, which explicitly separates the 5 categories (`row 0` = uniform, `rows 1-5` = best heuristic, `row 6` = best winner-seed, `rows 7-63` = best random, `rows 64+` = best BO) from the start — so "Best BO" here is always genuinely sourced from the adaptive BO-search phase, not a coincidental overall-best pick from an earlier phase.

**Status: all 3 categories complete (all 4 budgets each) — SINGLE_DOCUMENT_QA, MULTI_DOCUMENT_QA, CODE.**

---

## SnapKV — SINGLE_DOCUMENT_QA

### Summary

```
┌────────┬─────────┬────────────────┬─────────────┬─────────────┬─────────┬───────────────────┬─────────────────────────┐
│ Budget │ Uniform │ Best Heuristic │ Best Winner │ Best Random │ Best BO │ Winner vs Uniform │ Best config             │
├────────┼─────────┼────────────────┼─────────────┼─────────────┼─────────┼───────────────────┼─────────────────────────┤
│ 128    │ 32.97   │ 33.67          │ 33.51       │ 33.38       │ 33.45   │ +0.54             │ Heuristic (+0.16 over winner) │
│ 256    │ 35.25   │ 33.83          │ 34.51       │ 34.51       │ 34.43   │ -0.74             │ Uniform (+0.74 over winner)   │
│ 512    │ 35.97   │ 35.61          │ 36.33       │ 35.28       │ 35.13   │ +0.36             │ Winner (+0.36 over uniform)   │
│ 1024   │ 36.44   │ 36.27          │ 36.46       │ 37.01       │ 35.26   │ +0.02             │ Random (+0.55 over winner)    │
└────────┴─────────┴────────────────┴─────────────┴─────────────┴─────────┴───────────────────┴─────────────────────────┘
```

### Per-dataset breakdown

```
-- Budget 128 --
┌────────────────┬───────┬───────┬───────┬───────┐
│ Config         │ nqa   │ qas   │ mfqa  │ Mean  │
├────────────────┼───────┼───────┼───────┼───────┤
│ Uniform        │ 18.70 │ 35.14 │ 45.08 │ 32.97 │
│ Best Heuristic │ 19.07 │ 35.76 │ 46.18 │ 33.67 │
│ Best Winner    │ 19.51 │ 34.86 │ 46.16 │ 33.51 │
│ Best Random    │ 19.04 │ 35.91 │ 45.20 │ 33.38 │
│ Best BO        │ 20.28 │ 35.28 │ 44.79 │ 33.45 │
└────────────────┴───────┴───────┴───────┴───────┘

-- Budget 256 --
┌────────────────┬───────┬───────┬───────┬───────┐
│ Config         │ nqa   │ qas   │ mfqa  │ Mean  │
├────────────────┼───────┼───────┼───────┼───────┤
│ Uniform        │ 19.96 │ 39.44 │ 46.35 │ 35.25 │
│ Best Heuristic │ 18.87 │ 37.30 │ 45.33 │ 33.83 │
│ Best Winner    │ 19.31 │ 38.30 │ 45.91 │ 34.51 │
│ Best Random    │ 19.21 │ 39.32 │ 45.01 │ 34.51 │
│ Best BO        │ 20.11 │ 37.82 │ 45.36 │ 34.43 │
└────────────────┴───────┴───────┴───────┴───────┘

-- Budget 512 --
┌────────────────┬───────┬───────┬───────┬───────┐
│ Config         │ nqa   │ qas   │ mfqa  │ Mean  │
├────────────────┼───────┼───────┼───────┼───────┤
│ Uniform        │ 19.99 │ 41.86 │ 46.06 │ 35.97 │
│ Best Heuristic │ 20.24 │ 39.68 │ 46.90 │ 35.61 │
│ Best Winner    │ 20.83 │ 40.29 │ 47.86 │ 36.33 │
│ Best Random    │ 19.41 │ 39.96 │ 46.48 │ 35.28 │
│ Best BO        │ 20.95 │ 38.36 │ 46.07 │ 35.13 │
└────────────────┴───────┴───────┴───────┴───────┘

-- Budget 1024 --
┌────────────────┬───────┬───────┬───────┬───────┐
│ Config         │ nqa   │ qas   │ mfqa  │ Mean  │
├────────────────┼───────┼───────┼───────┼───────┤
│ Uniform        │ 20.66 │ 42.64 │ 46.02 │ 36.44 │
│ Best Heuristic │ 20.73 │ 41.99 │ 46.09 │ 36.27 │
│ Best Winner    │ 20.96 │ 41.24 │ 47.18 │ 36.46 │
│ Best Random    │ 21.07 │ 41.90 │ 48.05 │ 37.01 │
│ Best BO        │ 20.56 │ 38.98 │ 46.25 │ 35.26 │
└────────────────┴───────┴───────┴───────┴───────┘
```

---

## SnapKV — MULTI_DOCUMENT_QA

### Summary

```
┌────────┬─────────┬────────────────┬─────────────┬─────────────┬─────────┬───────────────────┬─────────────────────────┐
│ Budget │ Uniform │ Best Heuristic │ Best Winner │ Best Random │ Best BO │ Winner vs Uniform │ Best config             │
├────────┼─────────┼────────────────┼─────────────┼─────────────┼─────────┼───────────────────┼─────────────────────────┤
│ 128    │ 34.82   │ 34.94          │ 35.02       │ 34.65       │ 34.30   │ +0.20             │ Winner (+0.20 over uniform)   │
│ 256    │ 35.60   │ 35.49          │ 36.31       │ 35.68       │ 35.22   │ +0.71             │ Winner (+0.71 over uniform)   │
│ 512    │ 35.77   │ 34.74          │ 35.73       │ 35.55       │ 35.34   │ -0.04             │ Uniform (+0.04 over winner)   │
│ 1024   │ 35.87   │ 36.04          │ 36.26       │ 36.14       │ 35.88   │ +0.39             │ Winner (+0.39 over uniform)   │
└────────┴─────────┴────────────────┴─────────────┴─────────────┴─────────┴───────────────────┴─────────────────────────┘
```

### Per-dataset breakdown

```
-- Budget 128 --
┌────────────────┬───────┬───────┬───────┬───────┐
│ Config         │ hqa   │ 2wm   │ msq   │ Mean  │
├────────────────┼───────┼───────┼───────┼───────┤
│ Uniform        │ 45.94 │ 36.39 │ 22.13 │ 34.82 │
│ Best Heuristic │ 46.69 │ 36.15 │ 21.98 │ 34.94 │
│ Best Winner    │ 46.02 │ 36.28 │ 22.77 │ 35.02 │
│ Best Random    │ 45.95 │ 35.49 │ 22.50 │ 34.65 │
│ Best BO        │ 44.79 │ 35.51 │ 22.61 │ 34.30 │
└────────────────┴───────┴───────┴───────┴───────┘

-- Budget 256 --
┌────────────────┬───────┬───────┬───────┬───────┐
│ Config         │ hqa   │ 2wm   │ msq   │ Mean  │
├────────────────┼───────┼───────┼───────┼───────┤
│ Uniform        │ 46.94 │ 37.50 │ 22.36 │ 35.60 │
│ Best Heuristic │ 46.40 │ 37.86 │ 22.22 │ 35.49 │
│ Best Winner    │ 47.05 │ 38.58 │ 23.30 │ 36.31 │
│ Best Random    │ 46.37 │ 37.49 │ 23.17 │ 35.68 │
│ Best BO        │ 46.61 │ 36.68 │ 22.38 │ 35.22 │
└────────────────┴───────┴───────┴───────┴───────┘

-- Budget 512 --
┌────────────────┬───────┬───────┬───────┬───────┐
│ Config         │ hqa   │ 2wm   │ msq   │ Mean  │
├────────────────┼───────┼───────┼───────┼───────┤
│ Uniform        │ 46.72 │ 37.98 │ 22.60 │ 35.77 │
│ Best Heuristic │ 46.05 │ 35.67 │ 22.51 │ 34.74 │
│ Best Winner    │ 47.20 │ 37.69 │ 22.29 │ 35.73 │
│ Best Random    │ 47.17 │ 36.94 │ 22.55 │ 35.55 │
│ Best BO        │ 46.71 │ 37.04 │ 22.28 │ 35.34 │
└────────────────┴───────┴───────┴───────┴───────┘

-- Budget 1024 --
┌────────────────┬───────┬───────┬───────┬───────┐
│ Config         │ hqa   │ 2wm   │ msq   │ Mean  │
├────────────────┼───────┼───────┼───────┼───────┤
│ Uniform        │ 47.18 │ 38.40 │ 22.02 │ 35.87 │
│ Best Heuristic │ 47.23 │ 38.13 │ 22.75 │ 36.04 │
│ Best Winner    │ 47.86 │ 38.73 │ 22.19 │ 36.26 │
│ Best Random    │ 47.46 │ 38.57 │ 22.39 │ 36.14 │
│ Best BO        │ 47.07 │ 37.93 │ 22.64 │ 35.88 │
└────────────────┴───────┴───────┴───────┴───────┘
```

---

## SnapKV — CODE

### Summary

```
┌────────┬─────────┬────────────────┬─────────────┬─────────────┬─────────┬───────────────────┬─────────────────────────┐
│ Budget │ Uniform │ Best Heuristic │ Best Winner │ Best Random │ Best BO │ Winner vs Uniform │ Best config             │
├────────┼─────────┼────────────────┼─────────────┼─────────────┼─────────┼───────────────────┼─────────────────────────┤
│ 128    │ 54.82   │ 55.73          │ 55.86       │ 54.02       │ 56.10   │ +1.05             │ BO (+0.24 over winner)         │
│ 256    │ 55.68   │ 57.32          │ 57.33       │ 56.00       │ 55.29   │ +1.66             │ Winner (+0.02 over heuristic)  │
│ 512    │ 56.74   │ 58.01          │ 58.17       │ 57.78       │ 55.67   │ +1.43             │ Winner (+0.16 over heuristic)  │
│ 1024   │ 56.02   │ 58.49          │ 58.52       │ 58.91       │ 57.91   │ +2.50             │ Random (+0.40 over winner)     │
└────────┴─────────┴────────────────┴─────────────┴─────────────┴─────────┴───────────────────┴─────────────────────────┘
```

### Per-dataset breakdown

```
-- Budget 128 --
┌────────────────┬───────┬─────────────┬───────┐
│ Config         │ lcc   │ repobench-p │ Mean  │
├────────────────┼───────┼─────────────┼───────┤
│ Uniform        │ 56.90 │ 52.73       │ 54.82 │
│ Best Heuristic │ 57.13 │ 54.32       │ 55.73 │
│ Best Winner    │ 57.16 │ 54.56       │ 55.86 │
│ Best Random    │ 56.49 │ 51.54       │ 54.02 │
│ Best BO        │ 57.25 │ 54.94       │ 56.10 │
└────────────────┴───────┴─────────────┴───────┘

-- Budget 256 --
┌────────────────┬───────┬─────────────┬───────┐
│ Config         │ lcc   │ repobench-p │ Mean  │
├────────────────┼───────┼─────────────┼───────┤
│ Uniform        │ 58.23 │ 53.12       │ 55.68 │
│ Best Heuristic │ 59.21 │ 55.42       │ 57.32 │
│ Best Winner    │ 59.05 │ 55.61       │ 57.33 │
│ Best Random    │ 59.47 │ 52.52       │ 56.00 │
│ Best BO        │ 56.63 │ 53.95       │ 55.29 │
└────────────────┴───────┴─────────────┴───────┘

-- Budget 512 --
┌────────────────┬───────┬─────────────┬───────┐
│ Config         │ lcc   │ repobench-p │ Mean  │
├────────────────┼───────┼─────────────┼───────┤
│ Uniform        │ 59.16 │ 54.31       │ 56.74 │
│ Best Heuristic │ 59.83 │ 56.19       │ 58.01 │
│ Best Winner    │ 60.89 │ 55.44       │ 58.17 │
│ Best Random    │ 60.47 │ 55.08       │ 57.78 │
│ Best BO        │ 58.23 │ 53.10       │ 55.67 │
└────────────────┴───────┴─────────────┴───────┘

-- Budget 1024 --
┌────────────────┬───────┬─────────────┬───────┐
│ Config         │ lcc   │ repobench-p │ Mean  │
├────────────────┼───────┼─────────────┼───────┤
│ Uniform        │ 58.35 │ 53.69       │ 56.02 │
│ Best Heuristic │ 61.01 │ 55.97       │ 58.49 │
│ Best Winner    │ 61.39 │ 55.64       │ 58.52 │
│ Best Random    │ 61.89 │ 55.93       │ 58.91 │
│ Best BO        │ 59.60 │ 56.22       │ 57.91 │
└────────────────┴───────┴─────────────┴───────┘
```

---

## Notes

- **Best BO wins outright in only 1 of 12 completed (category, budget) combinations** (CODE B128, +0.24 over Winner) — everywhere else Best-BO is beaten by Heuristic/Winner/Random. Since this table's "Best BO" is verified genuinely isolated (see methodology note above), this is a real, not an artifact-of-mislabeling, finding: adaptive BO search rarely outperforms the cheaper heuristic/winner-seed/random alternatives here.
- **Uniform wins outright twice, both in the QA categories** (SINGLE_DOCUMENT_QA B256, MULTI_DOCUMENT_QA B512) — the layer-reallocation search does not universally help there. Gains in SINGLE/MULTI_DOCUMENT_QA are modest (≤1 point) compared to RULER's +4 to +10 point gains at matched budgets.
- **CODE is the exception to the "modest gains" pattern**: Winner-vs-Uniform deltas are consistently positive and substantially larger than the QA categories' — **+1.05 to +2.50 points** across all 4 budgets, with Uniform never winning outright at any CODE budget. Code completion/retrieval tasks (`lcc`, `repobench-p`) apparently leave more headroom for layer reallocation than open-domain QA does, plausibly because the tokens that matter (import statements, function signatures, recently-edited lines) sit at more consistent, structurally-predictable positions than QA evidence does — closer in spirit to RULER's "specific layers hold the answer" argument than to the QA categories' "evidence is spread evenly" one, though softer since Uniform is never stuck at a hard floor the way RULER's H2O baseline is.
- **Why the QA categories' gains are smaller than RULER's**: RULER's needle-in-haystack subtasks have hard structural floors — uniform allocation cannot retrieve certain needles regardless of total budget, so reallocating helps substantially. LongBench's QA tasks don't have the same structural floor; information is more evenly distributed across context, so a plain uniform split is already fairly competitive, leaving less headroom for reallocation to capture. See `RULER_Results.md`'s "Why H2O's Winner-vs-Uniform gap grows with budget..." section for the fuller version of this argument.
- This data is **SnapKV only**. H2O has no LongBench Step-4 (budget-constrained) data at all — only Step-1 (unconstrained search) was ever run for H2O on LongBench.
