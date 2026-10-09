# Analysis Results — ARR Oct 2026 (from existing data, no new GPU runs)

Built 2026-09-29, refreshed 2026-10-05 (adds SnapKV RULER B256 5-way, floor-64 RULER B128 winners, the H2O RULER Step-2 check and three ablations; earlier 2026-10-03 refresh added H2O SINGLE_DOC/SUMMARIZATION and SnapKV B128 cells and corrected winner labelling) from every full-data-evaluated config on local disk (Llama-3-8B-Instruct,
SnapKV + H2O, LongBench + RULER). All numbers regenerate from the scripts in
`NAS_Assets/analysis/`:

```
cd NAS_Assets
python3 analysis/collect_cells.py          # -> analysis_outputs/cells.csv (214 rows)
python3 analysis/analyze_gap_and_wins.py   # A5 + B4
python3 analysis/analyze_winner_transfer.py  # B2
python3 analysis/analyze_search_cost.py    # B1
python3 analysis/analyze_floor.py          # B3
python3 analysis/plot_layer_importance.py  # A4 (PNG + CSV)
python3 analysis/analyze_niah.py           # A6
```

Each evaluated config is labelled by its row position in its cell's Step-4 `output.txt`
(0 uniform, 1-5 heuristic, 6 winner, 7-63 random, 64+ BO); every 5-way config matched a row, and
row 0 is uniform in every file. **Row 6 is only a genuine winner if the search was launched with the
winner anchor** (see "Winner-seed labelling" below); the collector now checks this. "Floor" = per-layer minimum budget in effect for that run (16 before
Sep 2026, 64 after; all LongBench is 64). Full tables: `analysis_outputs/*.md`.

---

## Headline findings

1. **Calibration scores are optimistic and, on LongBench, don't rank configs (A5).**
   LongBench search-time scores (10% subsample) exceed full-data scores by +4.4 pts on
   average, and their ranking of the 5 candidate configs is essentially uncorrelated with the
   full-data ranking (mean Kendall τ ≈ 0; calibration picks the true best in only 6/29
   cells). On RULER, calibration is faithful (gap ≈ 0, τ = +0.8 to +1.0, 9/9 correct picks).
   → Justifies the mandatory full-data 5-way re-eval; explains why EvolKV-repro's
   calibration-only numbers looked inflated.

2. **NAS beats uniform in 35/38 cells (B4)** — every CODE and RULER cell. The 3 losses are
   all LongBench QA and small (−0.04 to −0.74): H2O MULTI_DOC B128, SnapKV MULTI_DOC B512,
   SnapKV SINGLE_DOC B256. Report them.

3. **Which search component matters depends on how faithful the search signal is (B4).**
   On LongBench the rescaled Step-2 winner is the most reliable config (overall best in 11/29
   cells, median +0.41 vs uniform) and BO is on average *worse* than uniform (median −0.26):
   BO over-fits the noisy calibration subsample (finding 1). On RULER, where calibration is
   faithful, BO is best in 5/9 cells (mean +14.3).

4. **One search, many budgets (B2).** A single unconstrained Step-1 search + Step-2 full-data
   pick, proportionally rescaled with no further search, beats uniform at **38/43**
   (category, method, budget) cells — including shapes found at avg budget ~2400 transferred
   down to 128. EvolKV must re-run its full search per budget.
   (cells.csv has no uniform row for H2O RULER B64/B256/B512; the paper adds them from
   `Meta-Llama-3-8B-Instruct/H2O_KV_All_Budgets/results_ruler` = 7.23 / 20.02 / 29.64, giving 40/46 — the
   winner wins at B64 and B512, loses at B256. Do not also add them to cells.csv or they double-count.)

5. **Search cost per budget is comparable to EvolKV — not cheaper (B1).** Same A100, same
   harness: 6 matched cells cost 53.7 GPU-h for EvolKV vs 51.1 GPU-h for our Step 4 at the
   200-eval cap. Per-sample throughput is identical; EvolKV runs 600 evals × 30 samples,
   ours ~200 evals × 55-100 samples (less noisy). Don't claim a per-search speedup; the
   efficiency argument is amortization (finding 4).

6. **Floor = 64 is a principled choice (B3).** SnapKV/H2O always keep an 8-token recent
   window (`window_size=8`, `run_longbench_lamp.py:314-318`), so a layer at budget 16 selects
   only 8 tokens by attention. Under the old floor=16, the search parked up to 66% of layers
   there (RULER B1024 H2O); at B1536/B2048 it never did (floor-independent). Under floor=64
   the floor is still binding at low budgets (50-75% of layers at the floor in B128 best
   configs), so the value genuinely matters (controlled ablation below: floor 64 better in 3 cells, tied in 2, worse in 1).

7. **Shared layer structure (A4).** Across categories, methods and budgets, middle layers
   L10, L14, L15, L16, L18 and L20 receive more than their uniform share in 58-77% of
   allocations (L17 and L19 do not: 44% / 34%), while early (L0-L9) and late (L21-L29) layers
   are mostly starved (mean 33%; exceptions L2 54%, L8 46%, L23 46%, L24 51%).
   Figure: `analysis_outputs/A4_layer_importance_heatmap.png` (draft; redraw in pgfplots).

8. **RULER gains concentrate in the hardest needle tasks (A6).** Over floor-clean cells, NAS
   adds +44.6 on niah_multikey_3 and +37.4 on niah_single_3 (tasks uniform nearly fails),
   vs −0.6/+2.7/+3.6 on CWE/FWE/VT. The floor-16 H2O B1024 config traded CWE 98→22 for NIAH
   — consistent with finding 6.

---

## Caveats to state in the paper

- **Floor footnote.** Early RULER runs used a per-layer floor of 16. RULER B1024 (both methods)
  exploits it (31% SnapKV / 66% H2O of layers at 16); B1536/B2048 also ran at floor=16 but the
  best configs never go below 64 (smallest layers 186-354), so those results are
  floor-independent. At SnapKV B1024 the rescaled winner (smallest layer 150) alone beats
  uniform by +5.8, so the floor can explain at most the ~2 extra points BO adds. Decision
  (2026-09-30): disclose, don't rerun. All LongBench is floor 64. RULER B128 (both methods)
  and SnapKV B256 have a floor-64 5-way; B64/B256(H2O)/B512 still only have the
  16-era Step-3 numbers.
- **Stage 1 budget-option cap differs by run (user + logs, 2026-10-05).** Stage 1 LongBench runs (SnapKV and
  H2O SINGLE_DOC/MULTI_DOC/SUMMARIZATION in July, AdaKV Aug 10) used 5 budget options [64..1024] (cap 1024;
  logs: "5 uniform budget anchors"); SnapKV CODE's log is lost but its anchor max is 1024 (inferred cap
  1024); H2O CODE (rebuilt Sep 11) and RULER SnapKV/H2O Stage 1 used 7 options [64..4096] ("7 uniform budget
  anchors"). 7 of the 8 LongBench winner anchors (max 1024, avg 274-732) therefore come from a space where no
  layer could exceed 1024 (range 16x) vs 64x for RULER/H2O CODE; Stage 4 slice searches decode continuously
  clipped to [64, 4096] and are not capped. Shapes are rescaled relative to their own max, so they still
  transfer to the reported B128-B1024. Hazard: `BUDGET_OPTIONS` is hard-coded to 7 options now, so re-decoding
  an old 5-option Stage 1 output.txt (e.g. rerunning `eval_top_configs.py`) would give wrong budgets; nothing
  in this analysis does (A5 etc. use Stage 4 data; anchors came from budgets recorded at eval time).
- **Eval-scheme mix on RULER.** Cells at B>=1024 were picked with earlier 3-4-config
  schemes (see `../PENDING_RUNS.md`); `RULER_Results.md`'s "Best BO" for SnapKV B1536/B2048 is
  actually the winner row. Present RULER as uniform / winner / best NAS.
- **H2O RULER winner was calibration-picked** (anchor made before the evaluate-then-pick rule). Check
  run 2026-10-04: the top-4 calibration-ranked configs scored on full data (avg budget 2180 / 2352 /
  2130 / 2260): 97.96 / 97.71 / 97.23 / 96.81 vs calibration 97.84 / 97.16 / 97.15 / 97.04 — the
  anchor (2180) is best on full data too and the full-data ranking equals the calibration ranking
  (tau = +1.0). This confirms it among the top 4 only; the rest of the front was not evaluated.
- SnapKV LongBench Step-4 run lengths (125-1000 evals) were set by the saturation watchdog,
  not by design; H2O runs are capped at 200.
- Some SnapKV MULTI_DOC calibration scores are identical across budgets (42.1067 for uniform at
  B256/B512/B1024) — likely calibration-subsample saturation; worth a quick look before
  quoting calibration numbers for that category.
- CODE Step-1 raw logs were lost (2026-09-10 `rm -rf`); CODE Step-1 cost is unreported.

## Winner-seed labelling (2026-10-03, resolved 2026-10-05)

Search row 6 is a *winner seed* only if the search was launched with `NAS_ANCHOR_FILE`, and the seed
need not sit at row 6. The collector now labels as winner whichever initial-design row (1-63) matches
the winner anchor (r > 0.9), and row 6 without a match as a heuristic. Three cells were affected:
- SINGLE_DOC/H2O B128: row 6 was a triangle heuristic (r = -0.19). Winner = the floor-64 Step-3
  rescaled winner, **29.72** (+1.51 over uniform 28.21; best NAS config in the cell).
- RULER SnapKV B128: row 6 was a triangle heuristic (r = +0.44) but **row 9 (labelled "random") is the
  winner** (r = +0.99; its score 58.37 is identical to the separately evaluated floor-64 rescaled
  winner, same budgets). Winner = **58.37 (+6.81)**, the best config in the cell.
- RULER H2O B128: row 6 was an alternating heuristic (r = -0.01). Floor-64 rescaled winner evaluated
  separately on 2026-10-04: **12.22** (+0.03 over uniform 12.19; BO 15.39 is best).
Effect on headline numbers: winner-beats-uniform 36/41; LongBench winner is overall best in 11/29
cells; RULER (9 cells): winner best in 4, BO in 5. EvolKV comparison cells are unaffected.

## RULER SnapKV B256 5-way (2026-10-04)

Uniform / heuristic / winner / random / BO = 68.06 / 67.95 / **72.28** / 71.07 / 68.48. The winner is
best (+4.21); BO adds only +0.42. Calibration picks the full-data best (RULER SnapKV 5/5).

## H2O RULER B2048 winner + SnapKV SUMMARIZATION B1024 (2026-10-05/06)

- **H2O RULER B2048 winner** (search row 6, r = +1.00 to the anchor; the old 4-way auto-eval never scored it
  because a heuristic beat it on calibration, 91.28 vs 87.70): **88.31** on full data (+25.5 over uniform 62.82).
  It is below the heuristic (92.51), random (93.09) and BO (96.14) configs, so at B2048 the NAS gain comes from
  the Stage 4 search, not the anchor shape alone. Smallest layer 248, so floor-independent.
- **SnapKV SUMMARIZATION B1024** (new Step-3 cell, no search): uniform **24.85**, rescaled winner **25.10**
  (+0.25). The uniform reproduces the 24.85 (u1024) in `NAS_vs_UNIFORM_LONGBENCH_13_08_2026.md`.

## Ablations (SnapKV, Llama-3-8B-Instruct, local A100; full data; `NAS_Assets/ablation_plans.py`)

Reports: `analysis_outputs/AB_search_budget_curve.md`, `AB_floor.md`, `AB_calibration_ratio.md`.

**1. Search-budget curve** (CODE and SINGLE_DOC x B128/256/512/1024, 8 cells): best-by-calibration
config among the first k search rows. Mean gain over uniform: k=64 (initial design only: uniform,
heuristics, winner seed, LHS points) **+0.72**; k=all (the paper's NAS-refined) **+0.47**. The
guided iterations changed the selected config in 3/8 cells: better in 1 (CODE B128 +0.91 -> +1.28),
worse in 2 (CODE B512 +1.04 -> -1.07; SINGLE_DOC B128 +0.70 -> +0.48); in the other 5 the best
initial-design config is already the final pick. So on LongBench the guided search does not improve
on its own initial design on average — consistent with finding 1 (calibration noise): the
calibration-best BO row over-fits. This weakens, not answers, the "benefit of the optimizer"
concern; an equal-budget random-search baseline would still be needed to separate guided search
from a good initial design.

**2. Controlled floor ablation (C3)** (same rescaled winner, per-layer floor 64 vs 16):
CODE B128 54.76 (floor 16) vs 55.86 (floor 64); CODE B256 57.30 vs 57.33; SINGLE_DOC B128 33.14 vs
33.51; SINGLE_DOC B256 34.77 vs 34.51; MULTI_DOC B128 34.32 vs 35.02; MULTI_DOC B256 identical (floor
not binding). Floor 64 is better in 3 cells (by 0.37-1.10, all at B128 where 16-24 layers sit at the
floor), tied in 2, worse in 1 (+0.26 at SINGLE_DOC B256, where the winner is below uniform anyway);
mean (16 - 64) = -0.32. Modest support for floor 64, concentrated at B128 — with the
floor-16 RULER B1024 caveat unchanged.

**3. Calibration-ratio study** (CODE B512, 24 configs: calibration at 10% / 30% vs full data). 10%:
mean optimism +5.10 pts, Kendall tau +0.51, the calibration-picked config is not the full-data best
(regret 2.87). 30%: optimism +1.37, tau +0.75, picks the full-data best (regret 0). A larger
calibration subsample reduces the noise (at ~3x the evaluation cost), so LongBench's unreliable
ranking is a sample-size effect. **Caveats:** one cell, chosen because BO underperformed uniform
there (selection bias — a case study, not a general result); the 24 configs span uniform,
heuristics, random and BO rows, not just the 5 evaluated per cell in A5.

## Transfer ablations (C1 / C2, SnapKV and H2O, CODE and SINGLE_DOC; full data)

Same shape (the source cell's rescaled winner) evaluated in another cell, vs the receiving
cell's uniform and its own rescaled winner (`NAS_Assets/transfer_evals/`).

| Transfer | B128 | B512 | B1024 | vs receiving uniform |
|---|---|---|---|---|
| C1 CODE shape on SINGLE_DOC (SnapKV) | 32.43 | 34.89 | 36.11 | -0.54 / -1.08 / -0.33 |
| C1 SINGLE_DOC shape on CODE (SnapKV) | 54.00 | 55.52 | 55.39 | -0.81 / -1.21 / -0.63 |
| C2 H2O CODE shape under SnapKV (CODE) | 54.88 | 57.48 | 57.68 | +0.07 / +0.74 / +1.66 |
| C2 SnapKV CODE shape under H2O (CODE) | 46.75 | 53.77 | 57.05 | +0.79 / +0.96 / +0.12 |

- **Allocations are task-specific (C1):** a shape moved to another task loses to uniform in 6/6 cells.
- **Shapes transfer across methods (C2):** the moved shape beats the receiving method's uniform
  in 6/6 cells (+0.07 to +1.66).
- Versus the receiving cell's *own* winner: SnapKV as recipient, the transferred shape trails
  at all 3 budgets (-0.98 / -0.69 / -0.84); H2O as recipient it is +0.16 / -0.26 / +0.90
  (H2O's own CODE winner scores 56.15 at B1024, below uniform 56.93, so the comparison is noisy).
  → C2 does **not** show that a per-method search always beats a transferred shape.

## Still to run (GPU)

- Optional: equal-budget random-search baseline (the real answer to "benefit of the optimizer"),
  seed variance of the search, and the 30%-calibration search (~25-50 GPU-h each, one GPU).
- RULER B64 / H2O B256 / B512 floor-64 multi-config evals (only floor-16 Step-3 numbers exist).
