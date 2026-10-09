#!/usr/bin/env python3
"""Create an amazing block diagram for Figure 1: LAMP 4-Stage Pipeline."""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import numpy as np

# Create figure
fig, ax = plt.subplots(figsize=(16, 10))
ax.set_xlim(0, 16)
ax.set_ylim(0, 10)
ax.axis('off')

# Colors
color_primary = '#2E86AB'      # Professional blue
color_secondary = '#A23B72'    # Professional purple
color_light = '#E8F4F8'        # Light blue background
color_light_purple = '#F3E5F5' # Light purple background
color_text = '#000000'         # Black text
color_arrows = '#333333'       # Dark gray

# Y positions for stages
y_positions = [8, 6, 4, 2]
stage_labels = [
    "STAGE 1:\nUnconstrained\nMulti-Budget NAS",
    "STAGE 2:\nWinner Selection\n(Full-Data Eval)",
    "STAGE 3:\nWinner Rescaling\n(Universal Baseline)",
    "STAGE 4:\nBudget-Constrained\nAdaptive Search"
]

stage_inputs = [
    "7 shapes + 57 LHS\n100 BO iterations\n(no budget constraint)",
    "Pareto front (13 configs)\nEvaluate on full test data\nExtract best (Winner)",
    "Rescale winner to\nB ∈ {64, 128, 256, 512, 1024, 2048}\nEvaluate on full data",
    "Per-budget dedicated BO\nSeeded with Stage 3 winner\nFind budget-specific optimizations"
]

stage_outputs = [
    "Pareto-optimal\nallocation patterns\n",
    "Winner Shape\n(universal anchor)\n",
    "Winner-Rescaled configs\n(generalization baseline)\n",
    "Constrained NAS results\n(shown in Tables 1-2)\n"
]

# Draw stages
for i, (y, label, input_text, output_text) in enumerate(zip(y_positions, stage_labels, stage_inputs, stage_outputs)):

    # Main stage box
    stage_box = FancyBboxPatch((0.5, y - 0.6), 3.5, 1.2,
                               boxstyle="round,pad=0.15",
                               edgecolor=color_primary,
                               facecolor=color_light,
                               linewidth=3)
    ax.add_patch(stage_box)

    # Stage label
    ax.text(2.25, y + 0.25, label,
            ha='center', va='center',
            fontsize=11, fontweight='bold',
            color=color_primary)

    # Input box
    input_box = FancyBboxPatch((4.5, y - 0.5), 4.5, 1.0,
                               boxstyle="round,pad=0.1",
                               edgecolor='#666666',
                               facecolor='#F5F5F5',
                               linewidth=1.5, linestyle='--')
    ax.add_patch(input_box)

    ax.text(6.75, y, input_text,
            ha='center', va='center',
            fontsize=9, color=color_text,
            style='italic')

    # Input label
    ax.text(4.5, y + 0.65, "INPUT",
            ha='left', va='bottom',
            fontsize=8, fontweight='bold',
            color='#666666')

    # Output box
    output_box = FancyBboxPatch((10, y - 0.5), 5, 1.0,
                                boxstyle="round,pad=0.1",
                                edgecolor=color_secondary,
                                facecolor=color_light_purple,
                                linewidth=2)
    ax.add_patch(output_box)

    ax.text(12.5, y, output_text,
            ha='center', va='center',
            fontsize=9, fontweight='bold',
            color=color_secondary)

    # Output label
    ax.text(10, y + 0.65, "OUTPUT",
            ha='left', va='bottom',
            fontsize=8, fontweight='bold',
            color=color_secondary)

    # Arrow from stage to output
    arrow_stage_output = FancyArrowPatch((4.0, y), (10, y),
                                        arrowstyle='->', mutation_scale=25,
                                        linewidth=2, color=color_arrows, alpha=0.6)
    ax.add_patch(arrow_stage_output)

# Vertical flow arrows between stages
for i in range(len(y_positions) - 1):
    arrow_down = FancyArrowPatch((2.25, y_positions[i] - 0.7),
                                (2.25, y_positions[i+1] + 0.7),
                                arrowstyle='->', mutation_scale=30,
                                linewidth=3, color=color_primary, alpha=0.8)
    ax.add_patch(arrow_down)

# Title
ax.text(8, 9.5, 'LAMP: Four-Stage Neural Architecture Search Pipeline',
        ha='center', va='top',
        fontsize=14, fontweight='bold',
        color=color_primary)

# Legend/Summary box at bottom
summary_box = FancyBboxPatch((0.5, 0.1), 15, 0.7,
                            boxstyle="round,pad=0.08",
                            edgecolor=color_primary,
                            facecolor='#FFFACD',
                            linewidth=2, alpha=0.9)
ax.add_patch(summary_box)

summary_text = ("LAMP discovers per-layer KV-cache budgets in 4 stages: (1) unconstrained exploration to find high-performing patterns, "
                "(2) winner selection by full-data evaluation, (3) rescaling winner to multiple budgets as universal baseline, "
                "(4) budget-constrained adaptive search for optimal per-budget configurations shown in results tables.")

ax.text(8, 0.45, summary_text,
        ha='center', va='center',
        fontsize=8.5, color=color_text,
        wrap=True, style='italic')

plt.tight_layout(pad=0.5)
plt.savefig('figures/figure1_method_diagram.pdf', dpi=300, bbox_inches='tight',
            format='pdf', facecolor='white', pad_inches=0.3)
print("✓ Figure 1 (professional block diagram) saved as PDF")

plt.savefig('figures/figure1_method_diagram.png', dpi=150, bbox_inches='tight',
            format='png', facecolor='white', pad_inches=0.3)
print("✓ Figure 1 (PNG preview) saved")

plt.close()
print("\n✨ Amazing block diagram created!")
print("   • Properly sized boxes with contained text")
print("   • Clear visual hierarchy (Stage → Input → Output)")
print("   • Professional color scheme")
print("   • Bottom summary explaining the entire pipeline")
