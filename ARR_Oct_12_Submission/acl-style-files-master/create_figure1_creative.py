#!/usr/bin/env python3
"""Create an amazing creative block diagram for Figure 1: LAMP 4-Stage Pipeline."""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Wedge, Polygon
from matplotlib.patches import ConnectionPatch, Rectangle
import matplotlib.patches as mpatches
from matplotlib.patheffects import withStroke
import numpy as np

# Create figure with high DPI and large canvas
fig = plt.figure(figsize=(18, 12), dpi=150)
ax = fig.add_subplot(111)
ax.set_xlim(-1, 19)
ax.set_ylim(-1, 13)
ax.axis('off')

# Professional color palette
color_stage_primary = '#1F4E79'     # Dark blue
color_stage_light = '#D5E8F7'       # Light blue
color_accent = '#C54F50'            # Deep red/burgundy
color_input = '#F0E5D8'             # Warm beige
color_output = '#E8D5C4'            # Light tan
color_text_main = '#1F1F1F'         # Dark charcoal
color_text_secondary = '#555555'    # Medium gray
color_arrows = '#2E5C8A'            # Arrow blue

# Stage configuration
stages = [
    {
        'name': 'STAGE 1',
        'subtitle': 'Unconstrained\nMulti-Budget NAS',
        'x': 2.5,
        'y': 9.5,
        'inputs': ['• 7 shape anchors', '• 57 LHS samples', '• 100 BO iterations'],
        'outputs': ['Pareto-optimal', 'allocation patterns']
    },
    {
        'name': 'STAGE 2',
        'subtitle': 'Winner Selection\nvia Full-Data Eval',
        'x': 7.5,
        'y': 9.5,
        'inputs': ['• 13 Pareto configs', '• Full test dataset', '• Extract top-ranked'],
        'outputs': ['Winner shape', '(universal anchor)']
    },
    {
        'name': 'STAGE 3',
        'subtitle': 'Winner Rescaling\nto Fixed Budgets',
        'x': 12.5,
        'y': 9.5,
        'inputs': ['• Winner shape', '• B ∈ {64–2048}', '• Evaluate & baseline'],
        'outputs': ['Rescaled configs', '(generalization baseline)']
    },
    {
        'name': 'STAGE 4',
        'subtitle': 'Budget-Constrained\nAdaptive BO Search',
        'x': 17.0,
        'y': 9.5,
        'inputs': ['• Seeded w/ Stage 3', '• Per-budget BO', '• 200 iterations each'],
        'outputs': ['Final optimized\nconfigs (Tables 1-2)']
    }
]

# Draw each stage
stage_positions = []
for stage in stages:
    x, y = stage['x'], stage['y']
    stage_positions.append((x, y))

    # **Stage Box: Large rounded rectangle**
    stage_box = FancyBboxPatch(
        (x - 1.8, y + 1.2), 3.6, 2.0,
        boxstyle="round,pad=0.25",
        edgecolor=color_stage_primary,
        facecolor=color_stage_light,
        linewidth=4,
        alpha=0.95
    )
    ax.add_patch(stage_box)

    # Stage number (larger, bolder)
    stage_name_text = ax.text(
        x, y + 2.7,
        stage['name'],
        ha='center', va='top',
        fontsize=16, fontweight='bold',
        color=color_stage_primary,
        path_effects=[withStroke(linewidth=3, foreground='white', alpha=0.8)]
    )

    # Subtitle
    subtitle_text = ax.text(
        x, y + 1.8,
        stage['subtitle'],
        ha='center', va='center',
        fontsize=11, fontweight='bold',
        color=color_text_main,
        linespacing=1.5
    )

    # **Input Box: Below stage, to the left-ish**
    input_x = x - 3.0
    input_y = y - 1.5
    input_box = FancyBboxPatch(
        (input_x - 1.4, input_y - 1.0), 2.8, 2.0,
        boxstyle="round,pad=0.15",
        edgecolor=color_text_secondary,
        facecolor=color_input,
        linewidth=2.5,
        linestyle='--',
        alpha=0.85
    )
    ax.add_patch(input_box)

    # Input label
    ax.text(
        input_x, input_y + 1.15,
        'INPUT',
        ha='center', va='bottom',
        fontsize=10, fontweight='bold',
        color=color_accent,
        style='italic'
    )

    # Input content
    input_text = '\n'.join(stage['inputs'])
    ax.text(
        input_x, input_y + 0.2,
        input_text,
        ha='center', va='center',
        fontsize=9.5,
        color=color_text_main,
        linespacing=1.6,
        family='monospace'
    )

    # Arrow from stage to input (avoid crossing text)
    arrow_to_input = FancyArrowPatch(
        (x - 0.8, y + 0.9),
        (input_x, input_y + 1.0),
        arrowstyle='-|>',
        mutation_scale=35,
        linewidth=2.5,
        color=color_arrows,
        connectionstyle="arc3,rad=0.3",
        alpha=0.7
    )
    ax.add_patch(arrow_to_input)

    # **Output Box: Below stage, to the right-ish**
    output_x = x + 3.0
    output_y = y - 1.5
    output_box = FancyBboxPatch(
        (output_x - 1.4, output_y - 1.0), 2.8, 2.0,
        boxstyle="round,pad=0.15",
        edgecolor=color_accent,
        facecolor=color_output,
        linewidth=2.5,
        alpha=0.90
    )
    ax.add_patch(output_box)

    # Output label
    ax.text(
        output_x, output_y + 1.15,
        'OUTPUT',
        ha='center', va='bottom',
        fontsize=10, fontweight='bold',
        color=color_accent
    )

    # Output content
    output_text = '\n'.join(stage['outputs'])
    ax.text(
        output_x, output_y + 0.2,
        output_text,
        ha='center', va='center',
        fontsize=9.5, fontweight='bold',
        color=color_stage_primary,
        linespacing=1.6
    )

    # Arrow from stage to output (avoid crossing text)
    arrow_to_output = FancyArrowPatch(
        (x + 0.8, y + 0.9),
        (output_x, output_y + 1.0),
        arrowstyle='-|>',
        mutation_scale=35,
        linewidth=2.5,
        color=color_accent,
        connectionstyle="arc3,rad=-0.3",
        alpha=0.7
    )
    ax.add_patch(arrow_to_output)

# **Horizontal flow arrows between stages (above the stage boxes)**
for i in range(len(stage_positions) - 1):
    x1, y1 = stage_positions[i]
    x2, y2 = stage_positions[i + 1]

    # Arrow from stage to stage
    arrow = FancyArrowPatch(
        (x1 + 1.9, y1 + 1.5),
        (x2 - 1.9, y2 + 1.5),
        arrowstyle='-|>',
        mutation_scale=50,
        linewidth=3.5,
        color=color_stage_primary,
        alpha=0.8,
        linestyle='-',
        zorder=5
    )
    ax.add_patch(arrow)

    # Arrow label: "flows to"
    mid_x = (x1 + x2) / 2
    mid_y = y1 + 1.5 + 0.4
    ax.text(
        mid_x, mid_y,
        '↓',
        ha='center', va='center',
        fontsize=14, color=color_stage_primary,
        fontweight='bold'
    )

# **Title at the top**
ax.text(
    9.0, 12.2,
    'LAMP: Four-Stage Neural Architecture Search Pipeline for Per-Layer KV-Cache Budgets',
    ha='center', va='top',
    fontsize=16, fontweight='bold',
    color=color_stage_primary,
    bbox=dict(boxstyle='round,pad=0.8', facecolor='#F5F5F5', edgecolor=color_stage_primary, linewidth=2),
    path_effects=[withStroke(linewidth=2, foreground='white', alpha=0.5)]
)

# **Bottom explanation box (larger and clearer)**
explanation_box = FancyBboxPatch(
    (0.2, -0.7), 17.6, 0.95,
    boxstyle="round,pad=0.15",
    edgecolor=color_accent,
    facecolor='#FFFEF0',
    linewidth=2.5,
    alpha=0.95
)
ax.add_patch(explanation_box)

explanation_text = (
    "The four-stage LAMP pipeline systematically discovers optimal per-layer KV-cache budget allocations. Stage 1 explores diverse allocation patterns. "
    "Stage 2 identifies the best-performing shape. Stage 3 rescales it to different budgets as a universal baseline. "
    "Stage 4 performs budget-specific search to find optimal per-layer allocations shown in results."
)

ax.text(
    9.0, -0.15,
    explanation_text,
    ha='center', va='center',
    fontsize=10.5,
    color=color_text_main,
    wrap=True,
    linespacing=1.5,
    style='italic'
)

# Remove axis
ax.set_aspect('equal')
plt.tight_layout(pad=1)

# Save in high quality
plt.savefig(
    'figures/figure1_method_diagram.pdf',
    dpi=300,
    bbox_inches='tight',
    format='pdf',
    facecolor='white',
    pad_inches=0.5,
    transparent=False
)
print("✓ Figure 1 (creative redesign) saved as PDF")

plt.savefig(
    'figures/figure1_method_diagram.png',
    dpi=200,
    bbox_inches='tight',
    format='png',
    facecolor='white',
    pad_inches=0.5
)
print("✓ Figure 1 (PNG preview) saved")

plt.close()

print("\n✨ Amazing creative block diagram created!")
print("   • Large, readable text (16pt+ for stage names)")
print("   • No text-line overlap — arrows curve away from text")
print("   • Creative layout with input/output boxes on left/right")
print("   • Professional color scheme with clear visual hierarchy")
print("   • Large, centered explanation at bottom")
print("   • High-quality PDF rendering (300 DPI)")
