# Search-budget curve (SnapKV, Llama-3-8B-Instruct, full data, local A100)

Best config by calibration among the first k rows of the Stage-4 search; k=64 is the initial design only, k=all is the paper's NAS-refined. Δ is vs the cell's uniform.

| Cell | k | row (type) | calibration | full-data | Δ vs uniform |
|---|---|---|---|---|---|
| CODE B128 | 64 | 1 (heuristic) | 62.97 | 55.73 | +0.91 |
| CODE B128 | 96 | 1 (heuristic) | 62.97 | 55.73 | +0.91 |
| CODE B128 | 128 | 1 (heuristic) | 62.97 | 55.73 | +0.91 |
| CODE B128 | 160 | 1 (heuristic) | 62.97 | 55.73 | +0.91 |
| CODE B128 | 200 | 1 (heuristic) | 62.97 | 55.73 | +0.91 |
| CODE B128 | all (542) | 453 (bo) | 63.60 | 56.09 | +1.28 |
| CODE B256 | 64 | 55 (random) | 64.48 | 55.99 | +0.32 |
| CODE B256 | 96 | 55 (random) | 64.48 | 55.99 | +0.32 |
| CODE B256 | 128 | 55 (random) | 64.48 | 55.99 | +0.32 |
| CODE B256 | 160 | 55 (random) | 64.48 | 55.99 | +0.32 |
| CODE B256 | 200 | 55 (random) | 64.48 | 55.99 | +0.32 |
| CODE B256 | all (216) | 55 (random) | 64.48 | 55.99 | +0.32 |
| CODE B512 | 64 | 25 (random) | 63.42 | 57.77 | +1.04 |
| CODE B512 | 96 | 25 (random) | 63.42 | 57.77 | +1.04 |
| CODE B512 | 128 | 107 (bo) | 63.74 | 55.66 | -1.07 |
| CODE B512 | all (148) | 107 (bo) | 63.74 | 55.66 | -1.07 |
| CODE B1024 | 64 | 25 (random) | 65.16 | 58.91 | +2.89 |
| CODE B1024 | 96 | 25 (random) | 65.16 | 58.91 | +2.89 |
| CODE B1024 | all (125) | 25 (random) | 65.16 | 58.91 | +2.89 |
| SINGLE_DOCUMENT_QA B128 | 64 | 3 (heuristic) | 37.05 | 33.67 | +0.70 |
| SINGLE_DOCUMENT_QA B128 | 96 | 3 (heuristic) | 37.05 | 33.67 | +0.70 |
| SINGLE_DOCUMENT_QA B128 | 128 | 3 (heuristic) | 37.05 | 33.67 | +0.70 |
| SINGLE_DOCUMENT_QA B128 | 160 | 138 (bo) | 37.47 | 32.86 | -0.11 |
| SINGLE_DOCUMENT_QA B128 | 200 | 138 (bo) | 37.47 | 32.86 | -0.11 |
| SINGLE_DOCUMENT_QA B128 | all (1000) | 236 (bo) | 37.71 | 33.45 | +0.48 |
| SINGLE_DOCUMENT_QA B256 | 64 | 0 (uniform) | 39.88 | 35.25 | +0.00 |
| SINGLE_DOCUMENT_QA B256 | 96 | 0 (uniform) | 39.88 | 35.25 | +0.00 |
| SINGLE_DOCUMENT_QA B256 | 128 | 0 (uniform) | 39.88 | 35.25 | +0.00 |
| SINGLE_DOCUMENT_QA B256 | 160 | 0 (uniform) | 39.88 | 35.25 | +0.00 |
| SINGLE_DOCUMENT_QA B256 | 200 | 0 (uniform) | 39.88 | 35.25 | +0.00 |
| SINGLE_DOCUMENT_QA B256 | all (501) | 0 (uniform) | 39.88 | 35.25 | +0.00 |
| SINGLE_DOCUMENT_QA B512 | 64 | 28 (random) | 40.65 | 35.28 | -0.69 |
| SINGLE_DOCUMENT_QA B512 | 96 | 28 (random) | 40.65 | 35.28 | -0.69 |
| SINGLE_DOCUMENT_QA B512 | 128 | 28 (random) | 40.65 | 35.28 | -0.69 |
| SINGLE_DOCUMENT_QA B512 | all (152) | 28 (random) | 40.65 | 35.28 | -0.69 |
| SINGLE_DOCUMENT_QA B1024 | 64 | 31 (random) | 40.54 | 37.01 | +0.57 |
| SINGLE_DOCUMENT_QA B1024 | 96 | 31 (random) | 40.54 | 37.01 | +0.57 |
| SINGLE_DOCUMENT_QA B1024 | 128 | 31 (random) | 40.54 | 37.01 | +0.57 |
| SINGLE_DOCUMENT_QA B1024 | 160 | 31 (random) | 40.54 | 37.01 | +0.57 |
| SINGLE_DOCUMENT_QA B1024 | 200 | 31 (random) | 40.54 | 37.01 | +0.57 |
| SINGLE_DOCUMENT_QA B1024 | all (211) | 31 (random) | 40.54 | 37.01 | +0.57 |

**Mean Δ vs uniform by k (cells with a value at that k; k=all uses each cell's full length)**

| k | mean Δ | cells |
|---|---|---|
| 64 | +0.72 | 8 |
| 96 | +0.72 | 8 |
| 128 | +0.11 | 7 |
| 160 | +0.34 | 5 |
| 200 | +0.34 | 5 |
| all | +0.47 | 8 |
