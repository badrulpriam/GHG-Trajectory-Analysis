# =============================================================================
# ANALYSIS 1 — EMISSION TRAJECTORY CLASSIFICATION & SDG 13 ALIGNMENT
# Project  : GHG Persistence Study
# Journal  : Science of the Total Environment (STOTEN)
# =============================================================================
#
# RESEARCH QUESTION:
#   Which national GHG emission trajectories are consistent with SDG 13
#   targets, and how are these distributed globally across 208 nations
#   over the period 1970–2024?
#
# CLASSIFICATION FRAMEWORK (based on % change 1970–2024):
#   Declining          : < −10%   → SDG-Aligned
#   Stable             : −10% to +10% → SDG-Transitioning
#   Moderately Rising  : +10% to +100% → SDG-At Risk
#   Rapidly Rising     : > +100% → SDG-Critical
#
# SDG 13 LINKAGE:
#   SDG 13.1 → resilience: are countries reducing climate pressure?
#   SDG 13.2 → policy integration: which countries have structurally
#              decoupled emissions from economic activity?
# =============================================================================

import os
import warnings
import numpy as np
import pandas as pd
warnings.filterwarnings('ignore')

# ── PATHS ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH    = os.path.join(PROJECT_ROOT, "data", "processed", "ghg_clean.csv")
TABLE_PATH   = os.path.join(PROJECT_ROOT, "outputs", "tables")

EDGAR_GLOBAL_TOTAL_2024 = 53206.4  # Mt CO2-eq — EDGAR GLOBAL TOTAL row, pre-exclusion

SDG_LABELS = {
    'Declining'         : 'SDG 13.2-Aligned',
    'Stable'            : 'SDG 13.2-Transitioning',
    'Moderately Rising' : 'SDG 13.2-At Risk',
    'Rapidly Rising'    : 'SDG 13.2-Critical',
}
TRAJ_ORDER = ['Declining', 'Stable', 'Moderately Rising', 'Rapidly Rising']

print("=" * 65)
print("  ANALYSIS 1 — EMISSION TRAJECTORY CLASSIFICATION")
print("=" * 65)

# =============================================================================
# STEP 1 — LOAD AND COMPUTE METRICS
# =============================================================================
print("\n[Step 1] Loading data and computing trajectory metrics...")

df = pd.read_csv(DATA_PATH)
df['Year'] = df['Year'].astype(int)

# Reshape to wide for metrics computation
df_wide = df.pivot(
    index='Country', columns='Year', values='GHG_Emissions'
).copy()

# Core metrics
df_wide['emis_1970']         = df_wide[1970]
df_wide['emis_2024']         = df_wide[2024]
df_wide['emis_mean']         = df_wide.loc[:, 1970:2024].mean(axis=1)
df_wide['emis_peak']         = df_wide.loc[:, 1970:2024].max(axis=1)
df_wide['peak_year']         = df_wide.loc[:, 1970:2024].idxmax(axis=1)
df_wide['change_abs']        = df_wide['emis_2024'] - df_wide['emis_1970']
df_wide['change_pct']        = (df_wide['change_abs'] / df_wide['emis_1970']) * 100
df_wide['change_pct_2015_24']= ((df_wide[2024] - df_wide[2015]) / df_wide[2015]) * 100
df_wide['cagr_full']         = ((df_wide['emis_2024'] / df_wide['emis_1970'])
                                ** (1 / 54) - 1) * 100   # 54 years 1970→2024
df_wide['cagr_post_paris']   = ((df_wide[2024] / df_wide[2015])
                                ** (1 / 9) - 1) * 100    # 9 years 2015→2024

print(f"  Countries loaded : {len(df_wide)}")
print(f"  All metrics computed successfully")

# =============================================================================
# STEP 2 — TRAJECTORY CLASSIFICATION
# =============================================================================
print("\n[Step 2] Classifying trajectory types...")

def classify_trajectory(pct_change):
    """
    Classify country based on % change in GHG emissions, 1970–2024.
    Thresholds aligned with IPCC terminology and SDG 13 monitoring.
    """
    if pct_change < -10:    return 'Declining'
    elif pct_change <= 10:  return 'Stable'
    elif pct_change <= 100: return 'Moderately Rising'
    else:                   return 'Rapidly Rising'

def sdg_alignment(trajectory):
    """Map trajectory type to SDG 13 alignment status."""
    return SDG_LABELS[trajectory]

df_wide['trajectory'] = df_wide['change_pct'].apply(classify_trajectory)
df_wide['sdg_status'] = df_wide['trajectory'].apply(sdg_alignment)

# Count per category
counts = df_wide['trajectory'].value_counts()
print(f"\n  TRAJECTORY CLASSIFICATION RESULTS:")
print(f"  {'Category':<25} {'Count':>6}  {'Share':>8}  {'SDG Status'}")
print(f"  {'-'*65}")
for t in TRAJ_ORDER:
    n   = counts.get(t, 0)
    pct = n / len(df_wide) * 100
    print(f"  {t:<25} {n:>6}  {pct:>7.1f}%  {SDG_LABELS[t]}")
print(f"  {'-'*65}")
print(f"  {'TOTAL':<25} {len(df_wide):>6}  {'100.0%':>8}")

# =============================================================================
# STEP 4 — EXPORT RESULTS TABLES
# =============================================================================
print("\n[Step 4] Exporting results tables...")

# Full classification table
results_df = df_wide[[
    'emis_1970', 'emis_2024', 'emis_mean',
    'change_pct', 'change_pct_2015_24',
    'cagr_full', 'cagr_post_paris',
    'peak_year', 'emis_peak',
    'trajectory', 'sdg_status'
]].copy().reset_index()

results_df.columns = [
    'Country',
    'GHG_1970_Mt', 'GHG_2024_Mt', 'GHG_Mean_Mt',
    'Change_Pct_1970_2024', 'Change_Pct_2015_2024',
    'CAGR_Full_Pct', 'CAGR_PostParis_Pct',
    'Peak_Emission_Year', 'Peak_Emission_Mt',
    'Trajectory_Type', 'SDG13.2_Status'
]
results_df = results_df.round(3)
results_df = results_df.sort_values('Trajectory_Type')

# Summary table for paper (Table 1)
summary_table = pd.DataFrame({
    'Trajectory Type'   : TRAJ_ORDER,
    'SDG 13.2 Status'   : [SDG_LABELS[t] for t in TRAJ_ORDER],
    'Threshold (1970–2024)': ['< −10%', '−10% to +10%', '+10% to +100%', '> +100%'],
    'N Countries'       : [counts.get(t, 0) for t in TRAJ_ORDER],
    'Share (%)'         : [f"{counts.get(t,0)/len(df_wide)*100:.1f}" for t in TRAJ_ORDER],
    'Mean Change (%)'   : [df_wide[df_wide['trajectory']==t]['change_pct'].mean().round(1)
                           for t in TRAJ_ORDER],
    'Median Change (%)' : [df_wide[df_wide['trajectory']==t]['change_pct'].median().round(1)
                           for t in TRAJ_ORDER],
    'Mean Full CAGR (%/yr)': [df_wide[df_wide['trajectory']==t]['cagr_full'].mean().round(3)
                               for t in TRAJ_ORDER],
})

with pd.ExcelWriter(
    os.path.join(TABLE_PATH, 'Analysis_Trajectory Classification.xlsx'),
    engine='openpyxl'
) as writer:
    results_df.to_excel(writer, sheet_name='Country_Classifications', index=False)
    summary_table.to_excel(writer, sheet_name='Summary_Table1', index=False)
    # Per-trajectory sheets
    for t in TRAJ_ORDER:
        subset = results_df[results_df['Trajectory_Type'] == t].copy()
        sheet  = t.replace(' ', '_')[:31]
        subset.to_excel(writer, sheet_name=sheet, index=False)
    # Post-Paris summary sheet (Table 3.2)
    pp_rows = []
    for t in TRAJ_ORDER:
        grp   = df_wide[df_wide['trajectory'] == t]['cagr_post_paris']
        n     = len(grp)
        pos_n = int((grp > 0).sum())
        neg_n = int((grp < 0).sum())
        pp_rows.append({
            'Category'               : t,
            'Post_Paris_CAGR_Pct_yr' : round(grp.mean(), 3),
            'Positive_PostParis_N'   : pos_n,
            'Positive_PostParis_Pct' : round(pos_n / n * 100, 1),
            'Negative_PostParis_N'   : neg_n,
            'Negative_PostParis_Pct' : round(neg_n / n * 100, 1),
        })
    pp_rows.append({
        'Category'               : 'Global Mean',
        'Post_Paris_CAGR_Pct_yr' : round(df_wide['cagr_post_paris'].mean(), 3),
        'Positive_PostParis_N'   : None,
        'Positive_PostParis_Pct' : None,
        'Negative_PostParis_N'   : None,
        'Negative_PostParis_Pct' : None,
    })
    pd.DataFrame(pp_rows).to_excel(writer, sheet_name='Post_Paris_Summary', index=False)

print(f"  ✓ Saved: Analysis_Trajectory Classification.xlsx")

# =============================================================================
# STEP 8 — KEY STATISTICS FOR PAPER WRITE-UP
# =============================================================================
print("\n[Step 8] Key statistics for paper (Methods & Results sections):")
print("=" * 65)

for t in TRAJ_ORDER:
    sub = df_wide[df_wide['trajectory'] == t]
    print(f"\n  {t.upper()} — {SDG_LABELS[t]}")
    print(f"    Countries      : {len(sub)} ({len(sub)/len(df_wide)*100:.1f}%)")
    print(f"    Change range   : {sub['change_pct'].min():.1f}% to {sub['change_pct'].max():.1f}%")
    print(f"    Mean change    : {sub['change_pct'].mean():.1f}%")
    print(f"    Median change  : {sub['change_pct'].median():.1f}%")
    print(f"    Mean CAGR (full): {sub['cagr_full'].mean():.3f} %/yr")
    print(f"    Median 2024    : {sub['emis_2024'].median():.1f} Mt CO₂-eq")

# POST-PARIS AGREEMENT TRAJECTORY DYNAMICS
print(f"\nPOST-PARIS AGREEMENT  TRAJECTORY DYNAMICS (2015-2024):")
print(f"  {'Category':<18} {'Post-Paris CAGR':>12}   {'Positive N (%)':>15}   Negative N (%)")
for t in TRAJ_ORDER:
    sub      = df_wide[df_wide['trajectory'] == t]
    n        = len(sub)
    mean_pp  = sub['cagr_post_paris'].mean()
    pos_n    = int((sub['cagr_post_paris'] > 0).sum())
    neg_n    = int((sub['cagr_post_paris'] < 0).sum())
    cagr_str = f"{mean_pp:+.3f} %/yr"
    pos_str  = f"{pos_n}/{n} ({pos_n/n*100:.1f}%)"
    neg_str  = f"{neg_n}/{n} ({neg_n/n*100:.1f}%)"
    print(f"  {t:<18} {cagr_str:>12}   {pos_str:>15}   {neg_str}")

global_cagr_str = f"{df_wide['cagr_post_paris'].mean():+.3f} %/yr"
print(f"  {'Global Mean':<18} {global_cagr_str:>12}   {'-':>15}   -")

# Global headline stats
total_1970 = df[df['Year']==1970]['GHG_Emissions'].sum()
print(f"\n  GLOBAL TOTALS:")
print(f"    1970 : {total_1970:,.1f} Mt CO₂-eq")
print(f"    2024 : {EDGAR_GLOBAL_TOTAL_2024:,.1f} Mt CO₂-eq")
print(f"    Change: {((EDGAR_GLOBAL_TOTAL_2024-total_1970)/total_1970*100):+.1f}%")

print("\n" + "=" * 65)
print("  ANALYSIS 1 COMPLETE")
print("=" * 65)
print(f"\n  Outputs:")
print(f"  ✓ outputs/tables/Analysis_Trajectory Classification.xlsx")
print("=" * 65)
