# RULER 4-step NAS methodology — runbook (any eviction method)

Reference implementation: SnapKV, already complete end-to-end under
`RULER_ALL/snapkv/` (Step 1) and `RULER_ALL_B{1024,1536,2048}/snapkv/`
(Step 4). This runbook generalizes the exact same commands to any method —
use it to run H2O / AdaKV / StreamingLLM (or anything else) on this or
another server.

All commands run from `NAS_Assets/` with:
```bash
export PYTHONNOUSERSITE=1   # REQUIRED — avoids a broken ~/.local transformers-5.x shadow install
export PYTHONPATH="/home/snap_nas/sravanth/LLM/Token_Eviction/Dynamic_Methods/KVCache-Factory:${PYTHONPATH:-}"
```
using the `cakekv` conda env's interpreter:
`/home/test/miniconda/envs/cakekv/bin/python` (all the `run_*.sh` scripts already default `PYTHON_BIN` to this).

## Method-name convention (must match exactly — `NAS_METHOD` / `--method`)

| Method | String to use | Notes |
|---|---|---|
| SnapKV | `snapkv` | reference method, fully done |
| H2O | `h2o` | |
| AdaKV | `adakv` | `kv_cluster` reset special-case already handled in `run_ruler_lamp.py` / `run_longbench_lamp.py` — no code changes needed. Known issue: full-500 scores differ slightly across machines by torch version (see caveat below). |
| StreamingLLM | `streamingllm` | **no underscore** — `streaming_llm` is not recognized by `pyramidkv/monkeypatch.py`'s dispatch and will fail silently/incorrectly. |
| PyramidKV | `pyramidkv` | out of scope for NAS per current paper decision (`Status.md`) |

## Step 1 — Unconstrained NAS

```bash
NAS_METHOD=<method> NAS_TASK_CATEGORY=RULER_ALL \
    nohup bash run_nas_ruler.sh > sravanth_logs/NAS_RULER_ALL_<method>_$(date +%d_%m_%Y).log 2>&1 &
```
Defaults: `NAS_SAMPLE_RATIO=0.3`, `NAS_SEED=42`, `NAS_CONTEXT_LENGTH=4096`, 3-GPU worker pool (`NAS_GPUS=0,1,2`) — override individually if needed. Output accumulates in `RULER_ALL/<method>/output.txt` (34 columns: 32 x-values + f1 avg-budget + f2 = -score). Watch it the same way SnapKV's was watched: monitor best score, stop once it stabilizes (SnapKV's run took 198 evals).

## Step 2 — Extract the winner anchor + full-500 eval of it

```bash
python3 extract_winner_anchor.py RULER_ALL --method <method>
# -> anchors/anchor_<method>_<avgbudget>.txt
```
This picks the best NON-uniform (shaped) config on the Pareto front — uniform-budget anchors are always Pareto-optimal on the score axis but carry no per-layer allocation information, so they're excluded (this exactly reproduces how `anchor_1756_budgets.txt` was chosen for SnapKV: arch 11 of 13, not the trivial uniform-4096 arch 6).

Full-500 evaluation of the whole Pareto front (mirrors `RULER_ALL/snapkv/top_configs/eval_results_all500.csv`):
```bash
python3 eval_top_configs_ruler.py RULER_ALL --method <method> --sample_ratio 1.0
```

## Step 3 — Rescale the anchor to fixed budgets + full-500 eval (cheap)

```bash
# Sanity check first (no GPU, just decode + sum check):
python3 eval_fixed_budgets_from_anchor.py anchors/anchor_<method>_<avgbudget>.txt \
    --method <method> --targets 64,128,256,512 --dry_run

# Then the real full-500 eval:
python3 eval_fixed_budgets_from_anchor.py anchors/anchor_<method>_<avgbudget>.txt \
    --method <method> --targets 64,128,256,512 --gpu 0
```
Writes `RULER_ALL_B{64,128,256,512}/<method>/top_configs/eval_results.csv`, each with 2 rows (uniform, winner-shape) at full 500 samples. Runs in minutes, not days — no search involved.

## Step 4 — Budget-constrained slice NAS (the expensive enhancement)

Recommended scope (matches SnapKV): same 3 budgets, 1024/1536/2048, one GPU each.

```bash
NAS_METHOD=<method> NAS_ANCHOR_FILE=anchors/anchor_<method>_<avgbudget>.txt \
    nohup bash run_nas_ruler_slices.sh > sravanth_logs/NAS_RULER_SLICES_<method>_launch_$(date +%d_%m_%Y).log 2>&1 &
```
Launches 3 independent LAMP searches (GPU 0/1/2 = B1024/B1536/B2048), each seeded with the 7 shape anchors (uniform + ramps/triangles/alternating + your winner shape) plus 57 LHS random-allocation points, then BO-guided search.

Auto-watch + auto-eval each slice on convergence (same stability rule used for SnapKV: 40 stale evals counted from `max(rows_at_best, 64)`, so the guided BO phase always gets ≥40 real evaluations before declaring convergence):
```bash
NAS_METHOD=<method> \
    nohup bash watch_slices_and_eval.sh > sravanth_logs/WATCH_SLICES_<method>_$(date +%d_%m_%Y).log 2>&1 &
```
On each slice's convergence this kills that slice's LAMP process, builds a 4-row snapshot (uniform anchor / best heuristic anchor / best random / best overall), and launches a full-500 eval on the freed GPU automatically — writing `RULER_ALL_B{T}/<method>/top_configs/eval_results.csv`.

### If a slice needs to be manually resumed after an out-of-band eval
(e.g. the watcher's staleness rule triggers prematurely — this happened once for SnapKV/B1536; see `Status.md`)
```bash
NAS_TARGET_BUDGET=<T> CUDA_VISIBLE_DEVICES=<gpu> NAS_METHOD=<method> \
    NAS_ANCHOR_FILE=anchors/anchor_<method>_<avgbudget>.txt \
    bash resume_b1536_after_eval.sh <eval_pid>

NAS_TARGET_BUDGET=<T> GPU=<gpu> NAS_METHOD=<method> EVALUATED_BEST=<known best score> \
    nohup bash watch_b1536_resume.sh > sravanth_logs/WATCH_RESUME_<method>_B<T>_$(date +%d_%m_%Y).log 2>&1 &
```
All four env vars are optional — every one defaults to the original B1536/SnapKV values, so omitting them all reproduces the exact original incident-recovery invocation.

### Best-BO eval, if you want it as its own table column
The auto-eval above already includes "best overall" (which is the best-BO row whenever BO beat the anchors/random). To force a *dedicated* eval of just the best BO-phase row (rows 65+) even when it tied or lost to the winner shape:
```bash
python3 - <<'PY'
import numpy as np
T = <budget>; method = "<method>"
d = np.loadtxt(f"RULER_ALL_B{T}/{method}/output.txt")
bo = d[64:]
i = int(np.argmin(bo[:, -1]))
np.savetxt(f"RULER_ALL_B{T}/{method}/top_configs/bo_best_snapshot.txt", bo[i:i+1])
PY

CUDA_VISIBLE_DEVICES=<gpu> NAS_GPUS="" NAS_TARGET_BUDGET=<budget> NAS_METHOD=<method> \
    NAS_TASK_CATEGORY=RULER_ALL_B<budget> \
    python3 eval_top_configs_ruler.py RULER_ALL_B<budget> --method <method> \
    --all_rows --sample_ratio 1.0 --output_file RULER_ALL_B<budget>/<method>/top_configs/bo_best_snapshot.txt
```
Back up `top_configs/eval_results.csv` first (`cp -n eval_results.csv eval_results_<label>.csv`) since `eval_top_configs_ruler.py` always writes that fixed filename — this is the same backup/rename dance used throughout Step 4.

## Consolidating results

Match the SnapKV format (`Constrained_NAS_Results/RULER/Average_Results_17_08_2026.md` and `All_Results_17_08_2026.csv`): one row per (budget, config) with uniform / winner-shape / best-random / best-BO, fitness-score and full-500-score side by side, plus the 11-subtask breakdown from each `eval_results.csv`.

## Cross-machine caveat (AdaKV specifically)

`Status.md` already documents that AdaKV scores differ between "LLM WS" and this machine ("SNAPNAS") due to differing torch versions. **Do the FINAL full-500 evals for any one comparison table on a single consistent machine** — don't mix an LLM-WS-evaluated config with a SNAPNAS-evaluated one in the same row.

## Parallelism / GPU notes

Step 1 (unconstrained) defaults to a 3-GPU worker pool for ONE search — don't also try to run Step 4 for the same method at the same time unless you have GPUs to spare. Step 4 needs 3 GPUs for 3 concurrent single-GPU slice searches (`NAS_GPUS` left empty per slice — sequential candidate evaluation within each slice, parallel across slices). Step 3 is cheap enough to run on a single free GPU (`--gpu <id>`) alongside anything else.
