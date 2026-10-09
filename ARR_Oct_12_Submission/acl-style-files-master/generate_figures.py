#!/usr/bin/env python3
"""Generate Figure 4: Task-specific gains comparison."""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Data extracted from ICLR_Final_Results tables
# Format: {task: {budget: delta}}
data_dict = {
    'SINGLE_DOC_QA': {128: 0.54, 256: -0.74, 512: 0.36, 1024: 0.02},
    'MULTI_DOC_QA': {128: 0.20, 256: 0.71, 512: -0.04, 1024: 0.39},
    'CODE': {128: 1.05, 256: 1.66, 512: 1.43, 1024: 2.50},
    'RULER': {64: 10.35, 128: 9.52, 256: 4.43, 512: 3.14, 1024: 8.13, 1536: 9.73, 2048: 5.98}
}

# Create DataFrame for visualization
# For cleaner viz, use best/representative budgets for each task
viz_data = {
    'Task': ['SINGLE_DOC_QA', 'MULTI_DOC_QA', 'CODE', 'RULER'],
    'B128': [0.54, 0.20, 1.05, 9.52],
    'B256': [-0.74, 0.71, 1.66, 4.43],
    'B512': [0.36, -0.04, 1.43, 3.14],
    'B1024': [0.02, 0.39, 2.50, 8.13]
}

df = pd.DataFrame(viz_data)
df_melted = df.melt(id_vars='Task', var_name='Budget', value_name='Delta')

# Create figure
fig, ax = plt.subplots(figsize=(8, 5))

# Generate grouped bar chart
sns.barplot(data=df_melted, x='Task', y='Delta', hue='Budget', ax=ax, palette='husl')

# Styling
ax.set_xlabel('Task Category', fontsize=12, fontweight='bold')
ax.set_ylabel('Performance Gain vs Uniform (points)', fontsize=12, fontweight='bold')
ax.set_title('NAS Performance Gains by Task Type', fontsize=13, fontweight='bold')
ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.3)
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.legend(title='Budget', fontsize=10, title_fontsize=11, loc='upper left')

# Format y-axis
ax.set_ylim(-2, 11)

plt.tight_layout()
plt.savefig('figures/figure4_task_gains.pdf', dpi=300, bbox_inches='tight', format='pdf')
print("✓ Figure 4 saved: figures/figure4_task_gains.pdf")

plt.savefig('figures/figure4_task_gains.png', dpi=150, bbox_inches='tight', format='png')
print("✓ Figure 4 (PNG preview) saved: figures/figure4_task_gains.png")
