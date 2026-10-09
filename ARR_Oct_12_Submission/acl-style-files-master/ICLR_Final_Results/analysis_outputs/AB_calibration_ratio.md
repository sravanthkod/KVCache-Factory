# Calibration-ratio study (CODE B512, SnapKV; 24/24 configs complete)

Calibration at 10% (from the search's own output.txt) and 30% vs full data for the same configs.

| ratio | mean gap (calib - full) | Kendall tau vs full | calib-picked = full-best | regret |
|---|---|---|---|---|
| 10% | +5.10 | +0.51 | no | 2.87 |
| 30% | +1.37 | +0.75 | yes | 0.00 |

| row (type) | calib 10% | calib 30% | full |
|---|---|---|---|
| 0 (uniform) | 60.75 | 57.34 | 56.73 |
| 1 (heuristic) | 62.27 | 58.91 | 58.01 |
| 4 (heuristic) | 60.84 | 55.76 | 54.62 |
| 5 (heuristic) | 60.48 | 55.96 | 55.39 |
| 6 (winner) | 62.30 | 59.13 | 58.16 |
| 9 (random) | 60.16 | 57.47 | 57.16 |
| 18 (random) | 62.64 | 60.65 | 58.53 |
| 25 (random) | 63.42 | 59.81 | 57.77 |
| 34 (random) | 59.78 | 58.19 | 57.49 |
| 36 (random) | 60.93 | 56.30 | 55.12 |
| 42 (random) | 61.76 | 57.83 | 56.11 |
| 43 (random) | 62.08 | 59.62 | 57.42 |
| 52 (random) | 61.62 | 57.31 | 56.83 |
| 55 (random) | 62.56 | 59.25 | 57.04 |
| 72 (bo) | 59.06 | 56.03 | 54.96 |
| 88 (bo) | 62.21 | 57.82 | 55.85 |
| 91 (bo) | 59.75 | 55.18 | 54.08 |
| 92 (bo) | 60.54 | 55.26 | 54.08 |
| 101 (bo) | 61.70 | 57.90 | 56.33 |
| 107 (bo) | 63.74 | 58.41 | 55.66 |
| 109 (bo) | 58.11 | 54.20 | 52.75 |
| 110 (bo) | 59.92 | 55.33 | 53.08 |
| 119 (bo) | 59.37 | 54.53 | 53.14 |
| 127 (bo) | 56.28 | 54.43 | 53.48 |
