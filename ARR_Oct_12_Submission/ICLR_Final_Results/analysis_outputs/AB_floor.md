# Controlled floor ablation (SnapKV, same rescaled winner, floor 16 vs 64; full data)

| Cell | uniform | winner, floor 64 | winner, floor 16 | Δ (16 - 64) | layers at floor (64 / 16 version) |
|---|---|---|---|---|---|
| CODE B128 | 54.81 | 55.86 | 54.76 | -1.10 | 19 / 0 |
| CODE B256 | 55.67 | 57.33 | 57.30 | -0.02 | 15 / 0 |
| SINGLE_DOCUMENT_QA B128 | 32.97 | 33.51 | 33.14 | -0.37 | 16 / 0 |
| SINGLE_DOCUMENT_QA B256 | 35.25 | 34.51 | 34.77 | +0.26 | 13 / 0 |
| MULTI_DOCUMENT_QA B128 | 34.82 | 35.02 | 34.32 | -0.70 | 24 / 0 |
| MULTI_DOCUMENT_QA B256 | 35.60 | 36.31 | 36.31 | +0.00 | 0 / 0 |
