#!/usr/bin/env python3
"""Generate Figure 1: LAMP Method Overview as a professional diagram."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# Create figure
fig, ax = plt.subplots(figsize=(12, 4))
ax.set_xlim(0, 12)
ax.set_ylim(0, 4)
ax.axis('off')

# Color scheme
color_stage = '#2E86AB'  # Professional blue
color_output = '#A23B72'  # Professional purple
color_arrow = '#333333'  # Dark gray
color_text = '#000000'

# Stage 1
stage1_x, stage1_y = 1.5, 2.2
rect1 = FancyBboxPatch((stage1_x - 0.8, stage1_y - 0.4), 1.6, 0.8,
                        boxstyle="round,pad=0.1",
                        edgecolor=color_stage, facecolor='#E8F4F8',
                        linewidth=2.5)
ax.add_patch(rect1)
ax.text(stage1_x, stage1_y + 0.05, 'Step 1', ha='center', va='center',
        fontsize=11, fontweight='bold', color=color_stage)
ax.text(stage1_x, stage1_y - 0.25, 'Unconstrained NAS', ha='center', va='center',
        fontsize=9, color=color_text)

# Output 1
out1_y = stage1_y - 1.2
rect_out1 = FancyBboxPatch((stage1_x - 0.75, out1_y - 0.35), 1.5, 0.7,
                           boxstyle="round,pad=0.05",
                           edgecolor=color_output, facecolor='#F3E5F5',
                           linewidth=1.5)
ax.add_patch(rect_out1)
ax.text(stage1_x, out1_y + 0.05, '100 BO iters', ha='center', va='center',
        fontsize=8, color=color_output, fontweight='bold')
ax.text(stage1_x, out1_y - 0.18, '7 shapes + 57 LHS', ha='center', va='center',
        fontsize=7.5, color=color_text)

# Arrow 1 -> Output 1
arrow_down1 = FancyArrowPatch((stage1_x, stage1_y - 0.4), (stage1_x, out1_y + 0.35),
                             arrowstyle='->', mutation_scale=20, linewidth=2,
                             color=color_arrow, linestyle='dashed', alpha=0.6)
ax.add_patch(arrow_down1)

# Stage 2
stage2_x, stage2_y = 5.5, 2.2
rect2 = FancyBboxPatch((stage2_x - 0.8, stage2_y - 0.4), 1.6, 0.8,
                        boxstyle="round,pad=0.1",
                        edgecolor=color_stage, facecolor='#E8F4F8',
                        linewidth=2.5)
ax.add_patch(rect2)
ax.text(stage2_x, stage2_y + 0.05, 'Step 2', ha='center', va='center',
        fontsize=11, fontweight='bold', color=color_stage)
ax.text(stage2_x, stage2_y - 0.25, 'Pareto Eval', ha='center', va='center',
        fontsize=9, color=color_text)

# Output 2
out2_y = stage2_y - 1.2
rect_out2 = FancyBboxPatch((stage2_x - 0.75, out2_y - 0.35), 1.5, 0.7,
                           boxstyle="round,pad=0.05",
                           edgecolor=color_output, facecolor='#F3E5F5',
                           linewidth=1.5)
ax.add_patch(rect_out2)
ax.text(stage2_x, out2_y + 0.05, '13 configs', ha='center', va='center',
        fontsize=8, color=color_output, fontweight='bold')
ax.text(stage2_x, out2_y - 0.18, 'Winner shape', ha='center', va='center',
        fontsize=7.5, color=color_text)

# Arrow 2 -> Output 2
arrow_down2 = FancyArrowPatch((stage2_x, stage2_y - 0.4), (stage2_x, out2_y + 0.35),
                             arrowstyle='->', mutation_scale=20, linewidth=2,
                             color=color_arrow, linestyle='dashed', alpha=0.6)
ax.add_patch(arrow_down2)

# Stage 3
stage3_x, stage3_y = 9.5, 2.2
rect3 = FancyBboxPatch((stage3_x - 0.8, stage3_y - 0.4), 1.6, 0.8,
                        boxstyle="round,pad=0.1",
                        edgecolor=color_stage, facecolor='#E8F4F8',
                        linewidth=2.5)
ax.add_patch(rect3)
ax.text(stage3_x, stage3_y + 0.05, 'Step 3', ha='center', va='center',
        fontsize=11, fontweight='bold', color=color_stage)
ax.text(stage3_x, stage3_y - 0.25, 'Budget Search', ha='center', va='center',
        fontsize=9, color=color_text)

# Output 3
out3_y = stage3_y - 1.2
rect_out3 = FancyBboxPatch((stage3_x - 0.75, out3_y - 0.35), 1.5, 0.7,
                           boxstyle="round,pad=0.05",
                           edgecolor=color_output, facecolor='#F3E5F5',
                           linewidth=1.5)
ax.add_patch(rect_out3)
ax.text(stage3_x, out3_y + 0.05, 'Per-budget BO', ha='center', va='center',
        fontsize=8, color=color_output, fontweight='bold')
ax.text(stage3_x, out3_y - 0.18, 'Final eval', ha='center', va='center',
        fontsize=7.5, color=color_text)

# Arrow 3 -> Output 3
arrow_down3 = FancyArrowPatch((stage3_x, stage3_y - 0.4), (stage3_x, out3_y + 0.35),
                             arrowstyle='->', mutation_scale=20, linewidth=2,
                             color=color_arrow, linestyle='dashed', alpha=0.6)
ax.add_patch(arrow_down3)

# Horizontal arrows between stages
arrow_1to2 = FancyArrowPatch((stage1_x + 0.8, stage1_y), (stage2_x - 0.8, stage2_y),
                            arrowstyle='->', mutation_scale=25, linewidth=2.5,
                            color=color_stage)
ax.add_patch(arrow_1to2)

arrow_2to3 = FancyArrowPatch((stage2_x + 0.8, stage2_y), (stage3_x - 0.8, stage3_y),
                            arrowstyle='->', mutation_scale=25, linewidth=2.5,
                            color=color_stage)
ax.add_patch(arrow_2to3)

# Labels for stages
ax.text(stage1_x, 3.5, 'Initialize', ha='center', va='bottom',
        fontsize=9, style='italic', color='#666666')
ax.text(stage2_x, 3.5, 'Select', ha='center', va='bottom',
        fontsize=9, style='italic', color='#666666')
ax.text(stage3_x, 3.5, 'Optimize', ha='center', va='bottom',
        fontsize=9, style='italic', color='#666666')

plt.tight_layout()
plt.savefig('figures/figure1_method_diagram.pdf', dpi=300, bbox_inches='tight', format='pdf', facecolor='white')
print("✓ Figure 1 (method diagram) saved as PDF: figures/figure1_method_diagram.pdf")

plt.savefig('figures/figure1_method_diagram.png', dpi=150, bbox_inches='tight', format='png', facecolor='white')
print("✓ Figure 1 (PNG preview) saved: figures/figure1_method_diagram.png")

plt.close()
