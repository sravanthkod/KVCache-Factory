# Llama-3-8B-Instruct -- L2Norm NAS Results (consolidated dump)

This folder is a consolidated copy of every measured L2Norm result for Llama-3-8B-Instruct, pulled together from wherever each piece of data currently lives on this server (some paths were archived into `*_llama_archived_<date>/` sibling folders once Mistral-7B started sharing the same output paths).

For the full narrative writeup (methodology, results tables, interpretation, caveats), see `../L2NORM_LLAMA_RESULTS.md` one directory up -- this README only explains what is in THIS folder and how to read it.

## Structure

One folder per task category, each with an `unconstrained/` subfolder plus one subfolder per budget level tested:

- RULER_ALL/ -- unconstrained, B64, B128, B256, B512, B1024, B1536, B2048, B4096
- CODE/ -- unconstrained, B64, B128, B256, B512, B1024, B2048
- SINGLE_DOCUMENT_QA/ -- unconstrained, B64, B128, B256, B512, B1024, B2048
- MULTI_DOCUMENT_QA/ -- unconstrained, B64, B128, B256, B512, B1024, B2048
- SUMMARIZATION/ -- unconstrained, B64, B128, B256, B512, B1024, B2048

## What is inside each subfolder

- eval_results.csv -- the actual scores. Columns: arch, avg_budget, nas_f2, one column per dataset in that category, mean_score, budgets (32 per-layer values, space-separated). This is the file you want for numbers.
- five_way_snapshot.txt (budget folders 128-1024, plus 1536/2048 for RULER_ALL) -- the 5 architectures evaluated, row order: uniform, best_heuristic, best_winner, best_random, best_bo -- matches eval_results.csv arch 1-5 in the same order.
- fixed_budget_snapshot.txt (unconstrained/, B64, and the top extreme B2048/B4096) -- single-shape rescale, not a 5-way search; see caveat below.
- output.txt (unconstrained/ and budget-search folders) -- every raw candidate the NAS search evaluated (32 layer-budget columns + f1=avg_budget + f2=negative task score), one row per candidate. This is the full search history behind eval_results.csv.

## Caveats

- B64 and the top extreme (B2048, or B4096 for RULER_ALL) only have ONE evaluated config, not 5 -- at the budget floor/ceiling every layer is forced to the same value, so a shaped allocation collapses to uniform. This is a mathematical certainty, not missing data.
- Not every category reached the same Step1 search depth before being stopped (e.g. SUMMARIZATION stopped earlier than the others) -- see ../L2NORM_LLAMA_RESULTS.md Section 6 for exact row counts.
- predictions/ (raw per-sample generations) and run_files/ (plot images) were deliberately left out to keep this a lean numbers-only package -- they still exist at the original source paths on this server if needed.

---
*Generated on H100 (space_n7), NAS_Assets/, 2026-09-29. Model: Meta-Llama-3-8B-Instruct. Method: L2Norm (L2NormCluster). Attn impl: sdpa.*
