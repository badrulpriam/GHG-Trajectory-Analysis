"""

Computes:
1. Emission-weighted mean CAGR per trajectory group (post-Paris 2015-2024)
2. Share of 2024 global emissions in each trajectory group
3. Contribution to absolute emission increase (1970-2024) by group

Inputs:
- GHG_totals_by_country.csv (EDGAR raw data)
- analysis1_trajectory_results.xlsx (Country_Classifications sheet)

Output:
- Printed table of all three metrics
- emission_weighted_results.xlsx

Author: Pri / STOTEN revision
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ── 1. Load data ──────────────────────────────────────────────────────────────

STUDY_DIR = Path(__file__).resolve().parent.parent

# Load PROCESSED EDGAR data (consistent with manuscript pipeline)
# Processed_GHG_totals_by_country.csv = GHG_totals_by_country.csv after preprocessing.py
raw = pd.read_csv(STUDY_DIR / "data" / "processed" / "Processed_GHG_totals_by_country.csv")

# Load classification results
results = pd.read_excel(
    STUDY_DIR / "outputs" / "tables" / "Analysis_Trajectory Classification.xlsx",
    sheet_name="Country_Classifications"
)

print(f"Processed CSV rows: {len(raw)}")
print(f"Classification results rows: {len(results)}")
print(f"Classification columns: {results.columns.tolist()}")
print()

# ── 2. Merge processed emissions with classifications ─────────────────────────

# Keep only country, 1970, 2015, 2024 from processed CSV
raw_slim = raw[["Country", "1970", "2015", "2024"]].copy()
raw_slim.columns = ["Country", "E_1970", "E_2015", "E_2024"]

# Merge
df = results.merge(raw_slim, on="Country", how="left")

missing = df["E_2024"].isna().sum()
print(f"Countries missing 2024 emission data: {missing}")
print()

# ── 3. Verify CAGR calculation (cross-check against existing results) ─────────

# Post-Paris CAGR = ((E_2024 / E_2015)^(1/9) - 1) * 100
df["CAGR_PP_check"] = ((df["E_2024"] / df["E_2015"]) ** (1/9) - 1) * 100

# Compare against existing CAGR_PostParis_Pct
diff = (df["CAGR_PP_check"] - df["CAGR_PostParis_Pct"]).abs().max()
print(f"Max CAGR discrepancy vs existing results: {diff:.6f} (should be ~0)")
print()

# ── 4. Global totals ──────────────────────────────────────────────────────────

GLOBAL_2024 = raw["2024"].sum()
GLOBAL_1970 = raw["1970"].sum()
EDGAR_GLOBAL_2024 = 53206.4  # pre-exclusion EDGAR global total (from manuscript)

print(f"Global 2024 sum (all 208): {df['E_2024'].sum():.1f} Mt")
print(f"Global 1970 sum (all 208): {df['E_1970'].sum():.1f} Mt")
print()

# ── 5. Metric 1: Share of 2024 global emissions per trajectory group ──────────

print("=" * 70)
print("METRIC 1: Share of 2024 Global Emissions by Trajectory Group")
print("=" * 70)

total_2024 = df["E_2024"].sum()

group_2024 = df.groupby("Trajectory_Type")["E_2024"].sum()
# Use EDGAR global total as denominator — consistent with manuscript methodology (Section 2.3)
group_share = (group_2024 / EDGAR_GLOBAL_2024 * 100).round(1)

cat_order = ["Declining", "Stable", "Moderately Rising", "Rapidly Rising"]
for cat in cat_order:
    if cat in group_2024.index:
        print(f"{cat:20s}: {group_2024[cat]:10.1f} Mt  ({group_share[cat]:.1f}% of EDGAR global total)")

print(f"\n208-country 2024 total: {total_2024:.1f} Mt")
print(f"EDGAR global total 2024: {EDGAR_GLOBAL_2024:.1f} Mt")
print(f"Coverage: {total_2024/EDGAR_GLOBAL_2024*100:.2f}%")
print()

# ── 5b. Metric 1b: Share of 1970 global emissions per trajectory group ────────

EDGAR_GLOBAL_1970 = 23228.506  # EDGAR pre-exclusion 1970 global total

group_1970 = df.groupby("Trajectory_Type")["E_1970"].sum()
group_share_1970 = (group_1970 / EDGAR_GLOBAL_1970 * 100).round(1)

print("=" * 70)
print("METRIC 1b: Share of 1970 Global Emissions by Trajectory Group")
print("=" * 70)
for cat in cat_order:
    if cat in group_1970.index:
        print(f"{cat:20s}: {group_1970[cat]:10.1f} Mt  ({group_share_1970[cat]:.1f}% of EDGAR 1970 global total)")
print(f"\nEDGAR 1970 global total: {EDGAR_GLOBAL_1970:.1f} Mt")
print(f"208-country 1970 coverage: {df['E_1970'].sum()/EDGAR_GLOBAL_1970*100:.2f}%")
print()

# ── 6. Metric 2: Contribution to absolute emission increase (1970-2024) ───────

print("=" * 70)
print("METRIC 2: Contribution to Absolute Emission Increase (1970-2024)")
print("=" * 70)

df["Abs_increase"] = df["E_2024"] - df["E_1970"]

total_increase = df["Abs_increase"].sum()
group_increase = df.groupby("Trajectory_Type")["Abs_increase"].sum()
group_increase_share = (group_increase / total_increase * 100).round(1)

for cat in cat_order:
    if cat in group_increase.index:
        print(f"{cat:20s}: {group_increase[cat]:10.1f} Mt increase  ({group_increase_share[cat]:.1f}% of total increase)")

print(f"\nTotal absolute increase 1970-2024: {total_increase:.1f} Mt")
print()

# ── 7. Metric 3: Emission-weighted mean post-Paris CAGR ───────────────────────

print("=" * 70)
print("METRIC 3: Emission-Weighted Mean Post-Paris CAGR by Trajectory Group")
print("=" * 70)
print("(Weighted by 2015 base-year emissions)")
print()

def emission_weighted_mean(group_df, weight_col, value_col):
    """Compute emission-weighted mean CAGR."""
    weights = group_df[weight_col]
    values = group_df[value_col]
    return (weights * values).sum() / weights.sum()

for cat in cat_order:
    group_df = df[df["Trajectory_Type"] == cat].copy()
    n = len(group_df)
    
    # Unweighted mean (existing)
    unweighted = group_df["CAGR_PostParis_Pct"].mean()
    
    # Emission-weighted mean (new)
    weighted = emission_weighted_mean(group_df, "E_2015", "CAGR_PostParis_Pct")
    
    print(f"{cat:20s} (n={n:3d}): Unweighted = {unweighted:+.3f}%/yr | Emission-weighted = {weighted:+.3f}%/yr")

# Global weighted mean
global_weighted = emission_weighted_mean(df, "E_2015", "CAGR_PostParis_Pct")
global_unweighted = df["CAGR_PostParis_Pct"].mean()
print(f"\n{'Global':20s} (n=208): Unweighted = {global_unweighted:+.3f}%/yr | Emission-weighted = {global_weighted:+.3f}%/yr")
print()

# ── 8. Additional: Spec 3 emission share (reviewer concern) ──────────────────

print("=" * 70)
print("SPEC 3 CHECK: ≥10 Mt 1970 threshold — emission coverage")
print("=" * 70)

spec3 = df[df["E_1970"] >= 10].copy()
spec3_rr = spec3[spec3["Trajectory_Type"] == "Rapidly Rising"]

print(f"Spec 3 N: {len(spec3)}")
print(f"Spec 3 2024 emission sum: {spec3['E_2024'].sum():.1f} Mt")
print(f"Spec 3 coverage of 208-country total: {spec3['E_2024'].sum()/total_2024*100:.2f}%")
print(f"Spec 3 Rapidly Rising N: {len(spec3_rr)} ({len(spec3_rr)/len(spec3)*100:.1f}%)")
print()

# ── 9. Save results to Excel ──────────────────────────────────────────────────

output_path = STUDY_DIR / "outputs" / "tables" / "emission_weighted_results.xlsx"
with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
    
    # Sheet 1: Summary table
    summary = pd.DataFrame({
        "Trajectory_Group": cat_order,
        "N": [len(df[df["Trajectory_Type"]==c]) for c in cat_order],
        "Share_2024_Emissions_Pct_of_EDGAR_Global": [group_share.get(c, 0) for c in cat_order],
        "Share_1970_Emissions_Pct_of_EDGAR_Global": [group_share_1970.get(c, 0) for c in cat_order],
        "Abs_Increase_1970_2024_Mt": [group_increase.get(c, 0) for c in cat_order],
        "Abs_Increase_Share_Pct": [group_increase_share.get(c, 0) for c in cat_order],
        "Unweighted_Mean_PostParis_CAGR": [
            df[df["Trajectory_Type"]==c]["CAGR_PostParis_Pct"].mean() for c in cat_order
        ],
        "Emission_Weighted_Mean_PostParis_CAGR": [
            emission_weighted_mean(
                df[df["Trajectory_Type"]==c], "E_2015", "CAGR_PostParis_Pct"
            ) for c in cat_order
        ]
    })
    summary.to_excel(writer, sheet_name="Summary", index=False)
    
    # Sheet 2: Full country-level data
    df[["Country", "Trajectory_Type", "E_1970", "E_2015", "E_2024",
        "CAGR_PostParis_Pct", "Abs_increase"]].to_excel(
        writer, sheet_name="Country_Level", index=False
    )

print(f"Results saved to {output_path}")
print("Sheets: Summary, Country_Level")
