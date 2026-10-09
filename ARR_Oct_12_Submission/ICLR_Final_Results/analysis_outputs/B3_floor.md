## B3 — Why the per-layer floor is 64, not 16

SnapKV/H2O always keep a fixed **8-token recent window** (`window_size=8`, `run_longbench_lamp.py:314-318`), enforced by `assert max_capacity_prompt - window_size > 0` in `SnapKVCluster`/`H2OKVCluster`. A layer with budget *b* therefore selects only *b − 8* tokens by attention score from the whole context.

| Per-layer budget | Recent window (always kept) | Attention-selected tokens |
|---|---|---|
| 16 | 8 | 8 |
| 32 | 8 | 24 |
| 64 | 8 | 56 |
| 128 | 8 | 120 |

At budget 16 only 8 tokens are chosen from a context of thousands — effectively noise. Raising the floor to 64 gives 56 selected tokens (7×).

**How often the best-scoring config parks layers exactly at the floor** (best = highest full-data score among the evaluated configs of each cell):

| Benchmark | Category | Budget | Method | Floor in effect | Best label | Layers at floor | Share |
|---|---|---|---|---|---|---|---|
| longbench | CODE | 128 | h2o | 64 | bo | 18/32 | 56% |
| longbench | CODE | 128 | snapkv | 64 | bo | 16/32 | 50% |
| longbench | CODE | 256 | h2o | 64 | winner | 8/32 | 25% |
| longbench | CODE | 256 | snapkv | 64 | winner | 15/32 | 47% |
| longbench | CODE | 512 | h2o | 64 | heuristic | 2/32 | 6% |
| longbench | CODE | 512 | snapkv | 64 | winner | 0/32 | 0% |
| longbench | CODE | 1024 | h2o | 64 | random | 1/32 | 3% |
| longbench | CODE | 1024 | snapkv | 64 | random | 1/32 | 3% |
| longbench | MULTI_DOCUMENT_QA | 128 | h2o | 64 | uniform | 0/32 | 0% |
| longbench | MULTI_DOCUMENT_QA | 128 | snapkv | 64 | winner | 24/32 | 75% |
| longbench | MULTI_DOCUMENT_QA | 256 | h2o | 64 | random | 4/32 | 12% |
| longbench | MULTI_DOCUMENT_QA | 256 | snapkv | 64 | winner | 0/32 | 0% |
| longbench | MULTI_DOCUMENT_QA | 512 | h2o | 64 | winner | 0/32 | 0% |
| longbench | MULTI_DOCUMENT_QA | 512 | snapkv | 64 | uniform | 0/32 | 0% |
| longbench | MULTI_DOCUMENT_QA | 1024 | h2o | 64 | bo | 17/32 | 53% |
| longbench | MULTI_DOCUMENT_QA | 1024 | snapkv | 64 | winner | 0/32 | 0% |
| longbench | SINGLE_DOCUMENT_QA | 128 | h2o | 64 | random | 9/32 | 28% |
| longbench | SINGLE_DOCUMENT_QA | 128 | snapkv | 64 | heuristic | 8/32 | 25% |
| longbench | SINGLE_DOCUMENT_QA | 256 | h2o | 64 | random | 3/32 | 9% |
| longbench | SINGLE_DOCUMENT_QA | 256 | snapkv | 64 | uniform | 0/32 | 0% |
| longbench | SINGLE_DOCUMENT_QA | 512 | h2o | 64 | heuristic | 1/32 | 3% |
| longbench | SINGLE_DOCUMENT_QA | 512 | snapkv | 64 | winner | 0/32 | 0% |
| longbench | SINGLE_DOCUMENT_QA | 1024 | h2o | 64 | heuristic | 0/32 | 0% |
| longbench | SINGLE_DOCUMENT_QA | 1024 | snapkv | 64 | random | 1/32 | 3% |
| longbench | SUMMARIZATION | 128 | h2o | 64 | bo | 13/32 | 41% |
| longbench | SUMMARIZATION | 128 | snapkv | 64 | winner | 8/32 | 25% |
| longbench | SUMMARIZATION | 256 | h2o | 64 | random | 6/32 | 19% |
| longbench | SUMMARIZATION | 512 | h2o | 64 | winner | 0/32 | 0% |
| longbench | SUMMARIZATION | 1024 | h2o | 64 | heuristic | 0/32 | 0% |
| ruler | RULER_ALL | 128 | h2o | 64 | bo | 19/32 | 59% |
| ruler | RULER_ALL | 128 | snapkv | 64 | winner | 14/32 | 44% |
| ruler | RULER_ALL | 256 | snapkv | 64 | winner | 11/32 | 34% |
| ruler | RULER_ALL | 1024 | h2o | 16 | bo | 21/32 | 66% |
| ruler | RULER_ALL | 1024 | snapkv | 16 | bo | 10/32 | 31% |
| ruler | RULER_ALL | 1536 | h2o | 16 | bo | 0/32 | 0% |
| ruler | RULER_ALL | 1536 | snapkv | 16 | winner | 0/32 | 0% |
| ruler | RULER_ALL | 2048 | h2o | 64 | bo | 0/32 | 0% |
| ruler | RULER_ALL | 2048 | snapkv | 16 | winner | 0/32 | 0% |

Reading: when the floor was 16, the search pushed up to two-thirds of layers (RULER B1024, H2O) down into the 8-selected-token regime — exploiting a degenerate setting rather than finding a meaningful allocation — while at B1536/B2048 it never needed to (0 layers), so those results are floor-independent. Under floor=64 many best configs still sit a large share of layers at the floor, i.e. the floor is an active constraint and the choice of value matters.
