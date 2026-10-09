# Handoff to the paper-writing session — 2026-10-05, updated 2026-10-06 (supersedes the 2026-10-02 file)

All three local GPU queues finished (2026-10-04). `analysis_outputs/` is refreshed (cells.csv = 211 rows),
`A4_layer_importance.csv` (+PNG) is copied into `ARR_Oct_12_Submission/acl-style-files-master/figures/`.
Regenerate the per-cell tables, Table 4 counts, calibration table, transfer table and Figure 3 from
`analysis_outputs/`. Narrative detail: `Analysis_Results.md`. Ablation tables: `analysis_outputs/AB_*.md`.

## Item 36 (the runs you were waiting on) — all done
- **RULER SnapKV B256 5-way** (uniform / heuristic / winner / random / BO): 68.06 / 67.95 / **72.28** / 71.07 / 68.48.
  Winner best (+4.21); BO only +0.42.
- **RULER B128 winners:** SnapKV winner = **58.37** (+6.81 over uniform 51.56), the best config in the cell.
  H2O winner (floor-64 rescaled, evaluated separately) = **12.22** (+0.03 over uniform 12.19); H2O BO 15.39 is best.
  So both RULER B128 cells now HAVE a clean winner; the "uniform / NAS-refined only" fallback is no longer needed.
  Note: in RULER SnapKV B128 the winner seed sat at search row 9 (it was labelled "random" before); row 6 was a
  heuristic. cells.csv now labels it winner. This changes that cell's 5-way labels (no "random" row remains).
- **H2O RULER Step-2 check (resolves part of PAPER_ISSUES 29b):** top-4 calibration-ranked configs on full data
  (avg budget 2180 / 2352 / 2130 / 2260) = 97.96 / 97.71 / 97.23 / 96.81 vs calibration 97.84 / 97.16 / 97.15 /
  97.04. The anchor (2180) is also best on full data and the full-data ranking equals the calibration ranking
  (tau = +1.0). Confirmed among the top 4 only; the rest of the Stage-1 front was not evaluated, so Figure 2's
  H2O RULER panel can be filled with these 4 but is not the full front.

## Updated headline numbers (SnapKV + H2O, Llama)
- NAS beats uniform **35/38** cells (same 3 losses). Rescaled winner beats uniform **36/41**.
- Calibration picks the true best: LongBench 6/29, RULER **9/9** (H2O 4/4, SnapKV 5/5). LongBench pooled
  calibration gap +4.4 pts (145 configs).
- LongBench components (29 cells): winner best in 11, random 6, heuristic 5, BO 4, uniform 3; median delta vs
  uniform: winner +0.41, BO -0.26. RULER (9 cells): BO best in 5 (mean +14.3), winner in 4 (mean +7.4).
- Layers above uniform share in 60-76% of allocations: L10, L14, L15, L16, L18, L20.

## NEW ablations (SnapKV, Llama-3-8B-Instruct, local A100, full data) — need honest framing
1. **Search-budget curve** (8 cells: CODE and SINGLE_DOC x B128/256/512/1024). Best-by-calibration config in the
   first k rows: k=64 (initial design only) mean gain over uniform **+0.72**; k=all (NAS-refined) **+0.47**.
   Guided iterations changed the pick in 3/8 cells: better in 1, worse in 2; unchanged in 5. => On LongBench the
   guided search does NOT beat its own initial design on average (calibration over-fitting). This is evidence
   AGAINST "the optimizer adds value" and is consistent with PAPER_ISSUES 18's note that 23 of 67 final configs
   are initial-design points. Frame the contribution as the workflow (anchor + rescaling + full-data selection),
   as the paper already does; do not claim the guided phase improves LongBench results.
2. **Controlled floor ablation** (same rescaled winner, floor 16 vs 64): floor 64 better in 3 cells (CODE B128
   -1.10, MULTI_DOC B128 -0.70, SINGLE_DOC B128 -0.37 for floor 16), tied in 2, floor 16 better in 1 (+0.26
   SINGLE_DOC B256). Mean (16 - 64) = -0.32. Modest support for floor 64, concentrated at B128.
3. **Calibration-ratio study** (CODE B512, 24 configs): 10% calibration: optimism +5.10, Kendall tau +0.51, picks
   a non-best config (regret 2.87); 30%: optimism +1.37, tau +0.75, picks the best (regret 0). Larger calibration
   reduces the noise (at ~3x eval cost). CAVEAT: one cell, chosen because BO underperformed uniform there
   (selection bias) — a case study, not a general result.

## Still open / not run
- Equal-budget random-search baseline (the real answer to PAPER_ISSUES 18), search-seed variance and a
  30%-calibration search: not run (~25-50 GPU-h each on the one local GPU that is reliably ours).
- RULER B64 / H2O B256 / B512 multi-config evals (floor-16 Step-3 only).
- `method_to_server.md` does not exist on this server; not updated.

## Update 2026-10-06 (cells.csv = 214 rows; A4 csv re-copied)
- **H2O RULER B2048 winner (search row 6): 88.31** (+25.5 over uniform 62.82). It was never scored before because the
  old 4-way auto-eval evaluates only the best of rows 1-6 by calibration and a heuristic (91.28) beat the winner
  seed (87.70). Below the heuristic (92.51), random (93.09) and BO (96.14): at B2048 the gain comes from the Stage 4
  search, not the anchor shape. Floor-independent (min layer 248). cells.csv adds it as a supplementary winner row.
- **SnapKV SUMMARIZATION B1024 (new Step-3 cell, no search):** uniform **24.85**, rescaled winner **25.10** (+0.25).
- Counts: rescaled winner beats uniform **38/43** in cells.csv (was 36/41); with the three external H2O RULER
  B64/B256/B512 uniform rows the paper adds, SnapKV+H2O = **40/46**. RULER winner mean gain +9.4 (4 cells).
- Layers above uniform share: L10 77%, L14 74%, L15 77%, L16 63%, L18 58%, L20 60%.
