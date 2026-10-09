# Handoff to the paper-writing session — updated 2026-10-03

(The "ARR Oct 12 - MOSAIC Paper Writing" session was not reachable when this was written, so it is
saved here. Everything below is on disk and verified. **This supersedes the 2026-10-02 version and
corrects four statements in it and in earlier messages — see "Corrections".**)

`analysis_outputs/` is refreshed (cells.csv = 207 rows) and `A4_layer_importance.csv` (+ PNG) is
copied into `ARR_Oct_12_Submission/acl-style-files-master/figures/`. Regenerate Table 4 counts,
per-cell tables, the calibration table, the transfer table and Figure 3 from `analysis_outputs/`.

## Corrections (please apply to anything already written)
1. **Winner labelling is wrong in 3 cells.** Search row 6 is a winner seed only if the search was
   launched with the anchor. In SINGLE_DOC/H2O B128, RULER H2O B128 and RULER SnapKV B128 it is a
   heuristic (r to the anchor = -0.19 / -0.01 / +0.44; all other 28 cells r >= 0.98). The
   collector now relabels it. For SINGLE_DOC/H2O B128 the winner is the floor-64 Step-3 rescaled
   winner, **29.72** (+1.51 over uniform 28.21; best NAS config in the cell). For RULER H2O B128
   and SnapKV B128 there is **no clean winner** (the SnapKV Step-3 winner is floor-16, min layer
   19) — show these two cells as Uniform / NAS-refined only, or wait for the floor-64 winner evals
   (2 configs, ~7 GPU-h, not yet run). Any "Winner" number in those 3 cells taken from the 5-way
   table (27.87 / 11.73 / 53.61) is a heuristic config, not the winner.
2. **C2 does not show "a per-method search always wins".** I earlier wrote that a transferred
   shape "trails the receiving method's own winner at all 3 budgets" in both directions. Actual:
   SnapKV as recipient it trails (-0.98 / -0.69 / -0.84); **H2O as recipient it is +0.16 / -0.26 /
   +0.90** (H2O's own CODE winner scores 56.15 at B1024, below uniform 56.93). The transferred
   shape beats the receiving method's uniform in 6/6 cells (+0.07 to +1.66). Also the H2O CODE
   winner at B1024 is 56.15, not 57.23 as I quoted.
3. **Layer-importance wording.** Not "L10 and L14-L20 / L14-L18". Correct: L10, L14, L15, L16, L18,
   L20 are above uniform share in 61-76% of allocations; L17 (44%) and L19 (34%) are not.
   Early/late layers: mean 33%, exceptions L2 54%, L8 46%, L23 46%, L24 51%.
4. **Coverage.** LongBench 5-way is done for 29 of 31 evaluated cells (see below), not "complete".

## Updated headline numbers (`Analysis_Results.md`)
- NAS beats uniform: **34/37** cells; the 3 losses are unchanged (H2O MULTI_DOC B128 -0.41,
  SnapKV MULTI_DOC B512 -0.04, SnapKV SINGLE_DOC B256 -0.74).
- Rescaled winner beats uniform: **34/39** cells (two RULER B128 cells have no clean winner).
- LongBench calibration gap **+4.4** pts (145 configs); calibration picks the true best in
  **6/29** LongBench cells; RULER 8/8. Mean Kendall tau: H2O -0.00, SnapKV +0.03.
- LongBench component breakdown (29 five-way cells): winner best in 11, random 6, heuristic 5,
  BO 4, uniform 3. Median delta vs uniform: winner +0.41, BO -0.26.
- RULER (8 cells): BO best in 5, winner 2, random 1; mean BO gain +16.6.

## New cells since the last handoff (full data, uniform / heuristic / winner / random / BO)
H2O SUMMARIZATION: B128 21.88/21.48/22.02/22.05/22.31 · B256 23.13/23.25/23.17/23.33/22.88 ·
B512 24.22/24.32/24.35/24.21/23.98 · B1024 24.97/25.32/25.11/25.29/24.29.
H2O SINGLE_DOC B128: 28.21/28.21/**29.72 (Step-3 winner)**/28.32/28.09 (the 5-way's own row-6 triangle
heuristic scored 27.87). SnapKV SUMMARIZATION B128: 21.03/20.95/21.15/20.89/20.83 (best NAS +0.12).
RULER SnapKV B128: uniform 51.56, heuristic 51.56, random 58.37, BO 55.91, no clean winner.
The B128 LongBench gains are marginal (+0.11 to +0.12 in two cells) — don't present as wins.
Repeated uniform configs reproduced their Step-3 scores exactly, so evals are deterministic.

## Coverage
LongBench 5-way: 29 of 31 evaluated (category x method x B128-1024) cells. Still Step-3-only:
SnapKV SUMMARIZATION B256/B512 (never searched); SnapKV SUMMARIZATION B1024 has no cell.
RULER SnapKV B256 5-way is running (ETA ~02:30 UTC Oct 4).

## Open
- H2O RULER Step-2 full-data check of the calibration-picked winner not run (disclose-only).
  Anchor is #1 of 205 by calibration (97.84 vs next 97.16); A5: RULER calibration is faithful.
- `method_to_server.md` (named in CLAUDE.md) does not exist on this server — not updated.
- Only GPU1 is reliably ours; GPU0/2 are often held by other users.
