"""
Sensitivity Analysis — Uncertainty Classification

Purpose:
    Identifies borderline classifications near each threshold boundary under
    plausible EDGAR inventory uncertainty. Reports robust vs ambiguous counts.
    Consistent with Sensitivity Analysis_Threshold.py and
    Sensitivity Analysis_Sample Composition.py naming convention.

Approach:
    For each country, propagate EDGAR measurement uncertainty into ChangePct:
    - OECD countries: ±5% on both E_1970 and E_2024
    - Non-Annex I countries: ±15% on both E_1970 and E_2024

    Worst-case ChangePct range per country:
    - ChangePct_lower = ((E_2024*(1-u) - E_1970*(1+u)) / E_1970*(1+u)) x 100
    - ChangePct_upper = ((E_2024*(1+u) - E_1970*(1-u)) / E_1970*(1-u)) x 100

    If lower and upper bounds give different trajectory classifications:
    classification is AMBIGUOUS. Otherwise: ROBUST.

Thresholds (Baseline):
    Declining         : ChangePct < -10%
    Stable            : -10% <= ChangePct <= +10%
    Moderately Rising : +10% < ChangePct <= +100%
    Rapidly Rising    : ChangePct > +100%

Inputs:
    - Processed_GHG_totals_by_country.csv
    - analysis1_trajectory_results.xlsx (Country_Classifications sheet)

Outputs:
    - Terminal: borderline counts per threshold, robust vs ambiguous counts
    - uncertainty_classification_results.xlsx

Author: Pri / STOTEN revision — Major Comment 5
"""

import os
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH    = os.path.join(PROJECT_ROOT, "data", "processed", "Processed_GHG_totals_by_country.csv")
TABLE_PATH   = os.path.join(PROJECT_ROOT, "outputs", "tables")

# ── 1. Load data ──────────────────────────────────────────────────────────────

raw = pd.read_csv(DATA_PATH)
results = pd.read_excel(
    os.path.join(TABLE_PATH, "Analysis_Trajectory Classification.xlsx"),
    sheet_name="Country_Classifications"
)

# Merge emissions with classifications
raw_slim = raw[["Country", "EDGAR_Code", "1970", "2024"]].copy()
raw_slim.columns = ["Country", "EDGAR_Code", "E_1970", "E_2024"]
df = results.merge(raw_slim, on="Country", how="left")

print(f"Countries loaded: {len(df)}")
print()

# ── 2. Define OECD vs non-Annex I uncertainty ────────────────────────────────
# OECD country codes — Annex I developed countries in EDGAR
OECD_CODES = [
    'AUS','AUT','BEL','CAN','CHL','COL','CZE','DNK','EST','FIN',
    'FRA','DEU','GRC','HUN','ISL','IRL','ISR','ITA','JPN','KOR',
    'LVA','LTU','LUX','MEX','NLD','NZL','NOR','POL','PRT','SVK',
    'SVN','ESP','SWE','CHE','TUR','GBR','USA','EU27'
]

def get_uncertainty(edgar_code):
    """Return uncertainty factor — Janssens-Maenhout et al. (2019, p.974)."""
    if edgar_code in OECD_CODES:
        return 0.05   # +/-5% for OECD countries
    else:
        return 0.15   # +/-15% for non-Annex I countries

df['uncertainty'] = df['EDGAR_Code'].apply(get_uncertainty)

# ── 3. Classification function — consistent with Analysis_Trajectory Classification.py ──

def classify(change_pct):
    if change_pct < -10:
        return 'Declining'
    elif change_pct <= 10:
        return 'Stable'
    elif change_pct <= 100:
        return 'Moderately Rising'
    else:
        return 'Rapidly Rising'

# ── 4. Compute worst-case ChangePct range per country ────────────────────────

def change_pct_lower(e2024, e1970, u):
    """Minimum possible ChangePct under uncertainty."""
    return ((e2024 * (1 - u)) - (e1970 * (1 + u))) / (e1970 * (1 + u)) * 100

def change_pct_upper(e2024, e1970, u):
    """Maximum possible ChangePct under uncertainty."""
    return ((e2024 * (1 + u)) - (e1970 * (1 - u))) / (e1970 * (1 - u)) * 100

df['ChangePct_central'] = df['Change_Pct_1970_2024']
df['ChangePct_lower'] = df.apply(
    lambda r: change_pct_lower(r['E_2024'], r['E_1970'], r['uncertainty']), axis=1
)
df['ChangePct_upper'] = df.apply(
    lambda r: change_pct_upper(r['E_2024'], r['E_1970'], r['uncertainty']), axis=1
)

df['Class_central'] = df['ChangePct_central'].apply(classify)
df['Class_lower']   = df['ChangePct_lower'].apply(classify)
df['Class_upper']   = df['ChangePct_upper'].apply(classify)

# ── 5. Identify robust vs ambiguous ──────────────────────────────────────────

df['Robust'] = (df['Class_lower'] == df['Class_upper'])
df['Status'] = df['Robust'].apply(lambda x: 'Robust' if x else 'Ambiguous')

# ── 6. Overall results ────────────────────────────────────────────────────────

print("=" * 70)
print("UNCERTAINTY PROPAGATION RESULTS")
print("=" * 70)
print()

total = len(df)
robust_n = df['Robust'].sum()
ambiguous_n = total - robust_n

print(f"Total classifications:  {total}")
print(f"Robust classifications: {robust_n} ({robust_n/total*100:.1f}%)")
print(f"Ambiguous:              {ambiguous_n} ({ambiguous_n/total*100:.1f}%)")
print()

# ── 7. Breakdown by threshold boundary ───────────────────────────────────────

print("=" * 70)
print("AMBIGUOUS CLASSIFICATIONS BY THRESHOLD BOUNDARY")
print("=" * 70)

ambiguous = df[~df['Robust']].copy()

# Near -10% threshold (Declining/Stable)
near_neg10 = ambiguous[
    (ambiguous['Class_lower'].isin(['Declining','Stable'])) &
    (ambiguous['Class_upper'].isin(['Declining','Stable']))
]
print(f"\nNear -10% threshold (Declining/Stable boundary): {len(near_neg10)} countries")
if len(near_neg10) > 0:
    for _, row in near_neg10.iterrows():
        print(f"  {row['Country']:30s} ChangePct={row['ChangePct_central']:+.1f}%  "
              f"Range=[{row['ChangePct_lower']:+.1f}%, {row['ChangePct_upper']:+.1f}%]  "
              f"Central={row['Class_central']}")

# Near +10% threshold (Stable/Moderately Rising)
near_pos10 = ambiguous[
    (ambiguous['Class_lower'].isin(['Stable','Moderately Rising'])) &
    (ambiguous['Class_upper'].isin(['Stable','Moderately Rising']))
]
print(f"\nNear +10% threshold (Stable/Moderately Rising boundary): {len(near_pos10)} countries")
if len(near_pos10) > 0:
    for _, row in near_pos10.iterrows():
        print(f"  {row['Country']:30s} ChangePct={row['ChangePct_central']:+.1f}%  "
              f"Range=[{row['ChangePct_lower']:+.1f}%, {row['ChangePct_upper']:+.1f}%]  "
              f"Central={row['Class_central']}")

# Near +100% threshold (Moderately Rising/Rapidly Rising)
near_pos100 = ambiguous[
    (ambiguous['Class_lower'].isin(['Moderately Rising','Rapidly Rising'])) &
    (ambiguous['Class_upper'].isin(['Moderately Rising','Rapidly Rising']))
]
print(f"\nNear +100% threshold (Moderately Rising/Rapidly Rising boundary): {len(near_pos100)} countries")
if len(near_pos100) > 0:
    for _, row in near_pos100.iterrows():
        print(f"  {row['Country']:30s} ChangePct={row['ChangePct_central']:+.1f}%  "
              f"Range=[{row['ChangePct_lower']:+.1f}%, {row['ChangePct_upper']:+.1f}%]  "
              f"Central={row['Class_central']}")

# Countries spanning multiple categories
multi_jump = ambiguous[ambiguous['Class_lower'] != ambiguous['Class_upper']]
multi_jump = multi_jump[~(
    (multi_jump['Class_lower'].isin(['Declining','Stable'])) &
    (multi_jump['Class_upper'].isin(['Declining','Stable']))
) & ~(
    (multi_jump['Class_lower'].isin(['Stable','Moderately Rising'])) &
    (multi_jump['Class_upper'].isin(['Stable','Moderately Rising']))
) & ~(
    (multi_jump['Class_lower'].isin(['Moderately Rising','Rapidly Rising'])) &
    (multi_jump['Class_upper'].isin(['Moderately Rising','Rapidly Rising']))
)]
if len(multi_jump) > 0:
    print(f"\nCountries spanning multiple categories under uncertainty: {len(multi_jump)}")
    for _, row in multi_jump.iterrows():
        print(f"  {row['Country']:30s} Central={row['Class_central']} "
              f"Lower={row['Class_lower']} Upper={row['Class_upper']}")

# ── 8. Ambiguous count by trajectory group ────────────────────────────────────

print()
print("=" * 70)
print("AMBIGUOUS COUNT BY TRAJECTORY GROUP")
print("=" * 70)

for cat in ['Declining', 'Stable', 'Moderately Rising', 'Rapidly Rising']:
    group = df[df['Trajectory_Type'] == cat]
    amb = (~group['Robust']).sum()
    rob = group['Robust'].sum()
    print(f"{cat:20s}: {rob} robust, {amb} ambiguous ({amb/len(group)*100:.1f}% ambiguous)")

# ── 9. OECD vs non-Annex I breakdown ─────────────────────────────────────────

print()
print("=" * 70)
print("AMBIGUOUS COUNT BY UNCERTAINTY LEVEL")
print("=" * 70)

oecd_group = df[df['uncertainty'] == 0.05]
nonannex_group = df[df['uncertainty'] == 0.15]

oecd_amb = (~oecd_group['Robust']).sum()
nonannex_amb = (~nonannex_group['Robust']).sum()

print(f"OECD (+/-5%):         {len(oecd_group)} countries — "
      f"{oecd_amb} ambiguous ({oecd_amb/len(oecd_group)*100:.1f}%)")
print(f"Non-Annex I (+/-15%): {len(nonannex_group)} countries — "
      f"{nonannex_amb} ambiguous ({nonannex_amb/len(nonannex_group)*100:.1f}%)")

# ── 10. Save results ──────────────────────────────────────────────────────────

OUTPUT_PATH = os.path.join(TABLE_PATH, "uncertainty_classification_results.xlsx")

with pd.ExcelWriter(
    OUTPUT_PATH, engine="openpyxl"
) as writer:

    df[['Country', 'EDGAR_Code', 'uncertainty', 'Trajectory_Type',
        'ChangePct_central', 'ChangePct_lower', 'ChangePct_upper',
        'Class_central', 'Class_lower', 'Class_upper', 'Status']].to_excel(
        writer, sheet_name='Full_Results', index=False
    )

    if len(ambiguous) > 0:
        ambiguous[['Country', 'EDGAR_Code', 'uncertainty', 'Trajectory_Type',
                   'ChangePct_central', 'ChangePct_lower', 'ChangePct_upper',
                   'Class_central', 'Class_lower', 'Class_upper']].to_excel(
            writer, sheet_name='Ambiguous_Countries', index=False
        )

print()
print(f"Results saved to: {OUTPUT_PATH}")
print("Sheets: Full_Results, Ambiguous_Countries")
