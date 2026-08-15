"""
Sensitivity Analysis — Alternative Baselines
STOTEN-D-26-02898

Purpose:
    Tests classification robustness under three alternative baseline years
    (1990, 2000, 2015) using the same threshold framework as the primary
    analysis (1970-2024). Addresses Reviewer #2 Major Comment 6.

Primary classification thresholds (consistent with main analysis):
    Declining         : ChangePct < -10%
    Stable            : -10% <= ChangePct <= +10%
    Moderately Rising : +10% < ChangePct <= +100%
    Rapidly Rising    : ChangePct > +100%

Alternative baselines tested:
    1990-2024 (34-year window)
    2000-2024 (24-year window)
    2015-2024 (9-year window)

Inputs:
    - Processed_GHG_totals_by_country.csv
    - analysis1_trajectory_results.xlsx (Country_Classifications sheet)

Outputs:
    - Terminal: classification distribution per baseline
    - Sensitivity_Analysis_Alternative_Baselines.xlsx

Author: Pri / STOTEN revision — Major Comment 6
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

# Build slim dataset with all required years
years = ["1970", "1990", "2000", "2015", "2024"]
raw_slim = raw[["Country", "EDGAR_Code"] + years].copy()
raw_slim.columns = ["Country", "EDGAR_Code", "E_1970", "E_1990", "E_2000", "E_2015", "E_2024"]

df = results.merge(raw_slim, on="Country", how="left")
print(f"Countries loaded: {len(df)}")
print()

# ── 2. Classification function ────────────────────────────────────────────────

def classify(change_pct):
    if change_pct < -10:
        return "Declining"
    elif change_pct <= 10:
        return "Stable"
    elif change_pct <= 100:
        return "Moderately Rising"
    else:
        return "Rapidly Rising"

# ── 3. Compute classifications for each baseline ──────────────────────────────

cat_order = ["Declining", "Stable", "Moderately Rising", "Rapidly Rising"]

baselines = {
    "1970-2024 (Primary)": ("E_1970", "E_2024", 54),
    "1990-2024"          : ("E_1990", "E_2024", 34),
    "2000-2024"          : ("E_2000", "E_2024", 24),
    "2015-2024"          : ("E_2015", "E_2024",  9),
}

results_summary = {}

for label, (base_col, end_col, interval) in baselines.items():
    df[f"ChangePct_{label}"] = (
        (df[end_col] - df[base_col]) / df[base_col]
    ) * 100

    df[f"CAGR_{label}"] = (
        (df[end_col] / df[base_col]) ** (1 / interval) - 1
    ) * 100

    df[f"Class_{label}"] = df[f"ChangePct_{label}"].apply(classify)

    counts = df[f"Class_{label}"].value_counts()
    total = len(df)

    print(f"=== {label} ===")
    for cat in cat_order:
        n = counts.get(cat, 0)
        print(f"  {cat:20s}: {n:4d} ({n/total*100:.1f}%)")

    rr_n = counts.get("Rapidly Rising", 0)
    majority = "YES" if rr_n > total / 2 else "NO"
    print(f"  Rapidly Rising majority: {majority} ({rr_n}/{total} = {rr_n/total*100:.1f}%)")
    print()

    results_summary[label] = {cat: counts.get(cat, 0) for cat in cat_order}
    results_summary[label]["Rapidly Rising Majority"] = majority
    results_summary[label]["Rapidly Rising %"] = round(rr_n / total * 100, 1)

# ── 4. Cross-baseline comparison ─────────────────────────────────────────────

print("=" * 70)
print("CROSS-BASELINE COMPARISON: RAPIDLY RISING MAJORITY")
print("=" * 70)
for label, data in results_summary.items():
    print(f"{label:30s}: {data['Rapidly Rising']:3d} ({data['Rapidly Rising %']:.1f}%) — Majority: {data['Rapidly Rising Majority']}")

print()

# ── 5. Country-level reclassification ────────────────────────────────────────

print("=" * 70)
print("COUNTRIES RECLASSIFIED BETWEEN 1970 AND 1990 BASELINES")
print("=" * 70)

reclass_90 = df[df["Trajectory_Type"] != df["Class_1990-2024"]].copy()
print(f"Reclassified: {len(reclass_90)} of 208")
if len(reclass_90) > 0:
    for _, row in reclass_90.iterrows():
        print(f"  {row['Country']:35s}: {row['Trajectory_Type']} -> {row['Class_1990-2024']}")

print()

print("=" * 70)
print("COUNTRIES RECLASSIFIED BETWEEN 1970 AND 2000 BASELINES")
print("=" * 70)

reclass_00 = df[df["Trajectory_Type"] != df["Class_2000-2024"]].copy()
print(f"Reclassified: {len(reclass_00)} of 208")
if len(reclass_00) > 0:
    for _, row in reclass_00.iterrows():
        print(f"  {row['Country']:35s}: {row['Trajectory_Type']} -> {row['Class_2000-2024']}")

# ── 6. Save results ───────────────────────────────────────────────────────────

summary_df = pd.DataFrame(results_summary).T
summary_df.index.name = "Baseline"
summary_df = summary_df.reset_index()

country_df = df[[
    "Country", "EDGAR_Code", "Trajectory_Type",
    "Class_1990-2024", "Class_2000-2024", "Class_2015-2024",
    "ChangePct_1970-2024 (Primary)", "ChangePct_1990-2024",
    "ChangePct_2000-2024", "ChangePct_2015-2024"
]].copy()

country_df.columns = [
    "Country", "EDGAR_Code", "Class_1970-2024 (Primary)",
    "Class_1990-2024", "Class_2000-2024", "Class_2015-2024",
    "ChangePct_1970-2024", "ChangePct_1990-2024",
    "ChangePct_2000-2024", "ChangePct_2015-2024"
]

country_df["Stable_1970_1990"] = (
    country_df["Class_1970-2024 (Primary)"] == country_df["Class_1990-2024"]
)
country_df["Stable_1970_2000"] = (
    country_df["Class_1970-2024 (Primary)"] == country_df["Class_2000-2024"]
)

OUTPUT_PATH = os.path.join(TABLE_PATH, "Sensitivity_Analysis_Alternative_Baselines.xlsx")

with pd.ExcelWriter(
    OUTPUT_PATH, engine="openpyxl"
) as writer:
    summary_df.to_excel(writer, sheet_name="Summary", index=False)
    country_df.to_excel(writer, sheet_name="Country_Classifications", index=False)

print()
print(f"Results saved to: {OUTPUT_PATH}")
print("Sheets: Summary, Country_Classifications")
