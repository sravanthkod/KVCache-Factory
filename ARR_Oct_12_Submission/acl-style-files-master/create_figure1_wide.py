#!/usr/bin/env python3
"""Generate Figure 1: LAMP Method Overview as a wide professional diagram (2-column)."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# Create WIDER figure for 2-column layout
fig, ax = plt.subplots(figsize=(14, 4.5))
ax.set_xlim(0, 14)
ax.set_ylim(0, 4.5)
ax.axis('off')

# Color scheme
color_stage = '#2E86AB'  # Professional blue
color_output = '#A23B72'  # Professional purple
color_arrow = '#333333'  # Dark gray
color_text = '#000000'

# ===== STAGE 1 =====
stage1_x, stage1_y = 2.0, 2.5
rect1 = FancyBboxPatch((stage1_x - 0.9, stage1_y - 0.5), 1.8, 1.0,
                        boxstyle="round,pad=0.12",
                        edgecolor=color_stage, facecolor='#E8F4F8',
                        linewidth=3)
ax.add_patch(rect1)
ax.text(stage1_x, stage1_y + 0.15, 'STEP 1', ha='center', va='center',
        fontsize=12, fontweight='bold', color=color_stage)
ax.text(stage1_x, stage1_y - 0.30, 'Unconstrained', ha='center', va='center',
        fontsize=10, color=color_text)
ax.text(stage1_x, stage1_y - 0.60, 'NAS', ha='center', va='center',
        fontsize=10, color=color_text, fontweight='bold')

# Output 1
out1_y = stage1_y - 1.4
rect_out1 = FancyBboxPatch((stage1_x - 0.85, out1_y - 0.45), 1.7, 0.9,
                           boxstyle="round,pad=0.08",
                           edgecolor=color_output, facecolor='#F3E5F5',
                           linewidth=2)
ax.add_patch(rect_out1)
ax.text(stage1_x, out1_y + 0.10, '100 BO iterations', ha='center', va='center',
        fontsize=9, color=color_output, fontweight='bold')
ax.text(stage1_x, out1_y - 0.25, '7 shapes + 57 LHS', ha='center', va='center',
        fontsize=8.5, color=color_text)

# Arrow 1 -> Output 1
arrow_down1 = FancyArrowPatch((stage1_x, stage1_y - 0.5), (stage1_x, out1_y + 0.45),
                             arrowstyle='->', mutation_scale=25, linewidth=2.5,
                             color=color_arrow, linestyle='dashed', alpha=0.7)
ax.add_patch(arrow_down1)

# ===== STAGE 2 =====
stage2_x, stage2_y = 6.5, 2.5
rect2 = FancyBboxPatch((stage2_x - 0.9, stage2_y - 0.5), 1.8, 1.0,
                        boxstyle="round,pad=0.12",
                        edgecolor=color_stage, facecolor='#E8F4F8',
                        linewidth=3)
ax.add_patch(rect2)
ax.text(stage2_x, stage2_y + 0.15, 'STEP 2', ha='center', va='center',
        fontsize=12, fontweight='bold', color=color_stage)
ax.text(stage2_x, stage2_y - 0.30, 'Pareto Front', ha='center', va='center',
        fontsize=10, color=color_text)
ax.text(stage2_x, stage2_y - 0.60, 'Evaluation', ha='center', va='center',
        fontsize=10, color=color_text, fontweight='bold')

# Output 2
out2_y = stage2_y - 1.4
rect_out2 = FancyBboxPatch((stage2_x - 0.85, out2_y - 0.45), 1.7, 0.9,
                           boxstyle="round,pad=0.08",
                           edgecolor=color_output, facecolor='#F3E5F5',
                           linewidth=2)
ax.add_patch(rect_out2)
ax.text(stage2_x, out2_y + 0.10, '13 configs', ha='center', va='center',
        fontsize=9, color=color_output, fontweight='bold')
ax.text(stage2_x, out2_y - 0.25, 'Winner shape extracted', ha='center', va='center',
        fontsize=8.5, color=color_text)

# Arrow 2 -> Output 2
arrow_down2 = FancyArrowPatch((stage2_x, stage2_y - 0.5), (stage2_x, out2_y + 0.45),
                             arrowstyle='->', mutation_scale=25, linewidth=2.5,
                             color=color_arrow, linestyle='dashed', alpha=0.7)
ax.add_patch(arrow_down2)

# ===== STAGE 3 =====
stage3_x, stage3_y = 11.0, 2.5
rect3 = FancyBboxPatch((stage3_x - 0.9, stage3_y - 0.5), 1.8, 1.0,
                        boxstyle="round,pad=0.12",
                        edgecolor=color_stage, facecolor='#E8F4F8',
                        linewidth=3)
ax.add_patch(rect3)
ax.text(stage3_x, stage3_y + 0.15, 'STEP 3', ha='center', va='center',
        fontsize=12, fontweight='bold', color=color_stage)
ax.text(stage3_x, stage3_y - 0.30, 'Budget-Constrained', ha='center', va='center',
        fontsize=10, color=color_text)
ax.text(stage3_x, stage3_y - 0.60, 'Search', ha='center', va='center',
        fontsize=10, color=color_text, fontweight='bold')

# Output 3
out3_y = stage3_y - 1.4
rect_out3 = FancyBboxPatch((stage3_x - 0.85, out3_y - 0.45), 1.7, 0.9,
                           boxstyle="round,pad=0.08",
                           edgecolor=color_output, facecolor='#F3E5F5',
                           linewidth=2)
ax.add_patch(rect_out3)
ax.text(stage3_x, out3_y + 0.10, 'Per-budget BO', ha='center', va='center',
        fontsize=9, color=color_output, fontweight='bold')
ax.text(stage3_x, out3_y - 0.25, 'Final evaluation', ha='center', va='center',
        fontsize=8.5, color=color_text)

# Arrow 3 -> Output 3
arrow_down3 = FancyArrowPatch((stage3_x, stage3_y - 0.5), (stage3_x, out3_y + 0.45),
                             arrowstyle='->', mutation_scale=25, linewidth=2.5,
                             color=color_arrow, linestyle='dashed', alpha=0.7)
ax.add_patch(arrow_down3)

# ===== HORIZONTAL FLOW ARROWS =====
arrow_1to2 = FancyArrowPatch((stage1_x + 0.9, stage1_y), (stage2_x - 0.9, stage2_y),
                            arrowstyle='->', mutation_scale=30, linewidth=3,
                            color=color_stage)
ax.add_patch(arrow_1to2)

arrow_2to3 = FancyArrowPatch((stage2_x + 0.9, stage2_y), (stage3_x - 0.9, stage3_y),
                            arrowstyle='->', mutation_scale=30, linewidth=3,
                            color=color_stage)
ax.add_patch(arrow_2to3)

# ===== STAGE LABELS =====
ax.text(stage1_x, 4.0, 'Initialize & Explore', ha='center', va='bottom',
        fontsize=10, style='italic', color='#555555', fontweight='bold')
ax.text(stage2_x, 4.0, 'Select Winner', ha='center', va='bottom',
        fontsize=10, style='italic', color='#555555', fontweight='bold')
ax.text(stage3_x, 4.0, 'Optimize under Budget', ha='center', va='bottom',
        fontsize=10, style='italic', color='#555555', fontweight='bold')

plt.tight_layout()
plt.savefig('figures/figure1_method_diagram.pdf', dpi=300, bbox_inches='tight', format='pdf', facecolor='white')
print("✓ Figure 1 (2-column wide) saved as PDF: figures/figure1_method_diagram.pdf")

plt.savefig('figures/figure1_method_diagram.png', dpi=150, bbox_inches='tight', format='png', facecolor='white')
print("✓ Figure 1 (PNG preview) saved: figures/figure1_method_diagram.png")

plt.close()
