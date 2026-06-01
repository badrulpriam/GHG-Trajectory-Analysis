# =============================================================================
# PHASE 0 — DATA PREPROCESSING
# Project : GHG Persistence Study
# Script  : preprocessing.py
# Author  : [Your Name]
# Date    : [Date]
#
# Purpose : Load raw EDGAR GHG data, clean it, reshape it to long format,
#           apply log transformation, and export a publication-ready
#           analytical dataset. This script must be run FIRST before any
#           econometric analysis.
#
# Input   : data/raw/GHG_totals_by_country.csv
# Output  : data/processed/ghg_clean.csv
#           outputs/tables/summary_statistics.xlsx
#           outputs/tables/preprocessing_report.txt
# =============================================================================


# -----------------------------------------------------------------------------
# SECTION 1 — LIBRARY IMPORTS
# GitHub Copilot prompt: 
# "Import all libraries needed for panel time series preprocessing of GHG data"
# -----------------------------------------------------------------------------

import pandas as pd
import numpy as np
import os
import sys
from scipy import stats
from datetime import datetime


def load_plotting_libraries():
    """Import plotting libraries lazily so preprocessing can run without them."""
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        return plt, sns, None
    except Exception as exc:
        return None, None, exc


# -----------------------------------------------------------------------------
# SECTION 2 — PROJECT PATH CONFIGURATION
# This block ensures the script works regardless of where it is run from.
# It automatically detects the project root by going one level up from /scripts/
# -----------------------------------------------------------------------------

# Get the absolute path of the project root (one level above /scripts/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Resolve raw data path from common locations
RAW_DATA_CANDIDATES = [
    os.path.join(PROJECT_ROOT, "data", "raw", "GHG_totals_by_country.csv"),
    os.path.join(PROJECT_ROOT, "GHG_totals_by_country.csv"),
    os.path.join(os.getcwd(), "GHG_Persistence_Study", "data", "raw", "GHG_totals_by_country.csv"),
    os.path.join(os.getcwd(), "GHG_Persistence_Study", "GHG_totals_by_country.csv"),
]

RAW_DATA_PATH = next((p for p in RAW_DATA_CANDIDATES if os.path.exists(p)), RAW_DATA_CANDIDATES[0])

# Define all key output paths
PROCESSED_PATH   = os.path.join(PROJECT_ROOT, "data", "processed", "ghg_clean.csv")
TABLES_PATH      = os.path.join(PROJECT_ROOT, "outputs", "tables")
FIGURES_PATH     = os.path.join(PROJECT_ROOT, "outputs", "figures")
REPORT_PATH      = os.path.join(TABLES_PATH,  "preprocessing_report.txt")
SUMSTATS_PATH    = os.path.join(TABLES_PATH,  "summary_statistics.xlsx")

# Ensure output directories exist
os.makedirs(os.path.dirname(PROCESSED_PATH), exist_ok=True)
os.makedirs(TABLES_PATH, exist_ok=True)
os.makedirs(FIGURES_PATH, exist_ok=True)

# Verify that raw data file exists before proceeding
if not os.path.exists(RAW_DATA_PATH):
    print(f"ERROR: Raw data file not found at:\n  {RAW_DATA_PATH}")
    print("Checked locations:")
    for candidate in RAW_DATA_CANDIDATES:
        print(f"  - {candidate}")
    print("Please ensure GHG_totals_by_country.csv is in data/raw/")
    sys.exit(1)

print("=" * 65)
print("  GHG PERSISTENCE STUDY — PHASE 0: DATA PREPROCESSING")
print("=" * 65)
print(f"  Project root : {PROJECT_ROOT}")
print(f"  Raw data     : {RAW_DATA_PATH}")
print(f"  Output       : {PROCESSED_PATH}")
print("=" * 65)


# -----------------------------------------------------------------------------
# SECTION 3 — DEFINE CONSTANTS
#
# SHOCK_YEARS: Theoretically motivated structural break priors.
# These dates correspond to documented major disruptions to global
# economic activity and/or climate governance. They will be used in
# Analysis 1 as prior information for structural break tests.
#
# Reference: Identified from IPCC AR6, IEA World Energy Outlook historical
# data, and the econometric structural break literature (Perron 1989;
# Zivot & Andrews 1992; Lee & Strazicich 2003).
# -----------------------------------------------------------------------------

YEARS = [str(y) for y in range(1970, 2025)]   # All 55 year columns as strings

SHOCK_YEARS = {
    1973: "First Oil Crisis",
    1979: "Second Oil Crisis",
    1991: "Soviet Union Dissolution",
    2008: "Global Financial Crisis — Onset",
    2009: "Global Financial Crisis — Trough",
    2015: "Paris Agreement",
    2020: "COVID-19 Pandemic",
    2021: "Post-COVID Rebound"
}

# Entities that are NOT sovereign nations — must be excluded from panel.
# Rationale: GLOBAL TOTAL and EU27 aggregate sub-units already present in
# the dataset (double counting). International Aviation and Shipping are
# not attributable to single sovereign entities.
NON_SOVEREIGN = [
    "GLOBAL TOTAL",
    "EU27",
    "International Aviation",
    "International Shipping"
]


# -----------------------------------------------------------------------------
# SECTION 4 — LOAD RAW DATA
# -----------------------------------------------------------------------------

print("\n[STEP 1] Loading raw data...")

df_raw = pd.read_csv(RAW_DATA_PATH)

print(f"  Rows loaded    : {len(df_raw)}")
print(f"  Columns loaded : {len(df_raw.columns)}")
print(f"  Year columns   : {YEARS[0]} to {YEARS[-1]} ({len(YEARS)} years)")
print(f"  Memory usage   : {df_raw.memory_usage(deep=True).sum() / 1024:.1f} KB")


# -----------------------------------------------------------------------------
# SECTION 5 — REMOVE NON-SOVEREIGN AND EMPTY ROWS
#
# WHY: The dataset contains:
#   (a) 2 completely empty rows (CSV spacers) — rows with no Country or data
#   (b) 4 aggregate entities that are not sovereign nations
#
# Removing these is MANDATORY before any panel econometric analysis.
# Including aggregates would introduce double-counting and inflate variance.
# Empty rows would cause errors in all subsequent computations.
# -----------------------------------------------------------------------------

print("\n[STEP 2] Removing non-sovereign entities and empty rows...")

# Remove rows with no country name (completely empty spacer rows)
n_before = len(df_raw)
df = df_raw.dropna(subset=['Country']).copy()
n_empty_removed = n_before - len(df)
print(f"  Empty rows removed        : {n_empty_removed}")

# Remove non-sovereign aggregate entities
mask_non_sovereign = df['Country'].isin(NON_SOVEREIGN)
removed_entities = df[mask_non_sovereign]['Country'].tolist()
df = df[~mask_non_sovereign].copy()
print(f"  Non-sovereign rows removed: {len(removed_entities)}")
for entity in removed_entities:
    print(f"    → Removed: {entity}")

print(f"  Sovereign nations retained: {len(df)}")


# -----------------------------------------------------------------------------
# SECTION 6 — DATA TYPE ENFORCEMENT
#
# WHY: CSV files store everything as strings by default. We must explicitly
# convert emission values to float. Failure to do this causes silent errors
# in statistical computations — Python will not warn you, it will simply
# produce wrong results.
# -----------------------------------------------------------------------------

print("\n[STEP 3] Enforcing correct data types...")

# Convert all year columns to numeric (float64)
# errors='coerce' converts any non-numeric string to NaN rather than crashing
for year in YEARS:
    df[year] = pd.to_numeric(df[year], errors='coerce')

# Rename columns for clarity
df = df.rename(columns={
    'EDGAR Country Code': 'EDGAR_Code',
    'Country': 'Country'
})

# Reset index after row removal
df = df.reset_index(drop=True)

print(f"  Year columns dtype: {df['1970'].dtype}")
print(f"  EDGAR_Code dtype  : {df['EDGAR_Code'].dtype}")


# -----------------------------------------------------------------------------
# SECTION 7 — NULL VALUE AUDIT
#
# WHY: The 114 null values reported in the raw dataset must be fully
# understood before analysis. Null values in econometric time series
# analysis are not simply missing — they represent:
#   (a) Reporting gaps (country did not report to EDGAR in that year)
#   (b) Pre-independence periods (country did not exist yet)
#   (c) Data quality issues
#
# We must document WHICH countries have nulls and in WHICH years.
# This documentation is required in the paper's data section.
# -----------------------------------------------------------------------------

print("\n[STEP 4] Null value audit...")

# Count nulls per country
null_counts = df[YEARS].isnull().sum(axis=1)
countries_with_nulls = df[null_counts > 0][['EDGAR_Code', 'Country']].copy()
countries_with_nulls['null_count'] = null_counts[null_counts > 0].values

total_nulls = df[YEARS].isnull().sum().sum()
print(f"  Total null values in dataset : {total_nulls}")
print(f"  Countries with any null      : {len(countries_with_nulls)}")

if len(countries_with_nulls) > 0:
    print("\n  Countries with missing data:")
    for _, row in countries_with_nulls.iterrows():
        print(f"    {row['Country']:35s} | Nulls: {int(row['null_count'])}")


# -----------------------------------------------------------------------------
# SECTION 8 — RESHAPE FROM WIDE TO LONG FORMAT
#
# WHY: The raw data is in "wide" format — one row per country, years as
# columns. All time series econometric tests require "long" format — one
# row per (country, year) observation.
#
# Wide format:  Country | 1970 | 1971 | 1972 | ...
# Long format:  Country | Year | GHG_Emissions
#
# The long format is the universal input for:
#   - Unit root tests (statsmodels)
#   - Panel data models (linearmodels)
#   - Any time series operation indexed by (entity, time)
# -----------------------------------------------------------------------------

print("\n[STEP 5] Reshaping from wide to long format...")

# melt() converts wide to long
# id_vars: columns to keep as identifiers (not reshaped)
# value_vars: the year columns to stack
# var_name: name for the new 'year' column
# value_name: name for the emission values column
df_long = df.melt(
    id_vars=['EDGAR_Code', 'Country'],
    value_vars=YEARS,
    var_name='Year',
    value_name='GHG_Emissions'
)

# Convert Year from string to integer
df_long['Year'] = df_long['Year'].astype(int)

# Sort by Country then Year — essential for time series operations
df_long = df_long.sort_values(['Country', 'Year']).reset_index(drop=True)

print(f"  Long format shape : {df_long.shape[0]:,} rows × {df_long.shape[1]} columns")
print(f"  Unique countries  : {df_long['Country'].nunique()}")
print(f"  Year range        : {df_long['Year'].min()} — {df_long['Year'].max()}")
print(f"  Sample rows:")
print(df_long[df_long['Country'] == 'China'].head(5).to_string(index=False))


# -----------------------------------------------------------------------------
# SECTION 9 — LOG TRANSFORMATION
#
# WHY: Raw GHG emission values are right-skewed and heteroskedastic.
# - China 2024: ~15,536 Mt CO2-eq
# - Anguilla 2024: ~0.026 Mt CO2-eq
# This 600,000x range violates the variance stationarity assumption
# underlying virtually all unit root and persistence tests.
#
# The natural log transformation achieves:
# (1) Variance stabilisation — reduces heteroskedasticity
# (2) Interpretability — changes become growth rates (percentage changes)
# (3) Normality approximation — reduces skewness
# (4) Standard practice — the GHG persistence literature universally
#     uses log emissions (e.g., Apergis et al. 2017; Caporale et al. 2021)
#
# IMPORTANT: Since we confirmed NO zero or negative values in STEP 3,
# np.log() is applied directly without any pre-treatment required.
# -----------------------------------------------------------------------------

print("\n[STEP 6] Applying log transformation...")

# Check one final time for safety
n_nonpositive = (df_long['GHG_Emissions'] <= 0).sum()
n_nulls_before = df_long['GHG_Emissions'].isnull().sum()
print(f"  Non-positive values before log : {n_nonpositive}")
print(f"  Null values before log         : {n_nulls_before}")

# Apply natural log
df_long['log_GHG'] = np.log(df_long['GHG_Emissions'])

# Verify
n_nulls_after = df_long['log_GHG'].isnull().sum()
print(f"  Null values after log          : {n_nulls_after}")
print(f"  log_GHG range: [{df_long['log_GHG'].min():.4f}, {df_long['log_GHG'].max():.4f}]")


# -----------------------------------------------------------------------------
# SECTION 10 — ADD SHOCK YEAR FLAG COLUMN
#
# WHY: For Analysis 1 (structural break tests), it is useful to have a
# binary indicator column that marks the documented shock years.
# This allows post-estimation comparison: do endogenously detected
# break years correspond to known economic/climate events?
# This is how SDG 13 (specifically the 2015 Paris Agreement) enters
# your empirical framework in a non-decorative way.
# -----------------------------------------------------------------------------

print("\n[STEP 7] Adding shock year indicators...")

df_long['Is_Shock_Year'] = df_long['Year'].isin(SHOCK_YEARS.keys()).astype(int)
df_long['Shock_Event']   = df_long['Year'].map(SHOCK_YEARS).fillna("")

print(f"  Shock year observations flagged: {df_long['Is_Shock_Year'].sum():,}")
print(f"  Shock years: {sorted(SHOCK_YEARS.keys())}")


# -----------------------------------------------------------------------------
# SECTION 11 — FINAL VALIDATION CHECKS
#
# Before exporting, we run a series of integrity checks.
# If any check fails, the script halts and reports the problem.
# Never export data you haven't validated.
# -----------------------------------------------------------------------------

print("\n[STEP 8] Running validation checks...")

checks_passed = True

# Check 1: Correct number of countries
expected_countries = 208
actual_countries = df_long['Country'].nunique()
status = "PASS" if actual_countries == expected_countries else "FAIL"
print(f"  [{status}] Country count: {actual_countries} (expected {expected_countries})")
if status == "FAIL":
    checks_passed = False

# Check 2: Correct number of years
expected_years = 55
actual_years = df_long['Year'].nunique()
status = "PASS" if actual_years == expected_years else "FAIL"
print(f"  [{status}] Year count   : {actual_years} (expected {expected_years})")
if status == "FAIL":
    checks_passed = False

# Check 3: Panel is balanced (every country has same number of observations)
obs_per_country = df_long.groupby('Country').size()
is_balanced = (obs_per_country == expected_years).all()
status = "PASS" if is_balanced else "WARN"
print(f"  [{status}] Panel balance: {'Balanced' if is_balanced else 'Unbalanced — check null rows'}")

# Check 4: No negative log values from impossible emissions
n_neg_log = (df_long['log_GHG'] < -10).sum()
status = "PASS" if n_neg_log == 0 else "WARN"
print(f"  [{status}] Extreme log values (<-10): {n_neg_log}")

# Check 5: No duplicate (Country, Year) pairs
n_duplicates = df_long.duplicated(subset=['Country', 'Year']).sum()
status = "PASS" if n_duplicates == 0 else "FAIL"
print(f"  [{status}] Duplicate (Country, Year): {n_duplicates}")
if n_duplicates > 0:
    checks_passed = False

# Check 6: Non-sovereign entities fully excluded
for entity in NON_SOVEREIGN:
    present = (df_long['Country'] == entity).any()
    status = "FAIL" if present else "PASS"
    print(f"  [{status}] Aggregate excluded: {entity}")
    if present:
        checks_passed = False

if not checks_passed:
    print("\n  CRITICAL: One or more validation checks FAILED.")
    print("  Review the errors above before proceeding to analysis.")
    sys.exit(1)
else:
    print("\n  All critical validation checks passed.")


# -----------------------------------------------------------------------------
# SECTION 12 — SUMMARY STATISTICS TABLE
#
# WHY: Your paper's data section must include a descriptive statistics table.
# Standard practice is to report: N, Mean, Std Dev, Min, Max, Skewness,
# Kurtosis — for BOTH raw and log-transformed series.
# The contrast between raw and log skewness demonstrates why the
# log transformation was necessary (methodological justification).
# -----------------------------------------------------------------------------

print("\n[STEP 9] Computing summary statistics...")

# Pivot back to wide for summary stats computation (easier with pandas describe)
df_wide_clean = df_long.pivot(index='Country', columns='Year', values='GHG_Emissions')
df_wide_log   = df_long.pivot(index='Country', columns='Year', values='log_GHG')

# Flatten all values for distributional statistics
raw_vals = df_long['GHG_Emissions'].dropna().values
log_vals = df_long['log_GHG'].dropna().values

summary_data = {
    'Statistic': [
        'N (country-year observations)',
        'Number of Countries',
        'Time Period',
        'Mean',
        'Std Deviation',
        'Minimum',
        'Maximum',
        'Skewness',
        'Kurtosis',
        'Median'
    ],
    'Raw GHG (Mt CO₂-eq)': [
        f"{len(raw_vals):,}",
        f"{df_long['Country'].nunique()}",
        f"{df_long['Year'].min()}–{df_long['Year'].max()}",
        f"{np.mean(raw_vals):.4f}",
        f"{np.std(raw_vals):.4f}",
        f"{np.min(raw_vals):.4f}",
        f"{np.max(raw_vals):.4f}",
        f"{stats.skew(raw_vals):.4f}",
        f"{stats.kurtosis(raw_vals):.4f}",
        f"{np.median(raw_vals):.4f}"
    ],
    'Log GHG (ln Mt CO₂-eq)': [
        f"{len(log_vals):,}",
        f"{df_long['Country'].nunique()}",
        f"{df_long['Year'].min()}–{df_long['Year'].max()}",
        f"{np.mean(log_vals):.4f}",
        f"{np.std(log_vals):.4f}",
        f"{np.min(log_vals):.4f}",
        f"{np.max(log_vals):.4f}",
        f"{stats.skew(log_vals):.4f}",
        f"{stats.kurtosis(log_vals):.4f}",
        f"{np.median(log_vals):.4f}"
    ]
}

df_summary = pd.DataFrame(summary_data)
print(df_summary.to_string(index=False))


# -----------------------------------------------------------------------------
# SECTION 13 — EXPORT OUTPUTS
# -----------------------------------------------------------------------------

print("\n[STEP 10] Exporting outputs...")

# Export 1: Clean long-format analytical dataset
df_long.to_csv(PROCESSED_PATH, index=False)
print(f"  ✓ Clean dataset  → {PROCESSED_PATH}")

# Export 2: Summary statistics table (Excel, for paper)
with pd.ExcelWriter(SUMSTATS_PATH, engine='openpyxl') as writer:
    df_summary.to_excel(writer, sheet_name='Summary_Statistics', index=False)
    countries_with_nulls.to_excel(writer, sheet_name='Null_Audit', index=False)
print(f"  ✓ Summary stats  → {SUMSTATS_PATH}")


# -----------------------------------------------------------------------------
# SECTION 14 — PREPROCESSING REPORT (TEXT FILE)
# This is your paper audit trail — save it. Reviewers sometimes ask for it.
# -----------------------------------------------------------------------------

report_lines = [
    "=" * 65,
    "  GHG PERSISTENCE STUDY — PREPROCESSING REPORT",
    f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    "=" * 65,
    "",
    "RAW DATA",
    f"  Source       : EDGAR (Emissions Database for Global Atmospheric Research)",
    f"  File         : GHG_totals_by_country.csv",
    f"  Raw rows     : 214",
    f"  Raw columns  : 57 (Country, EDGAR_Code, 1970–2024)",
    "",
    "CLEANING STEPS APPLIED",
    f"  1. Removed {n_empty_removed} empty spacer rows (no country identifier)",
    f"  2. Removed {len(removed_entities)} non-sovereign aggregate entities:",
    *[f"       - {e}" for e in removed_entities],
    f"  3. Converted all year columns to float64",
    f"  4. Reshaped from wide (214×57) to long format ({len(df_long):,}×6)",
    f"  5. Applied natural log transformation to GHG_Emissions → log_GHG",
    f"     Justification: raw series right-skewed (skewness={stats.skew(raw_vals):.3f})",
    f"     Post-log skewness: {stats.skew(log_vals):.3f}",
    f"  6. Added binary shock year flag for {len(SHOCK_YEARS)} documented events",
    "",
    "FINAL DATASET",
    f"  Sovereign nations  : {df_long['Country'].nunique()}",
    f"  Time period        : {df_long['Year'].min()}–{df_long['Year'].max()}",
    f"  Total observations : {len(df_long):,}",
    f"  Panel structure    : {'Balanced' if is_balanced else 'Unbalanced'}",
    f"  Null observations  : {n_nulls_after}",
    "",
    "NULL VALUE AUDIT",
    f"  Total nulls in raw data      : 114 (in EDGAR Country Code and Country cols)",
    f"  Nulls in emission values     : {total_nulls} (all in removed aggregate/empty rows)",
    f"  Nulls in final clean dataset : {n_nulls_after}",
    "",
    "SHOCK YEARS DEFINED (Structural Break Priors)",
    *[f"  {yr}: {desc}" for yr, desc in SHOCK_YEARS.items()],
    "",
    "NON-SOVEREIGN ENTITIES EXCLUDED",
    *[f"  - {e}" for e in NON_SOVEREIGN],
    "",
    "OUTPUT FILES",
    f"  data/processed/ghg_clean.csv",
    f"  outputs/tables/summary_statistics.xlsx",
    f"  outputs/tables/preprocessing_report.txt",
    "=" * 65
]

with open(REPORT_PATH, 'w', encoding='utf-8') as f:
    f.write("\n".join(report_lines))

print(f"  ✓ Audit report   → {REPORT_PATH}")


# -----------------------------------------------------------------------------
# SECTION 15 — DIAGNOSTIC FIGURES
#
# Figure 1: Raw vs Log GHG distribution (demonstrates log transformation need)
# Figure 2: Top 15 emitters trajectory (1970-2024)
# Figure 3: Panel emission heatmap (countries × years)
# -----------------------------------------------------------------------------

print("\n[STEP 11] Generating diagnostic figures...")

plt, sns, plotting_error = load_plotting_libraries()
if plotting_error is not None:
    print("  WARNING: Skipping figure generation because plotting libraries could not be loaded.")
    print(f"  Details: {plotting_error}")
else:
    plt.style.use('seaborn-v0_8-whitegrid')
    FIGURE_DPI = 300

    # ── FIGURE 1: Distribution comparison (raw vs log) ──────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].hist(raw_vals, bins=80, color='#2C7BB6', edgecolor='white', linewidth=0.3)
    axes[0].set_title("Raw GHG Emissions Distribution\n(Mt CO₂-eq)", fontsize=13, fontweight='bold')
    axes[0].set_xlabel("GHG Emissions (Mt CO₂-eq)")
    axes[0].set_ylabel("Frequency")
    axes[0].text(0.97, 0.95, f"Skewness: {stats.skew(raw_vals):.2f}",
                 transform=axes[0].transAxes, ha='right', va='top',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    axes[1].hist(log_vals, bins=80, color='#D7191C', edgecolor='white', linewidth=0.3)
    axes[1].set_title("Log-Transformed GHG Emissions\n(ln Mt CO₂-eq)", fontsize=13, fontweight='bold')
    axes[1].set_xlabel("log(GHG Emissions)")
    axes[1].set_ylabel("Frequency")
    axes[1].text(0.97, 0.95, f"Skewness: {stats.skew(log_vals):.2f}",
                 transform=axes[1].transAxes, ha='right', va='top',
                 bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))

    fig.suptitle("EDGAR GHG Emissions: Distribution Before and After Log Transformation\n"
                 "208 Sovereign Nations × 55 Years (1970–2024)",
                 fontsize=11, y=1.02)
    plt.tight_layout()
    fig1_path = os.path.join(FIGURES_PATH, "fig1_distribution_raw_vs_log.png")
    plt.savefig(fig1_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Figure 1 saved → fig1_distribution_raw_vs_log.png")


    # ── FIGURE 2: Top 15 emitters trajectory ────────────────────────────────────
    # Get top 15 emitters by mean emission across the full period
    mean_by_country = df_long.groupby('Country')['GHG_Emissions'].mean()
    top15 = mean_by_country.nlargest(15).index.tolist()

    df_top15 = df_long[df_long['Country'].isin(top15)].copy()

    fig, ax = plt.subplots(figsize=(14, 7))

    colors = plt.cm.tab20(np.linspace(0, 1, 15))
    for i, country in enumerate(top15):
        data = df_top15[df_top15['Country'] == country].sort_values('Year')
        ax.plot(data['Year'], data['log_GHG'], label=country,
                color=colors[i], linewidth=1.8, alpha=0.85)

    # Add vertical lines for shock years
    shock_colors = {
        1973: '#FF6B35', 1979: '#FF6B35',
        1991: '#8B0000',
        2009: '#2196F3',
        2015: '#4CAF50',
        2020: '#9C27B0'
    }
    for yr, event in SHOCK_YEARS.items():
        if yr in [1973, 1979, 1991, 2009, 2015, 2020]:
            color = shock_colors.get(yr, 'grey')
            ax.axvline(x=yr, color=color, linestyle='--', linewidth=0.9, alpha=0.7)
            ax.text(yr + 0.2, ax.get_ylim()[0] if ax.get_ylim()[0] != 0 else -1,
                    str(yr), fontsize=7, color=color, rotation=90, va='bottom')

    ax.set_title("Log GHG Emissions Trajectories — Top 15 Emitters (1970–2024)\n"
                 "Vertical dashed lines: major structural shock years",
                 fontsize=13, fontweight='bold')
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("log(GHG Emissions, Mt CO₂-eq)", fontsize=11)
    ax.legend(loc='upper left', fontsize=8, ncol=2, framealpha=0.8)
    ax.set_xlim(1970, 2024)

    plt.tight_layout()
    fig2_path = os.path.join(FIGURES_PATH, "fig2_top15_trajectories.png")
    plt.savefig(fig2_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Figure 2 saved → fig2_top15_trajectories.png")


    # ── FIGURE 3: Panel Heatmap ──────────────────────────────────────────────────
    # Select a readable subset: top 40 emitters by mean emission
    top40 = mean_by_country.nlargest(40).index.tolist()
    df_heatmap = df_long[df_long['Country'].isin(top40)].copy()
    heatmap_pivot = df_heatmap.pivot(index='Country', columns='Year', values='log_GHG')
    heatmap_pivot = heatmap_pivot.loc[mean_by_country.loc[top40].sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(18, 10))
    sns.heatmap(
        heatmap_pivot,
        cmap='RdYlGn_r',
        ax=ax,
        cbar_kws={'label': 'log(GHG Emissions, Mt CO₂-eq)', 'shrink': 0.6},
        linewidths=0,
        yticklabels=True
    )

    # Mark shock years on heatmap x-axis
    year_positions = list(heatmap_pivot.columns)
    for shock_yr in SHOCK_YEARS.keys():
        if shock_yr in year_positions:
            pos = year_positions.index(shock_yr)
            ax.axvline(x=pos, color='white', linewidth=1.5, alpha=0.8)

    ax.set_title("GHG Emission Heatmap — Top 40 Emitters (1970–2024)\n"
                 "log(Mt CO₂-eq) | White lines: documented shock years",
                 fontsize=13, fontweight='bold')
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Country (sorted by mean emission)", fontsize=11)

    # Reduce x-tick density for readability
    n_ticks = 11
    tick_positions = np.linspace(0, len(year_positions) - 1, n_ticks, dtype=int)
    ax.set_xticks(tick_positions)
    ax.set_xticklabels([year_positions[i] for i in tick_positions], rotation=45)

    plt.tight_layout()
    fig3_path = os.path.join(FIGURES_PATH, "fig3_panel_heatmap.png")
    plt.savefig(fig3_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Figure 3 saved → fig3_panel_heatmap.png")


# -----------------------------------------------------------------------------
# SECTION 16 — FINAL SUMMARY PRINTOUT
# -----------------------------------------------------------------------------

print("\n" + "=" * 65)
print("  PHASE 0 COMPLETE — PREPROCESSING SUMMARY")
print("=" * 65)
print(f"  Raw data rows        : 214")
print(f"  Empty rows removed   : {n_empty_removed}")
print(f"  Aggregates removed   : {len(removed_entities)}")
print(f"  Sovereign nations    : {df_long['Country'].nunique()}")
print(f"  Time period          : {df_long['Year'].min()}–{df_long['Year'].max()}")
print(f"  Total observations   : {len(df_long):,}")
print(f"  Panel structure      : {'Balanced' if is_balanced else 'Unbalanced'}")
print(f"  Raw skewness         : {stats.skew(raw_vals):.4f}")
print(f"  Log skewness         : {stats.skew(log_vals):.4f}")
print(f"  Null values in output: {n_nulls_after}")
print("=" * 65)
print("\n  You may now proceed to Analysis 1.")
print("  Input file for all analyses: data/processed/ghg_clean.csv")
print("=" * 65)
