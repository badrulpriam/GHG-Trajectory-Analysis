# =============================================================================
# ANALYSIS 2 — SHOCK RESPONSE & EMISSION RESILIENCE
# Project  : GHG Persistence Study
# Journal  : Ecological Indicators
# =============================================================================
#
# RESEARCH QUESTION:
#   Do major global shocks produce lasting reductions in national GHG
#   emissions, or does the global emissions system simply absorb shocks
#   and rebound? This is an ecological resilience analysis — measuring
#   the resistance and recovery of GHG as a pressure indicator.
#
# SHOCKS ANALYSED:
#   1. GFC 2009  — Global Financial Crisis trough
#   2. Paris 2015 — Paris Agreement adoption year
#   3. COVID 2020 — COVID-19 pandemic
#
# RESILIENCE METRICS (per country, per shock):
#   Resistance  : % change in emissions at shock year vs pre-shock year
#   Recovery    : % change 3 years post-shock vs pre-shock baseline
#   Permanence  : is post-shock level above or below pre-shock level?
#
# RESILIENCE CLASSIFICATION:
#   Absorbed    : emissions dropped AND remained below pre-shock (permanent)
#   Rebounded   : emissions dropped then exceeded pre-shock (temporary)
#   Unaffected  : emissions did not drop at shock year
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
SHOCK_COLOURS = {
    'GFC 2009'   : '#0072B2',
    'Paris 2015' : '#009E73',
    'COVID 2020' : '#D55E00',
}
RESILIENCE_COLOURS = {
    'Absorbed'   : '#1A7A4A',   # green — permanent reduction
    'Rebounded'  : '#E07B20',   # orange — temporary drop
    'Unaffected' : '#C0392B',   # red — no response
}

# ── SHOCK DEFINITIONS ─────────────────────────────────────────────────────────
# pre      : baseline year (one year before shock)
# shock    : year of shock
# post3    : 3 years after shock (recovery check)
# window   : years to plot around shock for profile charts
SHOCKS = {
    'GFC 2009'   : {'pre': 2008, 'shock': 2009, 'post3': 2012,
                    'window': range(2005, 2014)},
    'Paris 2015' : {'pre': 2014, 'shock': 2015, 'post3': 2018,
                    'window': range(2012, 2021)},
    'COVID 2020' : {'pre': 2019, 'shock': 2020, 'post3': 2023,
                    'window': range(2017, 2025)},
}

print("=" * 65)
print("  ANALYSIS 2 — SHOCK RESPONSE & EMISSION RESILIENCE")
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
    traj_df = pd.read_excel(traj_path, sheet_name='Country_Classifications')
    traj_map = dict(zip(traj_df['Country'], traj_df['Trajectory_Type']))
    print(f"  Trajectory classifications loaded from Analysis 1")
else:
    traj_map = {}
    print(f"  WARNING: Run analysis1 first for trajectory labels")

print(f"  Countries: {len(df_wide)} | Years: 1970–2024")

# =============================================================================
# STEP 2 — COMPUTE RESILIENCE METRICS PER SHOCK
# =============================================================================
print("\n[Step 2] Computing resilience metrics for each shock...")

all_resilience = []

for shock_name, s in SHOCKS.items():
    pre_yr   = s['pre']
    shock_yr = s['shock']
    post_yr  = s['post3']

    # Get common countries with data for all three years
    common = (df_wide[pre_yr].dropna().index
              .intersection(df_wide[shock_yr].dropna().index)
              .intersection(df_wide[post_yr].dropna().index))

    for country in common:
        pre_val   = df_wide.loc[country, pre_yr]
        shock_val = df_wide.loc[country, shock_yr]
        post_val  = df_wide.loc[country, post_yr]

        resistance  = (shock_val - pre_val) / pre_val * 100
        recovery    = (post_val  - pre_val) / pre_val * 100
        dropped     = shock_val < pre_val
        permanent   = post_val  < pre_val   # still below baseline 3 yrs later

        # Resilience classification
        if dropped and permanent:
            resilience = 'Absorbed'          # shock produced lasting reduction
        elif dropped and not permanent:
            resilience = 'Rebounded'         # temporary drop, then exceeded baseline
        else:
            resilience = 'Unaffected'        # emissions did not fall at shock

        all_resilience.append({
            'Country'          : country,
            'Shock'            : shock_name,
            'Trajectory_Type'  : traj_map.get(country, 'Unknown'),
            'Pre_Shock_Emis'   : pre_val,
            'Shock_Year_Emis'  : shock_val,
            'Post3yr_Emis'     : post_val,
            'Resistance_Pct'   : resistance,
            'Recovery_Pct'     : recovery,
            'Dropped_At_Shock' : dropped,
            'Permanent_Below'  : permanent,
            'Resilience_Class' : resilience,
        })

resilience_df = pd.DataFrame(all_resilience)
print(f"  Computed metrics for {len(resilience_df):,} country-shock observations")

# =============================================================================
# STEP 3 — SUMMARY STATISTICS PER SHOCK
# =============================================================================
print("\n[Step 3] Summary statistics by shock event:")
print("=" * 65)

for shock_name in SHOCKS.keys():
    sub = resilience_df[resilience_df['Shock'] == shock_name]
    n   = len(sub)

    abs_count = (sub['Resilience_Class'] == 'Absorbed').sum()
    reb_count = (sub['Resilience_Class'] == 'Rebounded').sum()
    una_count = (sub['Resilience_Class'] == 'Unaffected').sum()

    mean_resist  = sub['Resistance_Pct'].mean()
    mean_recover = sub['Recovery_Pct'].mean()

    print(f"\n  {shock_name}  (n = {n} countries)")
    print(f"  {'─'*50}")
    print(f"  Resistance (mean Δ at shock year) : {mean_resist:+.2f}%")
    print(f"  Recovery   (mean Δ 3yr post)      : {mean_recover:+.2f}%")
    print(f"  Absorbed   (permanent reduction)  : {abs_count:3d}  ({abs_count/n*100:.0f}%)")
    print(f"  Rebounded  (temporary drop)        : {reb_count:3d}  ({reb_count/n*100:.0f}%)")
    print(f"  Unaffected (no drop at shock)      : {una_count:3d}  ({una_count/n*100:.0f}%)")

# =============================================================================
# STEP 4 — EXPORT RESULTS TABLE
# =============================================================================
print("\n\n[Step 4] Exporting results table...")

# Pivot wide: one row per country, columns per shock
pivot_cols = ['Resistance_Pct', 'Recovery_Pct', 'Resilience_Class']
wide_parts = []
for shock_name in SHOCKS.keys():
    sub = resilience_df[resilience_df['Shock'] == shock_name][
        ['Country', 'Trajectory_Type'] + pivot_cols
    ].copy()
    suffix = shock_name.replace(' ', '_')
    sub = sub.rename(columns={
        'Resistance_Pct'  : f'Resistance_Pct_{suffix}',
        'Recovery_Pct'    : f'Recovery_Pct_{suffix}',
        'Resilience_Class': f'Resilience_{suffix}',
    })
    wide_parts.append(sub.set_index('Country'))

resilience_wide = pd.concat([p.drop(columns='Trajectory_Type')
                              for p in wide_parts], axis=1)
resilience_wide.insert(0, 'Trajectory_Type',
                       wide_parts[0]['Trajectory_Type'])
resilience_wide = resilience_wide.round(2).reset_index()

# Summary table for paper (Table 2)
summary_rows = []
for shock_name in SHOCKS.keys():
    sub = resilience_df[resilience_df['Shock'] == shock_name]
    n   = len(sub)
    summary_rows.append({
        'Shock Event'               : shock_name,
        'N Countries'               : n,
        'Mean Resistance (%)'       : round(sub['Resistance_Pct'].mean(), 2),
        'SD Resistance (%)'         : round(sub['Resistance_Pct'].std(), 2),
        'Mean Recovery 3yr (%)'     : round(sub['Recovery_Pct'].mean(), 2),
        'Absorbed (N, %)'           : f"{(sub['Resilience_Class']=='Absorbed').sum()} ({(sub['Resilience_Class']=='Absorbed').sum()/n*100:.0f}%)",
        'Rebounded (N, %)'          : f"{(sub['Resilience_Class']=='Rebounded').sum()} ({(sub['Resilience_Class']=='Rebounded').sum()/n*100:.0f}%)",
        'Unaffected (N, %)'         : f"{(sub['Resilience_Class']=='Unaffected').sum()} ({(sub['Resilience_Class']=='Unaffected').sum()/n*100:.0f}%)",
    })
summary_table = pd.DataFrame(summary_rows)

with pd.ExcelWriter(
    os.path.join(TABLE_PATH, 'analysis2_shock_resilience.xlsx'),
    engine='openpyxl'
) as writer:
    resilience_wide.to_excel(writer, sheet_name='Country_Resilience', index=False)
    summary_table.to_excel(writer, sheet_name='Summary_Table2', index=False)
    resilience_df.to_excel(writer, sheet_name='Full_Data', index=False)

print(f"  ✓ Saved: analysis2_shock_resilience.xlsx")

# =============================================================================
# STEP 5 — FIGURE B1: GLOBAL SHOCK RESPONSE PROFILES
# Left: normalised global emission index around each shock (pre = 100)
# Right: resilience classification stacked bars per shock
# =============================================================================
print("\n[Step 5] Generating Figure B1: Shock response profiles...")

fig1, (ax_left, ax_right) = plt.subplots(
    1, 2,
    figsize=(W2, W2 * 0.48),
    facecolor='white',
    gridspec_kw={'wspace': 0.38}
)

# ── Left panel: normalised global emission index ───────────────────────────────
ax = ax_left
ax.set_facecolor('white')

global_annual = df.groupby('Year')['GHG_Emissions'].sum().reset_index()
global_annual.columns = ['Year', 'Total']

for shock_name, s in SHOCKS.items():
    col      = SHOCK_COLOURS[shock_name]
    pre_val  = global_annual.loc[global_annual['Year'] == s['pre'], 'Total'].values[0]
    window   = list(s['window'])
    yrs      = global_annual[global_annual['Year'].isin(window)]['Year'].values
    vals     = global_annual[global_annual['Year'].isin(window)]['Total'].values
    idx      = (vals / pre_val) * 100

    # Relative year (0 = pre-shock year)
    rel_yrs = [y - s['pre'] for y in yrs]

    ax.plot(rel_yrs, idx, color=col, linewidth=1.8,
            solid_capstyle='round', zorder=4, label=shock_name)
    ax.scatter([0], [100], color=col, s=35, zorder=6, clip_on=False)

ax.axhline(100, color='#444444', linewidth=0.9, linestyle='--',
           alpha=0.55, zorder=3, label='Pre-shock baseline')
ax.axvline(0,   color='#444444', linewidth=0.7, linestyle=':',
           alpha=0.40, zorder=3)

ax.set_xlabel('Years relative to shock year (0 = shock year)', fontsize=8.5, labelpad=4)
ax.set_ylabel('Global GHG index (pre-shock year = 100)', fontsize=8.5, labelpad=4)
ax.xaxis.set_major_locator(mticker.MultipleLocator(2))
ax.yaxis.grid(True, color='#E8E8E8', linewidth=0.5, zorder=0)
ax.set_axisbelow(True)

ax.legend(loc='lower right', fontsize=7.5, frameon=True,
          framealpha=0.95, edgecolor='#CCCCCC', fancybox=False,
          borderpad=0.5, labelspacing=0.30, handlelength=1.8)

ax.text(-0.12, 1.05, '(a)', transform=ax.transAxes,
        fontsize=10, fontweight='bold', va='bottom')

# ── Right panel: stacked resilience classification ────────────────────────────
ax = ax_right
ax.set_facecolor('white')

shock_labels  = list(SHOCKS.keys())
res_classes   = ['Absorbed', 'Rebounded', 'Unaffected']
bar_width     = 0.55

bottoms = np.zeros(3)
for res_class in res_classes:
    vals = []
    for sn in shock_labels:
        sub = resilience_df[resilience_df['Shock'] == sn]
        pct = (sub['Resilience_Class'] == res_class).sum() / len(sub) * 100
        vals.append(pct)
    bars = ax.bar(range(3), vals, bar_width,
                  bottom=bottoms, color=RESILIENCE_COLOURS[res_class],
                  edgecolor='white', linewidth=0.5, label=res_class, zorder=3)
    # Add value labels inside bars if >8%
    for i, (v, b) in enumerate(zip(vals, bottoms)):
        if v > 8:
            ax.text(i, b + v/2, f'{v:.0f}%',
                    ha='center', va='center', fontsize=7,
                    color='white', fontweight='medium')
    bottoms += np.array(vals)

ax.set_xticks(range(3))
ax.set_xticklabels(['GFC\n2009', 'Paris\n2015', 'COVID\n2020'], fontsize=8)
ax.set_ylabel('Share of countries (%)', fontsize=8.5, labelpad=4)
ax.set_ylim(0, 100)
ax.yaxis.grid(True, color='#E8E8E8', linewidth=0.5, zorder=0)
ax.set_axisbelow(True)

ax.legend(loc='upper left', fontsize=7.5, frameon=True,
          framealpha=0.95, edgecolor='#CCCCCC', fancybox=False,
          borderpad=0.5, labelspacing=0.30,
          title='Resilience class', title_fontsize=7.8)

ax.text(-0.12, 1.05, '(b)', transform=ax.transAxes,
        fontsize=10, fontweight='bold', va='bottom')

fig1.text(
    0.5, -0.04,
    'Note: Panel (a) global GHG emission index normalised to pre-shock year = 100. '
    'Panel (b) resilience classification: Absorbed = permanent reduction; '
    'Rebounded = temporary drop then exceeded baseline; Unaffected = no emission drop.',
    ha='center', fontsize=6.8, style='italic', color='#555555'
)

fig1.savefig(os.path.join(FIG_PATH, 'fig_b1_shock_profiles.tiff'), **SAVE,
             format='tiff', pil_kwargs={'compression': 'tiff_lzw'})
fig1.savefig(os.path.join(FIG_PATH, 'fig_b1_shock_profiles.pdf'), **SAVE)
plt.close(fig1)
print("   ✓ fig_b1_shock_profiles.tiff / .pdf")

# =============================================================================
# STEP 6 — FIGURE B2: RESILIENCE CLASSIFICATION BY TRAJECTORY TYPE
# Heatmap: trajectory type (rows) × shock (columns) × resilience class (colour)
# Shows whether SDG-aligned countries absorb shocks better
# =============================================================================
print("\n[Step 6] Generating Figure B2: Resilience by trajectory type...")

TRAJ_ORDER = ['Declining', 'Stable', 'Moderately Rising', 'Rapidly Rising']
TRAJ_SHORT = ['Declining', 'Stable', 'Mod. Rising', 'Rapid Rising']

fig2, axes2 = plt.subplots(
    1, 3,
    figsize=(W2, W2 * 0.46),
    facecolor='white',
    gridspec_kw={'wspace': 0.38}
)

panel_labels = ['(a)', '(b)', '(c)']
res_order    = ['Absorbed', 'Rebounded', 'Unaffected']
res_cols     = [RESILIENCE_COLOURS[r] for r in res_order]

for idx, shock_name in enumerate(SHOCKS.keys()):
    ax  = axes2[idx]
    ax.set_facecolor('white')
    sub = resilience_df[resilience_df['Shock'] == shock_name]

    bottoms = np.zeros(len(TRAJ_ORDER))
    for ri, res_class in enumerate(res_order):
        vals = []
        for t in TRAJ_ORDER:
            t_sub = sub[sub['Trajectory_Type'] == t]
            if len(t_sub) == 0:
                vals.append(0)
            else:
                vals.append(
                    (t_sub['Resilience_Class'] == res_class).sum()
                    / len(t_sub) * 100
                )
        bars = ax.bar(range(len(TRAJ_ORDER)), vals, 0.65,
                      bottom=bottoms, color=res_cols[ri],
                      edgecolor='white', linewidth=0.5,
                      label=res_class, zorder=3)
        for i, (v, b) in enumerate(zip(vals, bottoms)):
            if v > 9:
                ax.text(i, b + v/2, f'{v:.0f}%',
                        ha='center', va='center', fontsize=6.8,
                        color='white', fontweight='medium')
        bottoms += np.array(vals)

    ax.set_xticks(range(len(TRAJ_ORDER)))
    ax.set_xticklabels(TRAJ_SHORT, fontsize=7, rotation=25, ha='right')
    ax.set_ylim(0, 100)
    ax.set_title(shock_name, fontsize=8.5, fontweight='medium',
                 color=SHOCK_COLOURS[shock_name], pad=4)

    if idx == 0:
        ax.set_ylabel('Share of countries (%)', fontsize=8.5, labelpad=4)
    else:
        ax.set_ylabel('')
        ax.tick_params(labelleft=False)

    ax.yaxis.grid(True, color='#E8E8E8', linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.text(-0.15, 1.06, panel_labels[idx], transform=ax.transAxes,
            fontsize=10, fontweight='bold', va='bottom')

# Shared legend
handles = [mpatches.Patch(color=RESILIENCE_COLOURS[r], label=r)
           for r in res_order]
fig2.legend(handles=handles, loc='lower center', ncol=3,
            fontsize=7.8, frameon=True, framealpha=0.95,
            edgecolor='#CCCCCC', fancybox=False,
            bbox_to_anchor=(0.5, -0.06),
            title='Resilience class', title_fontsize=8)

fig2.text(
    0.5, -0.13,
    'Note: Panels show resilience classification breakdown by emission trajectory '
    'type for each shock event. Trajectory types from Analysis 1.',
    ha='center', fontsize=6.8, style='italic', color='#555555'
)
fig2.supylabel('Share of countries (%)', x=0.0, fontsize=9)

fig2.savefig(os.path.join(FIG_PATH, 'fig_b2_resilience_by_trajectory.tiff'), **SAVE,
             format='tiff', pil_kwargs={'compression': 'tiff_lzw'})
fig2.savefig(os.path.join(FIG_PATH, 'fig_b2_resilience_by_trajectory.pdf'), **SAVE)
plt.close(fig2)
print("   ✓ fig_b2_resilience_by_trajectory.tiff / .pdf")

# =============================================================================
# STEP 7 — FIGURE B3: COVID-19 SHOCK DEEP-DIVE
# Country-level resistance vs recovery scatter
# Most recent and complete shock — richest story
# =============================================================================
print("\n[Step 7] Generating Figure B3: COVID-19 country-level scatter...")

fig3, ax = plt.subplots(figsize=(W2, W2 * 0.60), facecolor='white')
ax.set_facecolor('white')

covid_sub = resilience_df[resilience_df['Shock'] == 'COVID 2020'].copy()

TRAJ_COLOURS_MAP = {
    'Declining'         : '#1A7A4A',
    'Stable'            : '#F0C040',
    'Moderately Rising' : '#E07B20',
    'Rapidly Rising'    : '#C0392B',
    'Unknown'           : '#888888',
}

for traj in ['Declining', 'Stable', 'Moderately Rising', 'Rapidly Rising']:
    sub = covid_sub[covid_sub['Trajectory_Type'] == traj]
    ax.scatter(
        sub['Resistance_Pct'],
        sub['Recovery_Pct'],
        c=TRAJ_COLOURS_MAP[traj],
        s=np.clip(sub['Pre_Shock_Emis'] / 8, 12, 500),
        alpha=0.65,
        edgecolors='white', linewidths=0.4,
        zorder=4, label=f'{traj} (n={len(sub)})'
    )

# Label top emitters
top_emis = covid_sub.nlargest(10, 'Pre_Shock_Emis')['Country'].tolist()
for _, row in covid_sub[covid_sub['Country'].isin(top_emis)].iterrows():
    ax.annotate(
        row['Country'],
        xy=(row['Resistance_Pct'], row['Recovery_Pct']),
        xytext=(4, 2), textcoords='offset points',
        fontsize=6.2, color='#333333', va='bottom'
    )

# Reference lines
ax.axhline(0, color='#444444', linewidth=0.9, linestyle='--', alpha=0.55, zorder=3)
ax.axvline(0, color='#444444', linewidth=0.9, linestyle='--', alpha=0.55, zorder=3)

# Quadrant labels
xlim = ax.get_xlim()
ylim = ax.get_ylim()
ax.text(0.02, 0.97, 'Dropped & absorbed\n(permanent reduction)',
        transform=ax.transAxes, fontsize=6.5, va='top',
        color='#1A7A4A', style='italic')
ax.text(0.98, 0.97, 'No drop & rising\n(unaffected + growth)',
        transform=ax.transAxes, fontsize=6.5, va='top', ha='right',
        color='#C0392B', style='italic')
ax.text(0.02, 0.04, 'Dropped but still\nbelow baseline',
        transform=ax.transAxes, fontsize=6.5, va='bottom',
        color='#0072B2', style='italic')
ax.text(0.98, 0.04, 'Dropped but rebounded\nabove baseline',
        transform=ax.transAxes, fontsize=6.5, va='bottom', ha='right',
        color='#E07B20', style='italic')

ax.set_xlabel('Resistance — emission change at COVID year vs 2019 (%)',
              fontsize=9, labelpad=4)
ax.set_ylabel('Recovery — emission change 3yr post-COVID vs 2019 (%)',
              fontsize=9, labelpad=4)

ax.yaxis.grid(True, color='#E8E8E8', linewidth=0.5, zorder=0)
ax.xaxis.grid(True, color='#E8E8E8', linewidth=0.5, zorder=0)
ax.set_axisbelow(True)

legend = ax.legend(
    loc='center right',
    fontsize=7.5, frameon=True, framealpha=0.95,
    edgecolor='#CCCCCC', fancybox=False,
    borderpad=0.5, labelspacing=0.35,
    title='Trajectory type', title_fontsize=7.8
)
legend.get_title().set_fontweight('medium')

fig3.text(
    0.5, -0.03,
    'Note: Bubble size proportional to pre-COVID (2019) emission level. '
    'Quadrants defined by zero-change reference lines (dashed). '
    'Upper-left = temporary reduction (rebounded); lower-left = permanent reduction (absorbed).',
    ha='center', fontsize=6.8, style='italic', color='#555555'
)

fig3.savefig(os.path.join(FIG_PATH, 'fig_b3_covid_scatter.tiff'), **SAVE,
             format='tiff', pil_kwargs={'compression': 'tiff_lzw'})
fig3.savefig(os.path.join(FIG_PATH, 'fig_b3_covid_scatter.pdf'), **SAVE)
plt.close(fig3)
print("   ✓ fig_b3_covid_scatter.tiff / .pdf")

# =============================================================================
# STEP 8 — KEY STATISTICS FOR PAPER
# =============================================================================
print("\n[Step 8] Key statistics for paper:")
print("=" * 65)

# COVID headline stats — most relevant for SDG 13
covid_sub = resilience_df[resilience_df['Shock'] == 'COVID 2020']
print(f"\n  COVID-19 SHOCK — Headline Statistics:")
print(f"  Most severe single-year emission shock in study period")
print(f"  Countries with emission drop at shock year : "
      f"{covid_sub['Dropped_At_Shock'].sum()} "
      f"({covid_sub['Dropped_At_Shock'].sum()/len(covid_sub)*100:.0f}%)")
print(f"  Absorbed (permanent)   : "
      f"{(covid_sub['Resilience_Class']=='Absorbed').sum()} "
      f"({(covid_sub['Resilience_Class']=='Absorbed').sum()/len(covid_sub)*100:.0f}%)")
print(f"  Rebounded (temporary)  : "
      f"{(covid_sub['Resilience_Class']=='Rebounded').sum()} "
      f"({(covid_sub['Resilience_Class']=='Rebounded').sum()/len(covid_sub)*100:.0f}%)")
print(f"  Mean resistance (drop) : "
      f"{covid_sub['Resistance_Pct'].mean():+.2f}%")
print(f"  Mean recovery (3yr)    : "
      f"{covid_sub['Recovery_Pct'].mean():+.2f}%")

# GFC comparison
gfc_sub = resilience_df[resilience_df['Shock'] == 'GFC 2009']
print(f"\n  GFC 2009 — For comparison:")
print(f"  Countries with emission drop : "
      f"{gfc_sub['Dropped_At_Shock'].sum()} "
      f"({gfc_sub['Dropped_At_Shock'].sum()/len(gfc_sub)*100:.0f}%)")
print(f"  Absorbed : "
      f"{(gfc_sub['Resilience_Class']=='Absorbed').sum()} "
      f"({(gfc_sub['Resilience_Class']=='Absorbed').sum()/len(gfc_sub)*100:.0f}%)")

# SDG 13 implication statement
print(f"\n  SDG 13 IMPLICATION:")
n_absorbed_all = (resilience_df['Resilience_Class'] == 'Absorbed').sum()
n_total        = len(resilience_df)
print(f"  Across all 3 shocks, only "
      f"{n_absorbed_all}/{n_total} ({n_absorbed_all/n_total*100:.0f}%) "
      f"country-shock observations")
print(f"  resulted in permanent emission reductions (Absorbed class).")
print(f"  Global emission shocks alone are insufficient for SDG 13 compliance.")

print("\n" + "=" * 65)
print("  ANALYSIS 2 COMPLETE")
print("=" * 65)
print(f"\n  Outputs:")
print(f"  ✓ outputs/tables/analysis2_shock_resilience.xlsx")
print(f"  ✓ outputs/figures/fig_b1_shock_profiles.tiff/.pdf")
print(f"  ✓ outputs/figures/fig_b2_resilience_by_trajectory.tiff/.pdf")
print(f"  ✓ outputs/figures/fig_b3_covid_scatter.tiff/.pdf")
print(f"\n  Next: run analysis3_paris_effectiveness.py")
print("=" * 65)
