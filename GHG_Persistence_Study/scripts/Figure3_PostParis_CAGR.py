"""
Figure 3: Post-Paris Agreement CAGR Distribution by Trajectory Category
Manuscript: Post-Paris GHG Emission Trajectories and SDG 13.2 Compatibility
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import MaxNLocator
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
# Make input path script-relative so the script works when run from any CWD.
INPUT_PATH  = Path(__file__).resolve().parents[1] / "GHG_totals_by_country.csv"   # adjust if needed
# Save output in the project's outputs/figures directory
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "outputs" / "figures" / "Figure3_PostParis_CAGR.png"

# ── Data Loading and Preprocessing ────────────────────────────────────────
df = pd.read_csv(INPUT_PATH)

# Remove aggregate rows
exclude = ['GLOBAL TOTAL', 'EU27', 'International Aviation', 'International Shipping']
df = df[~df['Country'].isin(exclude)]

# Compute post-Paris CAGR (2015-2024, 9-year interval, Equation 4)
df['CAGR_PostParis'] = ((df['2024'] / df['2015']) ** (1 / 9) - 1) * 100

# Assign trajectory category (Equation 1 thresholds)
def classify(row):
    pct = (row['2024'] - row['1970']) / row['1970'] * 100
    if pct < -10:
        return 'Declining'
    elif pct <= 10:
        return 'Stable'
    elif pct <= 100:
        return 'Moderately Rising'
    else:
        return 'Rapidly Rising'

df['Category'] = df.apply(classify, axis=1)

# ── Category Config ────────────────────────────────────────────────────────
category_order  = ['Declining', 'Stable', 'Moderately Rising', 'Rapidly Rising']
category_colors = {
    'Declining':        '#2166ac',   # blue
    'Stable':           '#1a9850',   # green
    'Moderately Rising':'#f46d43',   # orange
    'Rapidly Rising':   '#d73027',   # red
}
mean_colors = {
    'Declining':        '#08306b',   # dark blue
    'Stable':           '#00441b',   # dark green
    'Moderately Rising':'#7f2704',   # dark orange/brown
    'Rapidly Rising':   '#67000d',   # dark red
}
category_labels = {
    'Declining':        '(A) Declining\n[SDG 13.2-Aligned, n=31]',
    'Stable':           '(B) Stable\n[SDG 13.2-Transitioning, n=11]',
    'Moderately Rising':'(C) Moderately Rising\n[SDG 13.2-At Risk, n=30]',
    'Rapidly Rising':   '(D) Rapidly Rising\n[SDG 13.2-Critical, n=136]',
}

# ── Figure Setup ───────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(12, 10), sharey=False)
fig.subplots_adjust(wspace=0.35, hspace=0.5)

for ax, cat in zip(axes.flatten(), category_order):
    data   = df[df['Category'] == cat]['CAGR_PostParis'].dropna()
    color  = category_colors[cat]
    mean   = data.mean()

    # Histogram
    ax.hist(
        data,
        bins=15,
        color=color,
        alpha=0.75,
        edgecolor='white',
        linewidth=0.6
    )

    # Zero reference line
    ax.axvline(0, color='black', linewidth=1.2, linestyle='--', alpha=0.7, label='Zero growth')

    # Mean line
    ax.axvline(mean, color=mean_colors[cat], linewidth=2.5, linestyle='-',
               label=f'Mean: {mean:+.3f}%/yr')


    # Panel title
    ax.set_title(
        category_labels[cat],
        fontsize=10,
        fontweight='bold',
        color=color,
        pad=8
    )

    # Axis labels
    ax.set_xlabel('Post-Paris Agreement CAGR (%/yr)', fontsize=9)
    ax.set_ylabel('Number of Countries', fontsize=9)



    # Legend inside panel
    if cat == 'Declining':
        ax.legend(fontsize=7.5, loc='upper left', framealpha=0.8)
    elif cat == 'Stable':
        ax.legend(fontsize=7.5, loc='upper right', framealpha=0.8,
                  bbox_to_anchor=(1.0, 0.88))
    elif cat == 'Moderately Rising':
        _ymax = ax.get_ylim()[1]
        ax.legend(fontsize=7.5, loc='upper left', framealpha=0.8,
                  bbox_to_anchor=(0, 6 / _ymax))
    else:
        _ymin, _ymax = ax.get_ylim()
        _y_frac = (30 - _ymin) / (_ymax - _ymin)
        ax.legend(fontsize=7.5, loc='upper right', framealpha=0.8,
                  bbox_to_anchor=(0.98, _y_frac))

    # Force integer y-axis ticks for the Stable panel
    if cat == 'Stable':
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    # Grid
    ax.yaxis.grid(True, linestyle='--', alpha=0.4)
    ax.set_axisbelow(True)

# ── Save ───────────────────────────────────────────────────────────────────
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUTPUT_PATH, dpi=300, bbox_inches='tight', format='png')
print(f"Saved: {OUTPUT_PATH}")
plt.close()
