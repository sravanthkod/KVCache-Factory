#!/usr/bin/env python3
"""
Plot comparison for the MULTI_DOCUMENT_QA task.

- X axis : Avg Score (higher is better)
- Y axis : Avg Budget (larger budgets consume more resources)
- Blue line/markers   : Our evaluated configurations (provided by the user)
- Red line/markers    : SnapKV baseline scores (provided by the user)

The script creates a Matplotlib figure and saves it as ``plot_configs.png`` in the
same directory.  The original version of this script is retained below as a
commented‑out reference.
"""

import matplotlib.pyplot as plt

# ----------------------------------------------------------------------
# Our evaluated configurations (MULTI_DOCUMENT_QA)
# ----------------------------------------------------------------------
# Data extracted from the table supplied by the user:
# | # | Avg Budget | Evicted Attn | hotpotqa | 2wikimqa | musique | Avg Score |
# |---|------------|--------------|----------|----------|---------|-----------|
# | 0 | 64  | -19.877 | 25.92 | 19.67 | 5.20 | 16.93 |
# | 1 |80  | -20.080 | 26.80 | 19.20 | 5.90 | 17.30 |
# | 2 | 82  | -21.717 | 25.98 | 21.69 | 6.65 | 18.11 |
# | 3 | 116 | -22.433 | 26.45 | 22.08 | 7.14 | 18.56 |
# | 4 | 140 | -22.583 | 27.47 | 21.32 | 7.89 | 18.89 |
# | 5 | 166 | -22.827 | 28.94 | 24.01 | 7.73 | 20.23 |
# | 6 | 194 | -23.390 | 28.33 | 23.92 | 8.34 | 20.20 |
# | 7 | 212 | -23.423 | 27.12 | 23.90 | 7.72 | 19.58 |
# | 8 | 244 | -23.993 | 29.47 | 23.24 | 7.24 | 19.98 |
# | 9 | 290 | -25.156 | 31.06 | 23.86 |10.19 | 21.70 |
# |10 | 452 | -25.343 | 30.90 | 25.38 | 9.55 | 21.94 |
our_budgets = [
    64, 80, 82, 116, 140, 166, 194, 212, 244, 290, 452
]

our_scores = [
    16.93, 17.30, 18.11, 18.56, 18.89,
    20.23, 20.20, 19.58, 19.98, 21.70, 21.94
]

# ----------------------------------------------------------------------
# SnapKV baseline (provided by the user)
# ----------------------------------------------------------------------
# Budgets and the corresponding average scores for the same task.
baseline_budgets = [64, 128, 256, 512, 1024]
baseline_scores = [16.93, 18.94, 21.58, 21.89, 21.92]

# ----------------------------------------------------------------------
# Plotting
# ----------------------------------------------------------------------
plt.figure(figsize=(8, 5))

# Our configurations – blue
plt.plot(
    our_budgets,               # X = Avg Budget
    our_scores,                # Y = Avg Score
    marker='o',
    color='blue',
    label='Our Configs (MULTI_DOCUMENT_QA)'
)

# SnapKV baseline – red
plt.plot(
    baseline_budgets,
    baseline_scores,
    marker='o',
    color='red',
    label='SnapKV Baseline'
)

plt.title('Avg Score vs Avg Budget (MULTI_DOCUMENT_QA)')
plt.xlabel('Avg Budget')
plt.ylabel('Avg Score')
plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
plt.legend()
plt.tight_layout()

# Save the figure
output_path = '/home/snap_nas/sravanth/LLM/Token_Eviction/Dynamic_Methods/PyramidKV/NAS_Assets/plot_configs.png'
plt.savefig(output_path, dpi=300)
print(f'Plot saved to {output_path}')

# ----------------------------------------------------------------------
# Previous version (commented out for reference)
# ----------------------------------------------------------------------
# import matplotlib.pyplot as plt
# 
# # Our configurations (Avg Budget, Avg Score)
# # our_budgets = [...]
# # our_scores = [...]
# 
# # SnapKV baseline (Avg Budget, Avg Score)
# # baseline_budgets = [64, 128, 256, 512, 1024]
# # baseline_scores = [17.16, 19.69, 21.70, 23.49, 24.81]
# 
# # plt.figure(figsize=(8, 5))
# # plt.plot(our_budgets, our_scores, marker='o', color='blue', label='Our Configs')
# # plt.plot(baseline_budgets, baseline_scores, marker='o', color='red', label='SnapKV Baseline')
# # plt.title('Avg Score vs. Avg Budget')
# # plt.xlabel('Average Budget')
# # plt.ylabel('Avg Score')
# # plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
# # plt.legend()
# # plt.tight_layout()
# # output_path = '/home/snap_nas/sravanth/LLM/Token_Eviction/Dynamic_Methods/PyramidKV/NAS_Assets/plot_configs.png'
# # plt.savefig(output_path, dpi=300)
# # print(f'Plot saved to {output_path}')
