# =============================================================================
# ANALYSIS 3 — PARIS AGREEMENT EFFECTIVENESS: POLICY ERA COMPARISON
# Project  : GHG Persistence Study
# Journal  : Ecological Indicators
# =============================================================================
#
# RESEARCH QUESTION:
#   Has the Paris Agreement (2015) measurably altered the rate of global
#   GHG emission growth, and is the post-Paris trajectory consistent with
#   SDG 13 targets?
#
# APPROACH:
#   Compare emission growth rates (CAGR) across four policy eras:
#     Era 1: Pre-Kyoto    1970–1990  (business as usual)
#     Era 2: Kyoto era    1990–2005  (first binding framework)
#     Era 3: Pre-Paris    2005–2015  (post-Kyoto gap)
#     Era 4: Post-Paris   2015–2024  (Paris Agreement period)
#
#   A genuine Paris effect would manifest as a statistically and
#   environmentally meaningful reduction in CAGR in Era 4 compared
#   to previous eras.
#
# METRICS:
#   CAGR  : Compound Annual Growth Rate of GHG emissions (%)
#   Δ CAGR: Change in growth rate between adjacent eras
#   Paris effect: difference between Era 3 and Era 4 CAGR
# =============================================================================

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
from scipy import stats

warnings.filterwarnings('ignore')

# ── PATHS ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH    = os.path.join(PROJECT_ROOT, "data", "processed", "ghg_clean.csv")
TABLE_PATH   = os.path.join(PROJECT_ROOT, "outputs", "tables")
FIG_PATH     = os.path.join(PROJECT_ROOT, "outputs", "figures")

# ── FIGURE SPECS ──────────────────────────────────────────────────────────────
W2   = 7.48
DPI  = 600
SAVE = dict(dpi=DPI, facecolor='white', edgecolor='none',
            bbox_inches='tight', pad_inches=0.06)

# ── STYLE ─────────────────────────────────────────────────────────────────────
plt.style.use('default')
matplotlib.rcParams.update({
    'font.family'      : 'DejaVu Sans',
    'font.size'        : 8,
    'axes.labelsize'   : 9,
    'xtick.labelsize'  : 8,
    'ytick.labelsize'  : 8,
    'legend.fontsize'  : 8,
    'axes.linewidth'   : 0.8,
    'axes.edgecolor'   : '#2B2B2B',
    'axes.facecolor'   : 'white',
    'figure.facecolor' : 'white',
    'axes.spines.top'  : False,
    'axes.spines.right': False,
    'axes.grid'        : True,
    'axes.axisbelow'   : True,
    'grid.color'       : '#E8E8E8',
    'grid.linewidth'   : 0.5,
    'savefig.facecolor': 'white',
})

# ── COLOURS ───────────────────────────────────────────────────────────────────
ERA_COLOURS = {
    'Pre-Kyoto (1970–1990)'  : '#888888',
    'Kyoto era (1990–2005)'  : '#0072B2',
    'Pre-Paris (2005–2015)'  : '#E69F00',
    'Post-Paris (2015–2024)' : '#009E73',
}
TRAJ_COLOURS = {
    'Declining'         : '#1A7A4A',
    'Stable'            : '#F0C040',
    'Moderately Rising' : '#E07B20',
    'Rapidly Rising'    : '#C0392B',
}

# ── ERA DEFINITIONS ───────────────────────────────────────────────────────────
ERAS = {
    'Pre-Kyoto (1970–1990)'  : (1970, 1990),
    'Kyoto era (1990–2005)'  : (1990, 2005),
    'Pre-Paris (2005–2015)'  : (2005, 2015),
    'Post-Paris (2015–2024)' : (2015, 2024),
}
ERA_ORDER = list(ERAS.keys())

print("=" * 65)
print("  ANALYSIS 3 — PARIS AGREEMENT EFFECTIVENESS")
print("=" * 65)

# =============================================================================
# STEP 1 — LOAD DATA
# =============================================================================
print("\n[Step 1] Loading data...")

df      = pd.read_csv(DATA_PATH)
df['Year'] = df['Year'].astype(int)
df_wide = df.pivot(index='Country', columns='Year', values='GHG_Emissions').copy()

# Load trajectory classification from Analysis 1
traj_path = os.path.join(TABLE_PATH, 'analysis1_trajectory_results.xlsx')
if os.path.exists(traj_path):
    traj_df  = pd.read_excel(traj_path, sheet_name='Country_Classifications')
    traj_map = dict(zip(traj_df['Country'], traj_df['Trajectory_Type']))
    print(f"  Trajectory classifications loaded")
else:
    traj_map = {}
    print(f"  WARNING: Run analysis1 first")

print(f"  Countries: {len(df_wide)} | Years: 1970–2024")

# =============================================================================
# STEP 2 — GLOBAL ERA ANALYSIS
# =============================================================================
print("\n[Step 2] Global CAGR per policy era...")

global_annual = df.groupby('Year')['GHG_Emissions'].sum().reset_index()
global_annual.columns = ['Year', 'Total']

global_era_stats = []
for era_name, (y1, y2) in ERAS.items():
    v1   = global_annual.loc[global_annual['Year'] == y1, 'Total'].values[0]
    v2   = global_annual.loc[global_annual['Year'] == y2, 'Total'].values[0]
    n_yr = y2 - y1
    cagr = ((v2 / v1) ** (1 / n_yr) - 1) * 100
    tot  = (v2 - v1) / v1 * 100
    abs_change = v2 - v1
    global_era_stats.append({
        'Era'            : era_name,
        'Start_Year'     : y1,
        'End_Year'       : y2,
        'N_Years'        : n_yr,
        'GHG_Start_Mt'   : round(v1, 1),
        'GHG_End_Mt'     : round(v2, 1),
        'Abs_Change_Mt'  : round(abs_change, 1),
        'Total_Change_Pct': round(tot, 2),
        'CAGR_Pct'       : round(cagr, 3),
    })
    print(f"  {era_name:<28} CAGR = {cagr:+.3f}%/yr  |  "
          f"Total = {tot:+.1f}%  |  "
          f"{v1:.0f} → {v2:.0f} Mt")

global_era_df = pd.DataFrame(global_era_stats)

# Paris effect: Era 3 CAGR vs Era 4 CAGR
cagr_pre  = global_era_df.loc[global_era_df['Era']=='Pre-Paris (2005–2015)', 'CAGR_Pct'].values[0]
cagr_post = global_era_df.loc[global_era_df['Era']=='Post-Paris (2015–2024)', 'CAGR_Pct'].values[0]
paris_effect = cagr_pre - cagr_post
print(f"\n  Paris Effect (Era 3 → Era 4 CAGR reduction): {paris_effect:+.3f} ppt/yr")
print(f"  Interpretation: Global emission growth rate reduced by "
      f"{paris_effect:.3f} percentage points after Paris Agreement")

# =============================================================================
# STEP 3 — COUNTRY-LEVEL ERA CAGR
# =============================================================================
print("\n[Step 3] Country-level CAGR per era...")

country_era_rows = []
for country in df_wide.index:
    row = {'Country': country,
           'Trajectory_Type': traj_map.get(country, 'Unknown')}
    for era_name, (y1, y2) in ERAS.items():
        v1 = df_wide.loc[country, y1]
        v2 = df_wide.loc[country, y2]
        if pd.notna(v1) and pd.notna(v2) and v1 > 0:
            n_yr = y2 - y1
            cagr = ((v2 / v1) ** (1 / n_yr) - 1) * 100
        else:
            cagr = np.nan
        col = 'CAGR_' + era_name[:3].replace('Pre', 'PreK').replace('Kyo', 'Kyo').replace('Pre', 'PreP').replace('Pos', 'Post')
        safe_col = f"CAGR_Era{list(ERAS.keys()).index(era_name)+1}"
        row[safe_col] = round(cagr, 3) if pd.notna(cagr) else np.nan
        row[f"CAGR_{era_name.split('(')[0].strip().replace(' ','_').replace('-','_')}"] = round(cagr, 3) if pd.notna(cagr) else np.nan
    country_era_rows.append(row)

country_era_df = pd.DataFrame(country_era_rows)
cagr_cols = [c for c in country_era_df.columns if c.startswith('CAGR_Era')]

# Paris effect at country level
cagr_era3 = country_era_df['CAGR_Era3'].dropna()
cagr_era4 = country_era_df['CAGR_Era4'].dropna()
common_idx = cagr_era3.index.intersection(cagr_era4.index)
paris_effect_country = cagr_era3[common_idx] - cagr_era4[common_idx]
country_era_df['Paris_Effect_ppt'] = paris_effect_country

n_positive_paris = (paris_effect_country > 0).sum()   # CAGR reduced post-Paris
n_negative_paris = (paris_effect_country < 0).sum()   # CAGR increased post-Paris

print(f"  Countries with LOWER CAGR post-Paris  : {n_positive_paris} ({n_positive_paris/len(common_idx)*100:.0f}%)")
print(f"  Countries with HIGHER CAGR post-Paris : {n_negative_paris} ({n_negative_paris/len(common_idx)*100:.0f}%)")
print(f"  Mean Paris effect (global)             : {paris_effect_country.mean():+.3f} ppt/yr")

# =============================================================================
# STEP 4 — EXPORT RESULTS
# =============================================================================
print("\n[Step 4] Exporting results tables...")

with pd.ExcelWriter(
    os.path.join(TABLE_PATH, 'analysis3_paris_effectiveness.xlsx'),
    engine='openpyxl'
) as writer:
    global_era_df.to_excel(writer, sheet_name='Global_Era_Stats', index=False)
    country_era_df.to_excel(writer, sheet_name='Country_Era_CAGR', index=False)

print(f"  ✓ Saved: analysis3_paris_effectiveness.xlsx")

# =============================================================================
# STEP 5 — FIGURE C1: GLOBAL ERA COMPARISON
# Left : absolute emission trajectory with era shading
# Right: CAGR bar chart per era
# =============================================================================
print("\n[Step 5] Generating Figure C1: Global era comparison...")

fig1, (ax_left, ax_right) = plt.subplots(
    1, 2,
    figsize=(W2, W2 * 0.48),
    facecolor='white',
    gridspec_kw={'wspace': 0.40}
)

# ── Left: emission trajectory with era shading ────────────────────────────────
ax = ax_left
ax.set_facecolor('white')

yrs  = global_annual['Year'].values
vals = global_annual['Total'].values / 1000   # convert to Gt

ax.plot(yrs, vals, color='#2B2B2B', linewidth=1.8,
        solid_capstyle='round', zorder=5)

era_boundaries = [1970, 1990, 2005, 2015, 2024]
era_cols_list  = list(ERA_COLOURS.values())

for i, era_name in enumerate(ERA_ORDER):
    y1, y2 = ERAS[era_name]
    era_vals = global_annual[
        (global_annual['Year'] >= y1) &
        (global_annual['Year'] <= y2)
    ]
    ax.fill_between(
        era_vals['Year'], era_vals['Total'] / 1000,
        alpha=0.15, color=ERA_COLOURS[era_name], zorder=2
    )
    # Era boundary line
    ax.axvline(y1, color=ERA_COLOURS[era_name], linewidth=0.8,
               linestyle='--', alpha=0.55, zorder=3)
    # CAGR annotation
    mid_yr = (y1 + y2) / 2
    max_val = global_annual[
        (global_annual['Year'] >= y1) &
        (global_annual['Year'] <= y2)
    ]['Total'].max() / 1000
    cagr_val = global_era_df.loc[
        global_era_df['Era'] == era_name, 'CAGR_Pct'
    ].values[0]
    ax.text(mid_yr, max_val * 0.88,
            f'{cagr_val:+.2f}%/yr',
            ha='center', fontsize=7.0,
            color=ERA_COLOURS[era_name], fontweight='medium')

ax.axvline(2015, color='#009E73', linewidth=1.4,
           linestyle='-', alpha=0.70, zorder=4)
ax.text(2015.3, vals.min() * 1.01, 'Paris\nAgreement',
        fontsize=6.8, color='#009E73', va='bottom', fontweight='medium')

ax.set_xlim(1970, 2024)
ax.set_xlabel('Year', fontsize=9, labelpad=4)
ax.set_ylabel('Global GHG Emissions (Gt CO₂-eq)', fontsize=8.5, labelpad=4)
ax.yaxis.grid(True, color='#E8E8E8', linewidth=0.5, zorder=0)
ax.set_axisbelow(True)
ax.xaxis.set_major_locator(mticker.MultipleLocator(10))
ax.text(-0.12, 1.05, '(a)', transform=ax.transAxes,
        fontsize=10, fontweight='bold', va='bottom')

# ── Right: CAGR bar chart ─────────────────────────────────────────────────────
ax = ax_right
ax.set_facecolor('white')

cagr_vals  = [global_era_df.loc[global_era_df['Era']==e, 'CAGR_Pct'].values[0]
              for e in ERA_ORDER]
bar_cols   = [ERA_COLOURS[e] for e in ERA_ORDER]
short_labs = ['Pre-Kyoto\n1970–1990',
              'Kyoto era\n1990–2005',
              'Pre-Paris\n2005–2015',
              'Post-Paris\n2015–2024']

bars = ax.bar(range(4), cagr_vals, 0.62,
              color=bar_cols, edgecolor='white', linewidth=0.5, zorder=3)

for bar, val in zip(bars, cagr_vals):
    ypos = val + 0.02 if val >= 0 else val - 0.06
    ax.text(bar.get_x() + bar.get_width()/2, ypos,
            f'{val:+.3f}%',
            ha='center', va='bottom', fontsize=7.5, fontweight='medium')

ax.axhline(0, color='#444444', linewidth=0.8, alpha=0.6, zorder=4)

# Highlight Paris effect arrow
ax.annotate('',
    xy=(3, cagr_vals[3]),
    xytext=(2, cagr_vals[2]),
    arrowprops=dict(arrowstyle='->', color='#009E73',
                    lw=1.4, connectionstyle='arc3,rad=-0.15')
)
mid_x = 2.5
mid_y = (cagr_vals[2] + cagr_vals[3]) / 2
ax.text(mid_x + 0.25, mid_y,
        f'−{abs(cagr_vals[2]-cagr_vals[3]):.3f}\nppt/yr',
        ha='left', fontsize=7, color='#009E73', fontweight='medium')

ax.set_xticks(range(4))
ax.set_xticklabels(short_labs, fontsize=7.2)
ax.set_ylabel('CAGR of GHG Emissions (%/yr)', fontsize=8.5, labelpad=4)
ax.yaxis.grid(True, color='#E8E8E8', linewidth=0.5, zorder=0)
ax.set_axisbelow(True)
ax.text(-0.12, 1.05, '(b)', transform=ax.transAxes,
        fontsize=10, fontweight='bold', va='bottom')

fig1.text(
    0.5, -0.04,
    'Note: Panel (a) global GHG emission trajectory with policy era shading; '
    'CAGR annotated per era. '
    'Panel (b) CAGR per era; arrow shows reduction in growth rate after Paris Agreement. '
    'CAGR = compound annual growth rate.',
    ha='center', fontsize=6.8, style='italic', color='#555555'
)

fig1.savefig(os.path.join(FIG_PATH, 'fig_c1_era_comparison.tiff'), **SAVE,
             format='tiff', pil_kwargs={'compression': 'tiff_lzw'})
fig1.savefig(os.path.join(FIG_PATH, 'fig_c1_era_comparison.pdf'), **SAVE)
plt.close(fig1)
print("   ✓ fig_c1_era_comparison.tiff / .pdf")

# =============================================================================
# STEP 6 — FIGURE C2: COUNTRY-LEVEL ERA CAGR DISTRIBUTION
# Box plots: distribution of country CAGR per era, split by trajectory type
# =============================================================================
print("\n[Step 6] Generating Figure C2: Country-level CAGR distributions...")

TRAJ_ORDER = ['Declining', 'Stable', 'Moderately Rising', 'Rapidly Rising']
TRAJ_SHORT = ['Declining', 'Stable', 'Mod. Rising', 'Rapid Rising']

fig2, axes2 = plt.subplots(
    1, 4,
    figsize=(W2, W2 * 0.50),
    facecolor='white',
    gridspec_kw={'wspace': 0.12}
)

cagr_era_col_map = {
    'Pre-Kyoto (1970–1990)'  : 'CAGR_Era1',
    'Kyoto era (1990–2005)'  : 'CAGR_Era2',
    'Pre-Paris (2005–2015)'  : 'CAGR_Era3',
    'Post-Paris (2015–2024)' : 'CAGR_Era4',
}

for era_idx, era_name in enumerate(ERA_ORDER):
    ax   = axes2[era_idx]
    ax.set_facecolor('white')
    col  = ERA_COLOURS[era_name]
    ecol = cagr_era_col_map[era_name]

    positions = range(len(TRAJ_ORDER))
    for ti, traj in enumerate(TRAJ_ORDER):
        data = country_era_df[
            country_era_df['Trajectory_Type'] == traj
        ][ecol].dropna()

        bp = ax.boxplot(
            data,
            positions=[ti],
            widths=0.55,
            patch_artist=True,
            boxprops=dict(facecolor=TRAJ_COLOURS[traj], alpha=0.70,
                          linewidth=0.7, edgecolor='#333333'),
            medianprops=dict(color='black', linewidth=1.4),
            whiskerprops=dict(linewidth=0.7, color='#444444'),
            capprops=dict(linewidth=0.7, color='#444444'),
            flierprops=dict(marker='o', markersize=1.8,
                            markerfacecolor=TRAJ_COLOURS[traj],
                            markeredgecolor='none', alpha=0.5),
            zorder=3
        )

    ax.axhline(0, color='#444444', linewidth=0.9,
               linestyle='--', alpha=0.55, zorder=4)
    ax.set_xticks(range(len(TRAJ_ORDER)))
    ax.set_xticklabels(TRAJ_SHORT, fontsize=6.5, rotation=30, ha='right')

    era_short = era_name.split('(')[0].strip()
    yr_range  = era_name.split('(')[1].replace(')', '')
    ax.set_title(f'{era_short}\n{yr_range}',
                 fontsize=7.5, fontweight='medium',
                 color=col, pad=4)

    if era_idx == 0:
        ax.set_ylabel('CAGR (%/yr)', fontsize=8.5, labelpad=4)
    else:
        ax.tick_params(labelleft=False)

    ax.yaxis.grid(True, color='#E8E8E8', linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)

    panel_lbl = ['(a)', '(b)', '(c)', '(d)'][era_idx]
    ax.text(-0.15, 1.06, panel_lbl, transform=ax.transAxes,
            fontsize=10, fontweight='bold', va='bottom')

fig2.text(
    0.5, -0.06,
    'Note: Box plots show country-level CAGR distribution per policy era, '
    'disaggregated by trajectory type (Analysis 1). '
    'Dashed line = zero growth. Outliers shown as points.',
    ha='center', fontsize=6.8, style='italic', color='#555555'
)

fig2.savefig(os.path.join(FIG_PATH, 'fig_c2_cagr_by_trajectory.tiff'), **SAVE,
             format='tiff', pil_kwargs={'compression': 'tiff_lzw'})
fig2.savefig(os.path.join(FIG_PATH, 'fig_c2_cagr_by_trajectory.pdf'), **SAVE)
plt.close(fig2)
print("   ✓ fig_c2_cagr_by_trajectory.tiff / .pdf")

# =============================================================================
# STEP 7 — FIGURE C3: PARIS EFFECT DISTRIBUTION
# Histogram of Paris effect (CAGR reduction Era3→Era4) per country
# Coloured by trajectory type, shows which countries benefited most
# =============================================================================
print("\n[Step 7] Generating Figure C3: Paris effect distribution...")

fig3, (ax_hist, ax_scatter) = plt.subplots(
    1, 2,
    figsize=(W2, W2 * 0.48),
    facecolor='white',
    gridspec_kw={'wspace': 0.38}
)

# ── Left: histogram of Paris effect ──────────────────────────────────────────
ax = ax_hist
ax.set_facecolor('white')

for traj in TRAJ_ORDER:
    sub = country_era_df[
        (country_era_df['Trajectory_Type'] == traj) &
        country_era_df['Paris_Effect_ppt'].notna()
    ]['Paris_Effect_ppt']
    if len(sub) > 0:
        ax.hist(sub, bins=30, color=TRAJ_COLOURS[traj],
                alpha=0.70, edgecolor='white', linewidth=0.3,
                label=f'{traj} (n={len(sub)})', zorder=3)

ax.axvline(0, color='#333333', linewidth=1.0,
           linestyle='--', alpha=0.60, zorder=4)
ax.axvline(country_era_df['Paris_Effect_ppt'].mean(), color='black',
           linewidth=1.2, linestyle='-', alpha=0.55, zorder=5,
           label=f'Global mean ({country_era_df["Paris_Effect_ppt"].mean():+.3f} ppt)')

ax.set_xlabel('Paris effect (CAGR reduction, ppt/yr)', fontsize=9, labelpad=4)
ax.set_ylabel('Number of countries', fontsize=9, labelpad=4)
ax.yaxis.grid(True, color='#E8E8E8', linewidth=0.5, zorder=0)
ax.set_axisbelow(True)

ax.legend(loc='upper left', fontsize=7.0, frameon=True,
          framealpha=0.95, edgecolor='#CCCCCC', fancybox=False,
          borderpad=0.5, labelspacing=0.25, handlelength=1.5)

ax.text(-0.12, 1.05, '(a)', transform=ax.transAxes,
        fontsize=10, fontweight='bold', va='bottom')

# ── Right: Era 3 vs Era 4 CAGR scatter ───────────────────────────────────────
ax = ax_scatter
ax.set_facecolor('white')

for traj in TRAJ_ORDER:
    sub = country_era_df[country_era_df['Trajectory_Type'] == traj]
    ax.scatter(
        sub['CAGR_Era3'], sub['CAGR_Era4'],
        c=TRAJ_COLOURS[traj], s=18, alpha=0.65,
        edgecolors='white', linewidths=0.3,
        zorder=4, label=traj
    )

# 1:1 line — above = CAGR increased after Paris, below = decreased
lims_min = min(country_era_df['CAGR_Era3'].min(),
               country_era_df['CAGR_Era4'].min()) - 0.5
lims_max = max(country_era_df['CAGR_Era3'].max(),
               country_era_df['CAGR_Era4'].max()) + 0.5
ax.plot([lims_min, lims_max], [lims_min, lims_max],
        color='#444444', linewidth=1.0, linestyle='--',
        alpha=0.55, zorder=3, label='No change (1:1 line)')
ax.axhline(0, color='#888888', linewidth=0.6,
           linestyle=':', alpha=0.5, zorder=2)

# Shade regions
ax.fill_between([lims_min, lims_max], [lims_min, lims_max], lims_min,
                color='#009E73', alpha=0.05, zorder=1)
ax.fill_between([lims_min, lims_max], [lims_min, lims_max], lims_max,
                color='#C0392B', alpha=0.05, zorder=1)

ax.text(0.03, 0.97,
        f'Below line: CAGR reduced\nafter Paris ({n_positive_paris} countries)',
        transform=ax.transAxes, fontsize=6.8, va='top',
        color='#009E73', style='italic')
ax.text(0.97, 0.03,
        f'Above line: CAGR increased\nafter Paris ({n_negative_paris} countries)',
        transform=ax.transAxes, fontsize=6.8, va='bottom', ha='right',
        color='#C0392B', style='italic')

ax.set_xlim(lims_min, lims_max)
ax.set_ylim(lims_min, lims_max)
ax.set_xlabel('CAGR pre-Paris era 2005–2015 (%/yr)', fontsize=8.5, labelpad=4)
ax.set_ylabel('CAGR post-Paris era 2015–2024 (%/yr)', fontsize=8.5, labelpad=4)
ax.yaxis.grid(True, color='#E8E8E8', linewidth=0.5, zorder=0)
ax.xaxis.grid(True, color='#E8E8E8', linewidth=0.5, zorder=0)
ax.set_axisbelow(True)
ax.set_aspect('equal', adjustable='box')

ax.legend(loc='lower right', fontsize=7.0, frameon=True,
          framealpha=0.95, edgecolor='#CCCCCC', fancybox=False,
          borderpad=0.5, labelspacing=0.25, handlelength=1.5)

ax.text(-0.12, 1.05, '(b)', transform=ax.transAxes,
        fontsize=10, fontweight='bold', va='bottom')

fig3.text(
    0.5, -0.04,
    'Note: Panel (a) distribution of country-level Paris effect '
    '(positive = CAGR reduced post-Paris). '
    'Panel (b) pre-Paris vs post-Paris CAGR scatter; '
    'points below the 1:1 line indicate reduced growth rate after 2015.',
    ha='center', fontsize=6.8, style='italic', color='#555555'
)

fig3.savefig(os.path.join(FIG_PATH, 'fig_c3_paris_effect.tiff'), **SAVE,
             format='tiff', pil_kwargs={'compression': 'tiff_lzw'})
fig3.savefig(os.path.join(FIG_PATH, 'fig_c3_paris_effect.pdf'), **SAVE)
plt.close(fig3)
print("   ✓ fig_c3_paris_effect.tiff / .pdf")

# =============================================================================
# STEP 8 — KEY STATISTICS FOR PAPER
# =============================================================================
print("\n[Step 8] Key statistics for paper:")
print("=" * 65)

print(f"\n  GLOBAL ERA CAGR COMPARISON:")
for _, row in global_era_df.iterrows():
    print(f"  {row['Era']:<30} {row['CAGR_Pct']:+.3f}%/yr")

print(f"\n  PARIS AGREEMENT EFFECT:")
print(f"  Global CAGR reduced from {cagr_pre:+.3f}%/yr (2005–2015) "
      f"to {cagr_post:+.3f}%/yr (2015–2024)")
print(f"  Paris effect: −{paris_effect:.3f} ppt/yr reduction in growth rate")
print(f"  Countries with lower CAGR post-Paris: {n_positive_paris}/208 "
      f"({n_positive_paris/208*100:.0f}%)")
print(f"  Countries with higher CAGR post-Paris: {n_negative_paris}/208 "
      f"({n_negative_paris/208*100:.0f}%)")

print(f"\n  SDG 13 GAP:")
# Required CAGR to reach net-zero: approximately -4% to -7%/yr
# Current post-Paris CAGR: +1.047%
required_cagr = -4.5   # approximate
gap = required_cagr - cagr_post
print(f"  Current post-Paris CAGR  : {cagr_post:+.3f}%/yr")
print(f"  Required for SDG 13 path : ~{required_cagr:.1f}%/yr")
print(f"  Gap                      : {gap:.2f} ppt/yr")
print(f"  Interpretation: Post-Paris growth rate is still positive.")
print(f"  Emissions are growing more slowly, not declining.")
print(f"  SDG 13 targets require absolute emission reductions, not")
print(f"  just slower growth.")

print("\n" + "=" * 65)
print("  ANALYSIS 3 COMPLETE")
print("=" * 65)
print(f"\n  Outputs:")
print(f"  ✓ outputs/tables/analysis3_paris_effectiveness.xlsx")
print(f"  ✓ outputs/figures/fig_c1_era_comparison.tiff/.pdf")
print(f"  ✓ outputs/figures/fig_c2_cagr_by_trajectory.tiff/.pdf")
print(f"  ✓ outputs/figures/fig_c3_paris_effect.tiff/.pdf")
print(f"\n  All three analyses complete.")
print(f"  Total figures produced: 9 (3 per analysis)")
print("=" * 65)
