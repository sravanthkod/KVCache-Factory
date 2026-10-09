# Mistral-7B-Instruct-v0.2 -- RULER NAS Results (SnapKV, H2O, AdaKV; consolidated dump)

Consolidated copy of every measured RULER result for Mistral-7B-Instruct-v0.2 for three eviction methods, mirroring MISTRAL_L2NORM_RESULTS.
Generated on A100 (supercomputer, sr_share_gpu), NAS_Assets_ruler/, copied 2026-10-06. Task group: RULER_ALL (11 subtasks, ctx 4096). All eval_results.csv are full-data (sample_ratio 1.0).

## Structure
One folder per eviction method; inside, RULER_ALL/ holds unconstrained/ (Step1 search plus Step2 Pareto eval) and B<n>/ (Step3-4 per-budget search plus 5-way eval).

- SNAPKV/RULER_ALL/ -- unconstrained (934 search rows), B128 (218), B256 (484), B512 (422), B1024 (308), B1536 (319), B2048 (336)
- H2O/RULER_ALL/ -- unconstrained (702 search rows), B128 (375), B256 (370), B512 (360), B1024 (218), B1536 (213), B2048 (225)
- ADAKV/RULER_ALL/ -- unconstrained (836 search rows), B128 (218), B256 (114), B512 (526), B1024 (3), B1536 (26), B2048 (25)

## What is inside each subfolder
- eval_results.csv -- full-data scores per architecture. In budget folders row arch 1..5 = uniform, best_heuristic, best_winner, best_random, best_bo (snapshot order). Columns: 11 RULER subtask scores, mean_score, and the per-layer budgets.
- five_way_snapshot.txt -- the 5 architectures compared at that budget.
- output.txt -- every raw candidate the NAS search evaluated (search-time fitness, NAS_SAMPLE_RATIO default 0.1).
- unconstrained/ -- output.txt, eval_results_all500.csv and eval_results_shard{0,1,2}.csv (Pareto-front configs evaluated on all 500 samples per subtask, split across shards), output_snapshot.txt (frozen copy of the search file used for that eval), and the winner anchor (anchor_snapkv.txt, anchor_h2o.txt; none was kept for AdaKV).

## Caveats
- No B64 results exist for any method. B64 was skipped on a wrong assumption that the minimum per-layer budget was 64; the real floor is NAS_MIN_BUDGET=16, so B64 is feasible but was never run.
- AdaKV B1024 (3 rows), B1536 (26) and B2048 (25) searches were stopped very early, so those "best" rows are close to the seeded starting points and are a weak comparison against SnapKV and H2O at the same budgets.
- Search depth differs per method and budget (see row counts above); searches were stopped manually, not at a fixed budget.
- AdaKV B512 was resumed once (NAS_RESUME_ROWS=34); the resumed job's scheduler status shows Failed from a harmless wrapper interrupt, but output.txt is intact (526 rows) and the eval completed.
- Slice-mode budgets are continuous, clamped to [16, 4096] per layer, with the mean pinned to the target.
- predictions/, run_files/ and nas_run.log were left out of this dump.
