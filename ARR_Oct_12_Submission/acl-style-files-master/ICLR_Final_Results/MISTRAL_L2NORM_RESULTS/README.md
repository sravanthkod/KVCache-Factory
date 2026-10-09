# Mistral-7B-Instruct-v0.2 -- L2Norm NAS Results (consolidated dump)

Consolidated copy of every measured L2Norm result for Mistral-7B-Instruct-v0.2, mirroring LLAMA_L2NORM_RESULTS.
Generated on H100, NAS_Assets/, 2026-10-06. Method: L2Norm. Search calibration: 30 percent of each dataset (NAS_SAMPLE_RATIO=0.3). All eval_results.csv are full-data (sample_ratio 1.0).

## Structure
One folder per task category; unconstrained/ is the Step1 search plus Step2 Pareto eval; B<n>/ is the Step4 per-budget search plus 5-way eval.

- RULER_ALL/ -- unconstrained (606 search rows), B128 (111 search rows), B256 (121 search rows), B512 (130 search rows), B1024 (140 search rows), B1536 (146 search rows), B2048 (117 search rows)
- CODE/ -- unconstrained (571 search rows), B128 (113 search rows), B256 (133 search rows), B512 (136 search rows), B1024 (117 search rows)
- SINGLE_DOCUMENT_QA/ -- unconstrained (365 search rows), B128 (170 search rows), B256 (193 search rows), B512 (220 search rows), B1024 (276 search rows)
- MULTI_DOCUMENT_QA/ -- unconstrained (440 search rows), B128 (218 search rows), B256 (233 search rows), B512 (260 search rows), B1024 (285 search rows)
- SUMMARIZATION/ -- unconstrained (209 search rows), B128 (140 search rows), B256 (140 search rows), B512 (144 search rows), B1024 (143 search rows)

## What is inside each subfolder
- eval_results.csv -- full-data scores. In budget folders row arch 1..5 = uniform, best_heuristic, best_winner, best_random, best_bo (snapshot order).
- five_way_snapshot.txt -- the 5 architectures compared at that budget.
- fixed_budget_snapshot.txt -- the uniform config evaluated.
- output.txt -- every raw candidate the NAS search evaluated (search-time fitness at 30 percent calibration).

## Caveats
- No Mistral B64, B2048 or B4096 uniform results exist for any category except RULER_ALL B2048. Mistral LongBench was run at B128-B1024 only.
- Search depth differs per category and budget (see row counts above); searches were stopped manually.
- predictions/ and run_files/ were left out of this dump.
