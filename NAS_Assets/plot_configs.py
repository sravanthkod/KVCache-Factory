#!/usr/bin/env python3
"""
Generate a comparison plot of SnapKV baseline scores vs. our top configurations.

- X axis: Average Budget
- Y axis: Avg Score
- Red line/markers: SnapKV baseline
- Blue line/markers: Our configurations (from top_configs.md)
"""

import matplotlib.pyplot as plt

# Our configurations (Avg Budget, Avg Score)
our_budgets = [
    64, 66, 70, 72, 74, 76, 82, 84, 86, 88,
    92, 96, 112, 140, 150, 172, 174, 190,
    234, 246, 296, 316, 350
]
our_scores = [
    17.16, 17.54, 17.54, 19.06, 18.97, 18.84, 18.74, 19.44,
    19.08, 19.65, 20.36, 19.58, 20.85, 21.71, 21.77,
    21.88, 21.86, 22.21, 23.08, 22.70, 22.80, 22.70, 23.26
]

# SnapKV baseline (Avg Budget, Avg Score)
baseline_budgets = [64, 128, 256, 512, 1024]
baseline_scores = [17.16, 19.69, 21.70, 23.49, 24.81]

plt.figure(figsize=(8, 5))
# Plot our configs
plt.plot(our_budgets, our_scores, marker='o', color='blue', label='Our Configs')
# Plot baseline
plt.plot(baseline_budgets, baseline_scores, marker='o', color='red', label='SnapKV Baseline')

plt.title('Avg Score vs. Avg Budget')
plt.xlabel('Average Budget')
plt.ylabel('Avg Score')
plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
plt.legend()
plt.tight_layout()

# Save the figure
output_path = '/home/snap_nas/sravanth/LLM/Token_Eviction/Dynamic_Methods/PyramidKV/NAS_Assets/plot_configs.png'
plt.savefig(output_path, dpi=300)
print(f'Plot saved to {output_path}')
