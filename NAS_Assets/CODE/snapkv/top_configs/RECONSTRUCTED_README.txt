This eval_results.csv was RECONSTRUCTED on 2026-09-11 by parsing
NAS_Assets/eval_logs/CODE_22_07_2026.log, after the original
NAS_Assets/CODE/snapkv/ directory (including the real eval_results.csv,
output.txt, and run_files/) was accidentally deleted via `rm -rf
NAS_Assets/CODE` (meant to clean up an unrelated EvolKV smoke-test
artifact that happened to share the same top-level "CODE" directory name).

What's preserved: per-config avg_budget, nas_f2 (search objective), mean
downstream task score (averaged over lcc+repobench-p, NOT split per-dataset
-- the Jul 22 script version didn't log per-dataset scores), and full
per-layer budgets, for all 11 rank-1/Pareto-optimal configs from the
original Step-1 search. Config 9 here matches
anchors/anchor_longbench_CODE_snapkv.txt exactly (avg_budget=430,
mean_score=58.26) -- confirms this is the same Step-2 run that produced
the winner anchor.

What's NOT recoverable: the raw Step-1 output.txt (full evolutionary
search history, ~116 evaluated architectures beyond the 11 shown here),
nas_run.log, and run_files/ plots.
