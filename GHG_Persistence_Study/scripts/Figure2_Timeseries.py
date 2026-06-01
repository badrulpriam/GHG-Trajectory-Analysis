"""
Figure 2: GHG Emission Trajectories by Category (1970-2024)
4-panel time series - Publication quality
"""

from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import warnings
warnings.filterwarnings('ignore')

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
CSV_PATH = PROJECT_ROOT / 'data' / 'processed' / 'Processed_GHG_totals_by_country.csv'
CLASSIFICATION_PATH = PROJECT_ROOT / 'outputs' / 'tables' / 'Analysis_Trajectory Classification.xlsx'
OUTPUT_PATH = PROJECT_ROOT / 'outputs' / 'figures' / 'Figure2_TimeSeries.png'

# ─────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────
ghg = pd.read_csv(CSV_PATH)
cls = pd.read_excel(CLASSIFICATION_PATH,
                    sheet_name='Country_Classifications')

# Year columns
years = list(range(1970, 2025))
year_cols = [str(y) for y in years]

# Merge trajectory classification
ghg = ghg.merge(cls[['Country', 'Trajectory_Type']], on='Country', how='inner')

# ─────────────────────────────────────────────
# 2. CONFIGURATION
# ─────────────────────────────────────────────
CATEGORIES = ['Declining', 'Stable', 'Moderately Rising', 'Rapidly Rising']

COLORS = {
    'Declining':        '#2166AC',   # Blue
    'Stable':           '#1A9850',   # Teal/Green
    'Moderately Rising':'#F97B2B',   # Orange
    'Rapidly Rising':   '#D7191C',   # Red
}

PANEL_LABELS = {
    'Declining':        'A',
    'Stable':           'B',
    'Moderately Rising':'C',
    'Rapidly Rising':   'D',
}

SDG_STATUS = {
    'Declining':        'SDG 13.2-Aligned',
    'Stable':           'SDG 13.2-Transitioning',
    'Moderately Rising':'SDG 13.2-At Risk',
    'Rapidly Rising':   'SDG 13.2-Critical',
}

# ─────────────────────────────────────────────
# 3. FIGURE SETUP
# ─────────────────────────────────────────────
fig, axes = plt.subplots(
    2, 2,
    figsize=(14, 10),
    dpi=300,
    constrained_layout=False
)

fig.subplots_adjust(
    left=0.07, right=0.97,
    top=0.92, bottom=0.10,
    hspace=0.38, wspace=0.22
)

# ─────────────────────────────────────────────
# 4. FONT SETTINGS (publication style)
# ─────────────────────────────────────────────
plt.rcParams.update({
    'font.family':      'DejaVu Sans',
    'font.size':        9,
    'axes.labelsize':   9,
    'axes.titlesize':   10,
    'xtick.labelsize':  8,
    'ytick.labelsize':  8,
    'axes.linewidth':   0.8,
    'xtick.major.width':0.8,
    'ytick.major.width':0.8,
})

# ─────────────────────────────────────────────
# 5. PLOT EACH PANEL
# ─────────────────────────────────────────────
ax_list = [axes[0,0], axes[0,1], axes[1,0], axes[1,1]]

for ax, cat in zip(ax_list, CATEGORIES):
    color  = COLORS[cat]
    label  = PANEL_LABELS[cat]
    status = SDG_STATUS[cat]

    subset = ghg[ghg['Trajectory_Type'] == cat]
    n      = len(subset)

    # Extract emission matrix
    em = subset[year_cols].values.astype(float)

    # ── Group mean (bold)
    group_mean = np.nanmean(em, axis=0)

    # ── Group median (dashed)
    group_median = np.nanmedian(em, axis=0)

    if cat == 'Stable':
        # Panel B only: median on left axis (0–150 Mt), mean on secondary right axis (0–900 Mt)
        ax.plot(
            years, group_median,
            color=color, linewidth=1.2, alpha=0.85,
            linestyle='--', zorder=3
        )
        ax2 = ax.twinx()
        ax2.plot(
            years, group_mean,
            color=color, linewidth=2.2, alpha=1.0,
            zorder=4, solid_capstyle='round'
        )
        ax.set_ylim(0, 150)
        ax2.set_ylim(0, 900)
        ax2.set_ylabel('Mean (Mt CO₂-eq)', fontsize=8.5)
        ax2.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, _: f'{x:,.0f}')
        )
        ax2.spines['top'].set_visible(False)
        ax2.tick_params(axis='y', labelsize=8)
    else:
        ax.plot(
            years, group_mean,
            color=color, linewidth=2.2, alpha=1.0,
            zorder=4, solid_capstyle='round'
        )
        ax.plot(
            years, group_median,
            color=color, linewidth=1.2, alpha=0.85,
            linestyle='--', zorder=3
        )

    # ── Paris Agreement vertical line
    ax.axvline(
        x=2015, color='#222222', linewidth=1.5,
        linestyle=':', zorder=5, alpha=1.0
    )

    # ── Panel title with label prepended
    ax.set_title(
        f'({label}) {cat}  [n={n}, {status}]',
        fontsize=10, fontweight='bold',
        color=color, pad=6
    )

    # ── Axis labels
    ax.set_xlabel('Year', fontsize=8.5)
    if cat == 'Stable':
        ax.set_ylabel('Median (Mt CO₂-eq)', fontsize=8.5)
    else:
        ax.set_ylabel('GHG Emissions (Mt CO₂-eq)', fontsize=8.5)

    # ── X-axis ticks
    ax.set_xticks([1970, 1980, 1990, 2000, 2010, 2024])
    ax.set_xlim(1968, 2026)

    # ── Linear y-axis for all panels
    ax.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, _: f'{x:,.0f}')
    )

    # ── Grid
    ax.grid(
        True, which='major', linestyle='-',
        linewidth=0.4, alpha=0.4, color='grey'
    )
    ax.set_axisbelow(True)

    # ── Spine styling
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)

# ─────────────────────────────────────────────
# 6. SHARED FIGURE LEGEND
# ─────────────────────────────────────────────
legend_elements = [
    Line2D([0],[0], color='#444444', linewidth=2.2,
           linestyle='-',  label='Group mean'),
    Line2D([0],[0], color='#444444', linewidth=1.2,
           linestyle='--', label='Group median'),
    Line2D([0],[0], color='#000000', linewidth=1.5,
           linestyle=':', label='Paris Agreement (2015)'),
]
fig.legend(
    handles=legend_elements,
    loc='lower center',
    bbox_to_anchor=(0.5, 0.01),
    ncol=3,
    fontsize=9.5,
    framealpha=0.95,
    edgecolor='lightgrey',
    frameon=True,
    handlelength=2.5,
    columnspacing=2.0,
    handletextpad=0.8
)

# ─────────────────────────────────────────────
# 8. SAVE
# ─────────────────────────────────────────────
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(
    OUTPUT_PATH,
    dpi=300,
    bbox_inches='tight',
    facecolor='white',
    format='png'
)
print(f"Saved: {OUTPUT_PATH}")
plt.close()
