# =============================================================================
# PHASE 0 — DATA PREPROCESSING
# Project : GHG Persistence Study
# Script  : preprocessing.py
#
# Purpose : Load raw EDGAR GHG data and produce a clean, analysis-ready
#           panel dataset. This script must be run FIRST before any analysis.
#
# Methodology: Section 2.3 — Four sequential preprocessing steps:
#   Step 1: Remove 2 empty spacer rows
#   Step 2: Extract GLOBAL TOTAL 2024, then exclude 4 aggregate entities
#   Step 3: Convert year columns to float64
#   Step 4: Verify panel balance (208 rows × 57 columns, no missing values)
#
# Input   : data/raw/GHG_totals_by_country.csv
# Output  : data/processed/Processed_GHG_totals_by_country.csv
#           outputs/tables/summary_statistics.xlsx
#           outputs/tables/preprocessing_report.txt
# =============================================================================


# -----------------------------------------------------------------------------
# SECTION 1 — LIBRARY IMPORTS
# -----------------------------------------------------------------------------

import pandas as pd
import numpy as np
import os
import sys
from scipy import stats
from datetime import datetime


# -----------------------------------------------------------------------------
# SECTION 2 — PROJECT PATH CONFIGURATION
# Detects the project root by going one level up from /scripts/
# -----------------------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_DATA_CANDIDATES = [
    os.path.join(PROJECT_ROOT, "data", "raw", "GHG_totals_by_country.csv"),
    os.path.join(PROJECT_ROOT, "GHG_totals_by_country.csv"),
    os.path.join(os.getcwd(), "GHG_Persistence_Study", "data", "raw", "GHG_totals_by_country.csv"),
    os.path.join(os.getcwd(), "GHG_Persistence_Study", "GHG_totals_by_country.csv"),
]

RAW_DATA_PATH = next((p for p in RAW_DATA_CANDIDATES if os.path.exists(p)), RAW_DATA_CANDIDATES[0])

PROCESSED_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "Processed_GHG_totals_by_country.csv")
TABLES_PATH    = os.path.join(PROJECT_ROOT, "outputs", "tables")
REPORT_PATH    = os.path.join(TABLES_PATH,  "preprocessing_report.txt")
SUMSTATS_PATH  = os.path.join(TABLES_PATH,  "summary_statistics.xlsx")

os.makedirs(os.path.dirname(PROCESSED_PATH), exist_ok=True)
os.makedirs(TABLES_PATH, exist_ok=True)

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
# SECTION 3 — CONSTANTS
# -----------------------------------------------------------------------------

YEARS = [str(y) for y in range(1970, 2025)]   # All 55 year columns as strings

# Entities that are NOT sovereign nations — excluded from panel per Section 2.3.
# GLOBAL TOTAL and EU27 aggregate sub-units already present in the dataset
# (double-counting). International Aviation and Shipping lack territorial attribution.
NON_SOVEREIGN = [
    "GLOBAL TOTAL",
    "EU27",
    "International Aviation",
    "International Shipping"
]


# -----------------------------------------------------------------------------
# SECTION 4 — LOAD RAW DATA
# -----------------------------------------------------------------------------

print("\n[STEP 0] Loading raw data...")

df_raw = pd.read_csv(RAW_DATA_PATH)

print(f"  Rows loaded    : {len(df_raw)}")
print(f"  Columns loaded : {len(df_raw.columns)}")
print(f"  Year columns   : {YEARS[0]} to {YEARS[-1]} ({len(YEARS)} years)")


# -----------------------------------------------------------------------------
# SECTION 5 — STEP 1: REMOVE EMPTY SPACER ROWS
#
# WHY: The raw CSV contains 2 completely empty rows (CSV spacers) with no
# Country identifier. These cause errors in all subsequent computations.
# -----------------------------------------------------------------------------

print("\n[STEP 1] Removing empty spacer rows...")

n_before = len(df_raw)
df = df_raw.dropna(subset=['Country']).copy()
n_empty_removed = n_before - len(df)
print(f"  Empty rows removed : {n_empty_removed}")


# -----------------------------------------------------------------------------
# SECTION 6 — STEP 2: EXTRACT GLOBAL TOTAL 2024, THEN EXCLUDE AGGREGATES
#
# WHY: The GLOBAL TOTAL 2024 value is extracted before exclusion because it
# serves as the reference denominator for all emission coverage calculations
# in Sensitivity Analysis II (Section 2.8). Once extracted, all 4 aggregate
# entities are removed to prevent double-counting in the sovereign panel.
# -----------------------------------------------------------------------------

print("\n[STEP 2] Extracting GLOBAL TOTAL 2024 and excluding aggregate entities...")

# Extract GLOBAL TOTAL 2024 before any rows are removed
global_total_row = df[df['Country'] == 'GLOBAL TOTAL']
if len(global_total_row) == 1:
    GLOBAL_TOTAL_2024 = pd.to_numeric(global_total_row['2024'].values[0], errors='coerce')
    print(f"  GLOBAL TOTAL 2024 extracted : {GLOBAL_TOTAL_2024:,.1f} Mt CO2-eq")
else:
    GLOBAL_TOTAL_2024 = 53206.4   # EDGAR fallback value
    print(f"  WARNING: GLOBAL TOTAL row not found; using fallback: {GLOBAL_TOTAL_2024:,.1f} Mt CO2-eq")

# Exclude non-sovereign aggregate entities
mask_non_sovereign = df['Country'].isin(NON_SOVEREIGN)
removed_entities = df[mask_non_sovereign]['Country'].tolist()
df = df[~mask_non_sovereign].copy()
print(f"  Aggregate entities removed  : {len(removed_entities)}")
for entity in removed_entities:
    print(f"    → Removed: {entity}")
print(f"  Sovereign nations retained  : {len(df)}")


# -----------------------------------------------------------------------------
# SECTION 7 — STEP 3: DATA TYPE ENFORCEMENT
#
# WHY: CSV files store all values as strings by default. Year-column values
# must be explicitly cast to float64 before any numerical computation.
# errors='coerce' converts non-numeric strings to NaN rather than crashing.
# -----------------------------------------------------------------------------

print("\n[STEP 3] Converting year columns to float64...")

for year in YEARS:
    df[year] = pd.to_numeric(df[year], errors='coerce')

df = df.rename(columns={'EDGAR Country Code': 'EDGAR_Code'})
df = df.reset_index(drop=True)

# Reorder columns: Country, EDGAR_Code, then year columns
df = df[['Country', 'EDGAR_Code'] + YEARS]

print(f"  Year columns dtype : {df['1970'].dtype}")
print(f"  EDGAR_Code dtype   : {df['EDGAR_Code'].dtype}")
print(f"  Dataset shape      : {df.shape[0]} rows × {df.shape[1]} columns")


# -----------------------------------------------------------------------------
# SECTION 8 — STEP 4: PANEL BALANCE VERIFICATION
#
# WHY: Before exporting, confirm the dataset is exactly balanced —
# 208 sovereign nations × 57 columns (Country, EDGAR_Code, 1970-2024)
# with no missing values in any year column.
# -----------------------------------------------------------------------------

print("\n[STEP 4] Verifying panel balance...")

checks_passed = True

# Check 1: Row count (sovereign nations)
expected_countries = 208
actual_countries = len(df)
status = "PASS" if actual_countries == expected_countries else "FAIL"
print(f"  [{status}] Row count (countries) : {actual_countries} (expected {expected_countries})")
if status == "FAIL":
    checks_passed = False

# Check 2: Year column count
expected_years = 55
actual_year_cols = len(YEARS)
status = "PASS" if actual_year_cols == expected_years else "FAIL"
print(f"  [{status}] Year columns          : {actual_year_cols} (expected {expected_years})")
if status == "FAIL":
    checks_passed = False

# Check 3: No missing values in any year column
n_nulls = df[YEARS].isnull().sum().sum()
status = "PASS" if n_nulls == 0 else "FAIL"
print(f"  [{status}] Missing values        : {n_nulls}")
if n_nulls > 0:
    checks_passed = False

# Check 4: No duplicate country names
n_duplicates = df['Country'].duplicated().sum()
status = "PASS" if n_duplicates == 0 else "FAIL"
print(f"  [{status}] Duplicate countries   : {n_duplicates}")
if n_duplicates > 0:
    checks_passed = False

# Check 5: Non-sovereign entities fully excluded
for entity in NON_SOVEREIGN:
    present = (df['Country'] == entity).any()
    status = "FAIL" if present else "PASS"
    print(f"  [{status}] Aggregate excluded   : {entity}")
    if present:
        checks_passed = False

if not checks_passed:
    print("\n  CRITICAL: One or more validation checks FAILED. Review above and rerun.")
    sys.exit(1)
else:
    print("\n  All validation checks passed.")


# -----------------------------------------------------------------------------
# SECTION 9 — SUMMARY STATISTICS
# Descriptive statistics for the paper's data section (raw GHG_Emissions).
# -----------------------------------------------------------------------------

print("\n[Summary] Computing descriptive statistics...")

# Flatten all year-column values for distributional statistics
raw_vals = df[YEARS].values.flatten()
raw_vals = raw_vals[~np.isnan(raw_vals)]

n_obs = actual_countries * actual_year_cols

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
    'GHG Emissions (Mt CO₂-eq)': [
        f"{n_obs:,}",
        f"{actual_countries}",
        f"1970–2024",
        f"{np.mean(raw_vals):.4f}",
        f"{np.std(raw_vals):.4f}",
        f"{np.min(raw_vals):.4f}",
        f"{np.max(raw_vals):.4f}",
        f"{stats.skew(raw_vals):.4f}",
        f"{stats.kurtosis(raw_vals):.4f}",
        f"{np.median(raw_vals):.4f}"
    ]
}

df_summary = pd.DataFrame(summary_data)
print(df_summary.to_string(index=False))


# -----------------------------------------------------------------------------
# SECTION 10 — EXPORT OUTPUTS
# -----------------------------------------------------------------------------

print("\n[Export] Saving outputs...")

# Export clean wide-format dataset (208 rows × 57 columns)
df.to_csv(PROCESSED_PATH, index=False)
print(f"  ✓ Clean dataset  → {PROCESSED_PATH}")

# Export summary statistics table
with pd.ExcelWriter(SUMSTATS_PATH, engine='openpyxl') as writer:
    df_summary.to_excel(writer, sheet_name='Summary_Statistics', index=False)
print(f"  ✓ Summary stats  → {SUMSTATS_PATH}")


# -----------------------------------------------------------------------------
# SECTION 11 — PREPROCESSING REPORT (audit trail)
# -----------------------------------------------------------------------------

report_lines = [
    "=" * 65,
    "  GHG PERSISTENCE STUDY — PREPROCESSING REPORT",
    f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    "=" * 65,
    "",
    "RAW DATA",
    "  Source  : EDGAR (Emissions Database for Global Atmospheric Research)",
    "  File    : GHG_totals_by_country.csv",
    "  Entities: 214",
    "  Columns : 57 (Country, EDGAR_Code, 1970-2024)",
    "",
    "PREPROCESSING STEPS (Section 2.3)",
    f"  Step 1: Removed {n_empty_removed} empty spacer rows",
    f"  Step 2: Extracted GLOBAL TOTAL 2024 = {GLOBAL_TOTAL_2024:,.1f} Mt CO2-eq",
    f"          Excluded {len(removed_entities)} aggregate entities:",
    *[f"            - {e}" for e in removed_entities],
    "  Step 3: Converted all year columns to float64",
    f"  Step 4: Panel balance verified",
    f"          {actual_countries} rows x {actual_year_cols} year columns",
    f"          Total country-year observations: {n_obs:,}",
    f"          Missing values in year columns: {n_nulls}",
    "",
    "REFERENCE VALUE",
    f"  GLOBAL TOTAL 2024 : {GLOBAL_TOTAL_2024:,.1f} Mt CO2-eq",
    "  (Reference denominator for Sensitivity Analysis II, Section 2.8)",
    "",
    "FINAL DATASET",
    "  File    : data/processed/Processed_GHG_totals_by_country.csv",
    "  Format  : Wide (one row per country)",
    f"  Rows    : {actual_countries} sovereign nations",
    f"  Columns : 57 (Country, EDGAR_Code, 1970-2024)",
    f"  Obs     : {n_obs:,} country-year values",
    f"  Missing : {n_nulls}",
    "=" * 65
]

with open(REPORT_PATH, 'w', encoding='utf-8') as f:
    f.write("\n".join(report_lines))
print(f"  ✓ Audit report   → {REPORT_PATH}")


# -----------------------------------------------------------------------------
# SECTION 12 — FINAL SUMMARY
# -----------------------------------------------------------------------------

print("\n" + "=" * 65)
print("  PHASE 0 COMPLETE — PREPROCESSING SUMMARY")
print("=" * 65)
print(f"  Raw entities         : 214")
print(f"  Empty rows removed   : {n_empty_removed}")
print(f"  Aggregates removed   : {len(removed_entities)}")
print(f"  GLOBAL TOTAL 2024    : {GLOBAL_TOTAL_2024:,.1f} Mt CO2-eq (retained as reference)")
print(f"  Sovereign nations    : {actual_countries}")
print(f"  Year columns         : {actual_year_cols} (1970-2024)")
print(f"  Output shape         : {actual_countries} rows × 57 columns")
print(f"  Missing values       : {n_nulls}")
print(f"  Format               : Wide")
print("=" * 65)
print("\n  You may now proceed to Analysis 1.")
print("  Input file for all analyses: data/processed/Processed_GHG_totals_by_country.csv")
print("=" * 65)
