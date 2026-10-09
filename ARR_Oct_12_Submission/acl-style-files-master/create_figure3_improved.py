#!/usr/bin/env python3
"""Improve Figure 3: Create a properly sized 2-panel figure with convergence + profiles."""

import matplotlib.pyplot as plt
from PIL import Image
import matplotlib.gridspec as gridspec

# Load the two existing images
convergence_img = Image.open('figures/convergence.png')
profiles_img = Image.open('figures/config_profiles.png')

# Create a new figure with 1 row, 2 columns
fig = plt.figure(figsize=(14, 5))
gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1], wspace=0.25)

# Left panel: Convergence
ax1 = fig.add_subplot(gs[0, 0])
ax1.imshow(convergence_img)
ax1.axis('off')
ax1.text(0.5, -0.08, '(a) BO Convergence', transform=ax1.transAxes,
         ha='center', va='top', fontsize=11, fontweight='bold')

# Right panel: Config profiles (make taller)
ax2 = fig.add_subplot(gs[0, 1])
ax2.imshow(profiles_img)
ax2.axis('off')
ax2.text(0.5, -0.08, '(b) Per-Layer Budget Profiles', transform=ax2.transAxes,
         ha='center', va='top', fontsize=11, fontweight='bold')

# Overall title
fig.suptitle('Search Efficiency and Budget Allocation Strategies',
             fontsize=12, fontweight='bold', y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig('figures/figure3_convergence_profiles.pdf', dpi=300, bbox_inches='tight',
            format='pdf', facecolor='white', pad_inches=0.2)
print("✓ Figure 3 (improved 2-panel layout) saved as PDF")

plt.savefig('figures/figure3_convergence_profiles.png', dpi=150, bbox_inches='tight',
            format='png', facecolor='white', pad_inches=0.2)
print("✓ Figure 3 (PNG preview) saved")

plt.close()
