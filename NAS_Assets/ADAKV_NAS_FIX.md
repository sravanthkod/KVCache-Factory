# AdaKV NAS Bug Fix

## Problem
AdaKV NAS was producing scores that didn't respond to budget changes. When running NAS on the 30% calibration dataset, the f2 objective (task_score) remained nearly constant across different per-layer budget configurations, preventing the optimizer from finding meaningful tradeoffs between budget and quality.

**Evidence:**
- 49 unique f2 values but no clear correlation with f1 (budget)
- All f2 scores in narrow range (-2.84 to -6.88) without clear pattern
- Working algorithms (SNAPKV, H2O) showed clear score variation with budget changes

## Root Cause
In `run_dataset_calibration_with_scoring()` function, the `kv_cluster` cache was not being deleted after `set_model_budgets()` updated the per-layer budget instance attributes.

**Why this matters for AdaKV:**
1. AdaKV's `init_adakv()` creates a kv_cluster object that caches per-head budget allocations
2. The check `if not hasattr(self, "kv_cluster")` (line 1457 in pyramidkv_utils.py) means it only creates the cluster if it doesn't exist
3. When evaluating a new X_point (budget configuration), `set_model_budgets()` updates the budget instance attributes
4. But if kv_cluster from the previous X_point still exists with old budgets, `init_adakv()` skips creation
5. Result: The same old kv_cluster with old budgets is reused, so f2 scores don't change

**Why SNAPKV/H2O don't have this issue:**
- Their kv_cluster reads budget values fresh on each forward pass, rather than caching them

**Why the bug only appears in `run_dataset_calibration_with_scoring()`:**
- `run_dataset_calibration()` (evicted_attn variant) has deletion in the batch loop (lines 471-474)
- `run_dataset_calibration_with_scoring()` (task_score variant) was missing the deletion after `set_model_budgets()`

## The Fix
**File:** `run_longbench_lamp.py`  
**Location:** Lines 546-552 (after line 544 in `run_dataset_calibration_with_scoring()`)

Added kv_cluster deletion right after `set_model_budgets()` call:

```python
    # Set per-layer budgets on the model
    set_model_budgets(model, max_capacity_prompts, method=method)

    # Delete kv_cluster to force recreation with new budgets.
    # Critical for AdaKV/HeadKV: they cache per-head budget allocations inside kv_cluster.
    # Without deletion, old budgets persist and f2 scores don't reflect new X_point values.
    if method.lower() in ("adakv", "headkv"):
        for layer in model.model.layers:
            if hasattr(layer.self_attn, "kv_cluster"):
                delattr(layer.self_attn, "kv_cluster")
```

This forces `init_adakv()` to recreate the kv_cluster with the new per-layer budgets on the next forward pass.

## Verification
To verify the fix works:

1. **Check score variation:** Run AdaKV NAS for a small number of iterations and verify that f2 scores now vary with budget changes
   ```bash
   cd /home/snap_nas/sravanth/LLM/Token_Eviction/Dynamic_Methods/KVCache-Factory/NAS_Assets
   NAS_TASK_CATEGORY=SINGLE_DOCUMENT_QA NAS_METHOD=adakv python LAMP.py
   ```

2. **Check output.txt:** Look for clear inverse correlation between f1 (budget) and f2 (score)
   - Example: Lower budget (f1=500) → Higher negative score (f2=-2.5)
   - Example: Higher budget (f1=1500) → Lower negative score (f2=-6.0, which is "better")

3. **Compare with working methods:**
   ```bash
   # Run SNAPKV for comparison
   NAS_TASK_CATEGORY=SINGLE_DOCUMENT_QA NAS_METHOD=snapkv python LAMP.py
   ```

## Impact
This fix enables AdaKV to:
1. Properly leverage NAS to find optimal per-layer budget allocations
2. Discover task-specific budget patterns (which layers need high budgets)
3. Generate meaningful Pareto-optimal configurations
4. Match the quality of SNAPKV and H2O NAS results

## Related Code
- `init_adakv()`: `/pyramidkv/pyramidkv_utils.py` line 1435
- `set_model_budgets()`: `run_longbench_lamp.py` line 288
- `run_dataset_calibration()` (working version): `run_longbench_lamp.py` line 404
- `run_dataset_calibration_with_scoring()` (fixed version): `run_longbench_lamp.py` line 514
