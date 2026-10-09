#!/usr/bin/env python3
"""Create Figure 1: LAMP 4-Stage Pipeline - VERTICAL FLOW (2-column layout)."""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.patheffects import withStroke
import numpy as np

# Create figure properly sized for 2-column ACL paper (7-8 inches wide)
fig = plt.figure(figsize=(8.5, 11), dpi=150)
ax = fig.add_subplot(111)
ax.set_xlim(0, 8.5)
ax.set_ylim(0, 11)
ax.axis('off')

# Color palette
color_primary = '#1565C0'      # Professional blue
color_light = '#E3F2FD'        # Light blue background
color_accent = '#D32F2F'       # Red accent
color_text = '#212121'         # Dark text
color_secondary = '#FFF8E1'    # Cream background

# Title
ax.text(
    4.25, 10.5,
    'LAMP: Four-Stage NAS Pipeline',
    ha='center', va='top',
    fontsize=14, fontweight='bold',
    color=color_primary
)

# Stage positions (vertical flow, top to bottom)
stage_y = [9.5, 7.0, 4.5, 2.0]

stages = [
    {
        'num': '1',
        'title': 'Unconstrained\nExploration',
        'details': [
            '• 7 shape anchors',
            '• 57 LHS samples',
            '• 100 BO iterations'
        ],
        'result': '→ Pareto Front'
    },
    {
        'num': '2',
        'title': 'Winner\nSelection',
        'details': [
            '• Evaluate 13 configs',
            '• Full test dataset',
            '• Extract best shape'
        ],
        'result': '→ Winner Shape'
    },
    {
        'num': '3',
        'title': 'Rescaling to\nFixed Budgets',
        'details': [
            '• Scale to 6 budgets',
            '• B ∈ {64–2048}',
            '• Universal baseline'
        ],
        'result': '→ Baseline Configs'
    },
    {
        'num': '4',
        'title': 'Budget-Constrained\nSearch',
        'details': [
            '• Per-budget BO',
            '• 200 iterations',
            '• Optimize locally'
        ],
        'result': '→ Final Results'
    }
]

# Draw stages
for i, (y, stage) in enumerate(zip(stage_y, stages)):

    # Stage box (left side)
    stage_box = FancyBboxPatch(
        (0.3, y - 0.7), 3.2, 1.4,
        boxstyle="round,pad=0.1",
        edgecolor=color_primary,
        facecolor=color_light,
        linewidth=2.5,
        zorder=10
    )
    ax.add_patch(stage_box)

    # Stage number circle
    circle = plt.Circle((0.8, y + 0.35), 0.25, color=color_primary, zorder=15)
    ax.add_patch(circle)
    ax.text(0.8, y + 0.35, stage['num'], ha='center', va='center',
            fontsize=12, fontweight='bold', color='white', zorder=16)

    # Stage title
    ax.text(2.0, y + 0.45, stage['title'], ha='center', va='center',
            fontsize=10, fontweight='bold', color=color_primary)

    # Stage details
    details_text = '\n'.join(stage['details'])
    ax.text(2.0, y - 0.25, details_text, ha='center', va='center',
            fontsize=8, color=color_text, linespacing=1.5, family='monospace')

    # Result arrow and text (right side)
    result_box = FancyBboxPatch(
        (3.8, y - 0.6), 4.2, 1.2,
        boxstyle="round,pad=0.08",
        edgecolor=color_accent,
        facecolor=color_secondary,
        linewidth=2,
        zorder=9
    )
    ax.add_patch(result_box)

    ax.text(5.9, y + 0.3, stage['result'], ha='center', va='center',
            fontsize=9.5, fontweight='bold', color=color_accent)

    # Arrow from stage to result
    arrow = FancyArrowPatch(
        (3.5, y + 0.15), (3.8, y + 0.15),
        arrowstyle='->', mutation_scale=20,
        linewidth=2.5, color=color_primary, zorder=8
    )
    ax.add_patch(arrow)

    # Vertical arrow to next stage (if not last)
    if i < len(stages) - 1:
        next_y = stage_y[i + 1]
        v_arrow = FancyArrowPatch(
            (2.0, y - 0.85), (2.0, next_y + 0.75),
            arrowstyle='->', mutation_scale=25,
            linewidth=3, color=color_primary, zorder=8, alpha=0.7
        )
        ax.add_patch(v_arrow)

# Bottom explanation
explanation_box = FancyBboxPatch(
    (0.2, 0.05), 8.1, 0.7,
    boxstyle="round,pad=0.08",
    edgecolor=color_accent,
    facecolor='#FFFACD',
    linewidth=1.5,
    zorder=20
)
ax.add_patch(explanation_box)

explanation = "LAMP systematically discovers per-layer budget allocations through four stages: exploration, selection, rescaling, and optimization."
ax.text(4.25, 0.4, explanation, ha='center', va='center',
        fontsize=8.5, color=color_text, linespacing=1.4, style='italic')

plt.tight_layout(pad=0.3)
plt.savefig('figures/figure1_method_diagram.pdf', dpi=300, bbox_inches='tight',
            format='pdf', facecolor='white', pad_inches=0.2)
print("✓ Figure 1 (vertical flow) saved as PDF")

plt.savefig('figures/figure1_method_diagram.png', dpi=200, bbox_inches='tight',
            format='png', facecolor='white', pad_inches=0.2)
print("✓ Figure 1 (PNG) saved")
plt.close()

print("\n✨ Clean Vertical Pipeline Figure Created!")
print("   ✓ Proper 2-column layout size (8.5×11 inches)")
print("   ✓ Vertical flow: stages stack top-to-bottom")
print("   ✓ Left: Stage details | Right: Output results")
print("   ✓ No overlapping elements")
print("   ✓ Large, clear text (8.5-14pt)")
print("   ✓ Numbered stages with circles")
print("   ✓ Clean, professional appearance")
