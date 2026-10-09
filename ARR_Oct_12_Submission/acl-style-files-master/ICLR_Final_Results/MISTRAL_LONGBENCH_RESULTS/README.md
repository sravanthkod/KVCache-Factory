# Mistral-7B-Instruct-v0.2 -- LongBench NAS Results (SnapKV, H2O, AdaKV; consolidated dump)

Consolidated copy of every measured LongBench NAS result for Mistral-7B-Instruct-v0.2 for three eviction methods, mirroring MISTRAL_L2NORM_RESULTS and MISTRAL_RULER_RESULTS.
Generated on A100 (supercomputer, sr_share_gpu), NAS_Assets/ (SnapKV), NAS_Assets_h2o/ (H2O), NAS_Assets_adakv/ (AdaKV); copied 2026-10-08. Search calibration: 30 percent of each dataset (run_nas.sh default NAS_SAMPLE_RATIO=0.3), task score f2. All eval_results.csv are full-data (sample_ratio 1.0).

## Structure
One folder per eviction method, then one folder per task category; unconstrained/ is the Step1 search plus its Pareto eval; B<n>/ is the Step3-4 per-budget slice search plus 5-way eval.

Categories: CODE (lcc, repobench-p), SINGLE_DOCUMENT_QA, MULTI_DOCUMENT_QA. SUMMARIZATION is not included (Step1 only exists for it, no per-budget runs).

Search rows (output.txt lines) per folder:

| Method | Category | unconstrained | B128 | B256 | B512 | B1024 |
|--------|----------|---------------|------|------|------|-------|
| SNAPKV | CODE | 272 | 150 | 143 | 150 | 150 |
| SNAPKV | SINGLE_DOCUMENT_QA | 796 | 150 | 150 | 150 | 150 |
| SNAPKV | MULTI_DOCUMENT_QA | 827 | 150 | 150 | 150 | 150 |
| H2O | CODE | 269 | 146 | 150 | 125 | 150 |
| H2O | SINGLE_DOCUMENT_QA | 561 | 150 | 150 | 150 | 150 |
| H2O | MULTI_DOCUMENT_QA | 560 | 150 | 133 | 150 | 150 |
| ADAKV | CODE | 329 | 125 | 150 | 150 | 150 |
| ADAKV | SINGLE_DOCUMENT_QA | 781 | 150 | 142 | 150 | 150 |
| ADAKV | MULTI_DOCUMENT_QA | 693 | 150 | 139 | 150 | 150 |

## What is inside each subfolder
- eval_results.csv -- full-data scores per architecture. In budget folders row arch 1..5 = uniform, best_heuristic, best_winner, best_random, best_bo (snapshot order). Columns: per-dataset scores, mean_score, per-layer budgets.
- five_way_snapshot.txt -- the 5 architectures compared at that budget.
- output.txt -- every raw candidate the NAS search evaluated (search-time fitness at 30 percent calibration).
- unconstrained/ -- output.txt (Step1 search) and summary_*.csv/json (full-data eval of its Pareto-front configs); objective_values.csv for H2O only where it exists.

## Caveats
- Budget searches were capped at 150 configs (NAS_EVAL_BUDGET=150) and several were stopped earlier by hand, so depth differs (see the table). Stopped runs were evaluated at their final count.
- Per-budget searches seed 7 shape anchors, one of them the Step2 winner of the unconstrained search; slice-mode budgets are continuous, clamped to [16, 4096] per layer, with the mean pinned to the target.
- Mistral max prompt length differs by method in the code that produced these results: run_longbench_lamp.py sets model2maxlen["mistral"] = 31500 for SnapKV and AdaKV but 7500 for H2O. Prompts longer than 7500 tokens are truncated for H2O only, so H2O scores are not strictly comparable with SnapKV and AdaKV on long-context samples. This was in the files before the slice-mode port and was not changed.
- No B64 results exist. No uniform baseline for B2048 or above was run for LongBench.
- A few eval jobs failed on one node (agpu1084, CUDA device busy) and were rerun on other nodes; the reruns are the results shown.
- predictions/, run_files/ and nas_run.log were left out of this dump.
