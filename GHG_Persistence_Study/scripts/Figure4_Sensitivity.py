"""
Figure 4: Sensitivity Analysis Visualization
Manuscript: Post-Paris GHG Emission Trajectories and SDG 13.2 Compatibility
Journal: Science of the Total Environment (STOTEN)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

# ── Output Path ────────────────────────────────────────────────────────────
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "outputs" / "figures" / "Figure4_Sensitivity.png"

# ── Data ───────────────────────────────────────────────────────────────────
# Sensitivity Analysis I: Threshold Robustness
sa1_labels = ['Baseline\n(>+100%)', 'Set A\n(>+75%)', 'Set B\n(>+150%)']
sa1_values = [65.4, 68.8, 58.7]

# Sensitivity Analysis II: Sample Composition Robustness
sa2_labels = ['Full Sample\n(n=208)', 'Spec 1\n(≥1 Mt, n=162)',
              'Spec 2\n(≥5 Mt, n=136)', 'Spec 3\n(≥10 Mt, n=110)']
sa2_values = [65.4, 58.6, 55.9, 47.3]

# ── Colors ─────────────────────────────────────────────────────────────────
color_sa1 = '#2166ac'   # blue for threshold robustness
color_sa2 = '#d73027'   # red for sample composition
color_spec3 = '#fee090' # highlight Spec 3 (below majority)

# ── Figure Setup ───────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
fig.subplots_adjust(wspace=0.35)

# ── Panel A: Sensitivity Analysis I ───────────────────────────────────────
x1 = np.arange(len(sa1_labels))
bars1 = ax1.bar(x1, sa1_values, color=color_sa1, alpha=0.75,
                edgecolor='white', linewidth=0.6, width=0.5)

# 50% majority threshold line
ax1.axhline(50, color='black', linewidth=1.5, linestyle='--',
            label='50% majority threshold')

# Value labels on bars
for bar, val in zip(bars1, sa1_values):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
             f'{val}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

ax1.set_xticks(x1)
ax1.set_xticklabels(sa1_labels, fontsize=9)
ax1.set_ylabel('SDG 13.2-Critical Share (%)', fontsize=10)
ax1.set_ylim(0, 85)
ax1.set_title('(A) Sensitivity Analysis I\nThreshold Robustness',
              fontsize=11, fontweight='bold', color=color_sa1, pad=8)
ax1.yaxis.grid(True, linestyle='--', alpha=0.4)
ax1.set_axisbelow(True)
ax1.legend(fontsize=9, loc='lower right')

# ── Panel B: Sensitivity Analysis II ──────────────────────────────────────
x2 = np.arange(len(sa2_labels))
bar_colors = [color_sa2, color_sa2, color_sa2, color_spec3]
bars2 = ax2.bar(x2, sa2_values, color=bar_colors, alpha=0.75,
                edgecolor='white', linewidth=0.6, width=0.5)

# 50% majority threshold line
ax2.axhline(50, color='black', linewidth=1.5, linestyle='--',
            label='50% majority threshold')

# Value labels on bars
for bar, val in zip(bars2, sa2_values):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
             f'{val}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

ax2.set_xticks(x2)
ax2.set_xticklabels(sa2_labels, fontsize=9)
ax2.set_ylabel('SDG 13.2-Critical Share (%)', fontsize=10)
ax2.set_ylim(0, 85)
ax2.set_title('(B) Sensitivity Analysis II\nSample Composition Robustness',
              fontsize=11, fontweight='bold', color=color_sa2, pad=8)
ax2.yaxis.grid(True, linestyle='--', alpha=0.4)
ax2.set_axisbelow(True)

# Legend for Panel B
majority_patch = mpatches.Patch(color=color_sa2, alpha=0.75,
                                label='Majority maintained')
spec3_patch = mpatches.Patch(color=color_spec3, alpha=0.75,
                             label='Majority not met (Spec 3)')
ax2.legend(handles=[majority_patch, spec3_patch,
           plt.Line2D([0], [0], color='black', linewidth=1.5,
                      linestyle='--', label='50% majority threshold')],
           fontsize=9, loc='lower left')

# ── Save ───────────────────────────────────────────────────────────────────
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUTPUT_PATH, dpi=300, bbox_inches='tight', format='png')
print(f"Saved: {OUTPUT_PATH}")
plt.close()
