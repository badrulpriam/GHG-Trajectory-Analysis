# GHG Persistence & SDG 13 Alignment Analysis

A comprehensive empirical study of national greenhouse gas (GHG) emission trajectories (1970–2024) across 208 sovereign nations, assessing alignment with UN Sustainable Development Goal 13 (Climate Action) and evaluating the impact of global policy frameworks and economic shocks on emission patterns.

---

## Overview

This project investigates whether national GHG emission trajectories are compatible with SDG 13 targets, and whether major global interventions — the Kyoto Protocol, the Paris Agreement, and economic shocks such as the 2008 Global Financial Crisis (GFC) and COVID-19 — have produced lasting emission reductions.

**Core Finding**: More than 50% of nations are classified as *SDG 13.2-Critical*, meaning their emissions have more than doubled since 1970, indicating persistent structural misalignment with global climate targets despite successive international agreements.

---

## Project Structure

```
GHG_All_Analyses/
├── GHG_Persistence_Study/
│   ├── scripts/                          # Python analysis pipeline (10 scripts)
│   ├── data/
│   │   └── processed/
│   │       └── ghg_clean.csv             # Cleaned long-format analytical dataset
│   ├── outputs/
│   │   ├── tables/                       # 9 Excel result files
│   │   └── figures/                      # 20+ publication-quality figures
│   ├── GHG_totals_by_country.csv         # Raw EDGAR source data
│   ├── Methodology_*.docx                # Methods documentation (3 versions)
│   ├── results_section.docx              # Results write-up
│   └── discussion_section.docx          # Discussion write-up
├── Introduction/                         # Reference papers (13 PDFs)
├── Methodology/                          # Methodological references (5 PDFs)
└── Discussion/                           # Policy context materials (1 PDF)
```

---

## Data

**Source**: [EDGAR — Emissions Database for Global Atmospheric Research](https://edgar.jrc.ec.europa.eu/)

| Attribute | Detail |
|---|---|
| Coverage | 208 sovereign nations |
| Time Period | 1970–2024 (55 years) |
| Unit | Mt CO₂-equivalent (megatonnes) |
| Total Observations | 11,440 (208 countries × 55 years) |

**Data Range**: Anguilla (0.026 Mt CO₂-eq) → China (15,536 Mt CO₂-eq) in 2024 — a ~600,000x spread, requiring log transformation.

**Preprocessing** (`preprocessing.py`):
- Removed non-sovereign aggregate entities (GLOBAL TOTAL, EU27, International Aviation/Shipping)
- Reshaped from wide to long format
- Applied natural log transformation to stabilize variance
- Flagged 8 documented global shock years
- Output: `ghg_clean.csv` (11,440 rows)

---

## Analyses

### Analysis 1 — Emission Trajectory Classification & SDG 13 Alignment

**Script**: `Analysis_Trajectory Classification.py`

Countries are classified by their % change in GHG emissions from 1970 to 2024:

| Category | Threshold | SDG 13 Status | Count |
|---|---|---|---|
| Declining | < −10% | SDG 13.2-Aligned | 1 |
| Stable | −10% to +10% | SDG 13.2-Transitioning | 18 |
| Moderately Rising | +10% to +100% | SDG 13.2-At Risk | 97 |
| Rapidly Rising | > +100% | SDG 13.2-Critical | 92 |

**Key Result**: 44% of nations have doubled their emissions since 1970 (Rapidly Rising). Only 1 country is on a declining trajectory.

---

### Analysis 2 — Shock Response & Emission Resilience

**Script**: `analysis2_shock_resilience.py`

Measures how national emissions responded to three major global shocks:

| Shock | Year |
|---|---|
| Global Financial Crisis (GFC) | 2009 |
| Paris Agreement Adoption | 2015 |
| COVID-19 Pandemic | 2020 |

**Resilience Metrics** (per country, per shock):
- **Resistance**: % change at shock year vs. baseline
- **Recovery**: % change 3 years post-shock
- **Permanence**: Whether post-shock emissions stayed below pre-shock levels

**Resilience Classifications**:
- **Absorbed** — Permanent reduction (dropped and stayed below baseline)
- **Rebounded** — Temporary drop followed by exceeding baseline
- **Unaffected** — No initial decline observed

**Key Result**: Most nations rebounded after each shock. COVID-19 produced the largest immediate drops, but recovery was rapid — emissions returned to pre-pandemic levels within 1–2 years.

---

### Analysis 3 — Paris Agreement Effectiveness

**Script**: `analysis3_paris_effectiveness.py`

Compares Compound Annual Growth Rate (CAGR) across four policy eras:

| Era | Period | Context |
|---|---|---|
| Era 1 | 1970–1990 | Pre-Kyoto baseline |
| Era 2 | 1990–2005 | Kyoto Protocol era |
| Era 3 | 2005–2015 | Post-Kyoto gap |
| Era 4 | 2015–2024 | Paris Agreement era |

**Paris Effect** = CAGR reduction between Era 3 and Era 4.

**Key Result**: Post-Paris CAGR shows some reduction relative to the Pre-Paris period, but the global trajectory remains upward — suggesting the Paris Agreement has slowed but not reversed emission growth.

---

### Sensitivity Analyses

| Script | Purpose |
|---|---|
| `Sensitivity Analysis_Threshold.py` | Tests three threshold systems (Baseline, Set A strict, Set B wide) to verify classification robustness |
| `Sensitivity Analysis_Sample Compostion.py` | Tests robustness by excluding outlier countries from the sample |

**Result**: The headline finding (>50% of nations SDG 13.2-Critical) holds across all alternative specifications.

---

## Analysis Pipeline

Run scripts in the following order:

```
1. preprocessing.py                          → Produces ghg_clean.csv
2. Analysis_Trajectory Classification.py     → Produces analysis1_trajectory_results.xlsx
3. analysis2_shock_resilience.py             → Shock response & resilience tables
   analysis3_paris_effectiveness.py          → Era CAGR comparison tables
4. Sensitivity Analysis_Threshold.py
   Sensitivity Analysis_Sample Compostion.py
5. figures_publication.py + Figure*.py       → Publication-quality figures
```

---

## Outputs

| Type | Count | Format | Description |
|---|---|---|---|
| Tables | 9 | `.xlsx` | Trajectory classifications, shock resilience, Paris effectiveness, sensitivity analyses |
| Figures | 20+ | `.png` / `.tiff` / `.pdf` | Time series, heatmaps, bubble charts, bar charts, distribution plots |
| Dataset | 1 | `.csv` | Cleaned long-format analytical dataset (11,440 rows) |

**Figure specifications** (Elsevier journal standard):
- Resolution: 600 DPI
- Width: 190mm (double-column)
- Font: Arial
- Formats: TIFF LZW + PDF vector backup

---

## Methods Summary

- **Compound Annual Growth Rate (CAGR)** — cross-era emission growth comparison
- **Descriptive statistics** — mean, median, standard deviation, skewness, kurtosis
- **Percentage change analysis** — 1970–2024 and 2015–2024 windows
- **Log transformation** — natural log to stabilize the wide emission range
- **Structural break identification** — shock year classification
- **Resilience classification** — categorical grouping based on post-shock trajectory
- **Threshold sensitivity testing** — robustness verification of classification boundaries

---

## Technology Stack

| Component | Details |
|---|---|
| Language | Python 3.13 |
| Data handling | pandas, numpy |
| Statistics | scipy.stats |
| Visualization | matplotlib, seaborn |
| Excel output | openpyxl |

---

## Key Conclusions

1. **Structural misalignment persists**: >50% of nations are SDG 13.2-Critical — emissions have more than doubled since 1970.
2. **Shocks produce temporary, not permanent, reductions**: All three major shocks (GFC, Paris, COVID) were followed by rebounds in most nations.
3. **Paris Agreement decelerated but did not reverse growth**: Post-Paris CAGR is lower than Pre-Paris, but global emissions continue rising.
4. **Trajectory persistence is the norm**: Long-run emission growth trajectories show strong path dependence, suggesting deep economic–emissions coupling.
5. **Results are robust**: All headline findings hold under alternative threshold specifications and sample compositions.

---

## Research Context

This study addresses a gap in the literature: no prior work has systematically classified all 208 sovereign nations against SDG 13.2 targets, nor comprehensively analyzed shock resilience across GFC, Paris, and COVID simultaneously.

**Target journals**: *Science of the Total Environment*, *Ecological Indicators*, *Climate Policy*

---

## Reference Materials

| Folder | Contents |
|---|---|
| `Introduction/` | 13 reference PDFs for literature context |
| `Methodology/` | 5 methodological reference papers |
| `Discussion/` | Policy context material |
| `GHG_Persistence_Study/*.docx` | Draft manuscript sections (Introduction, Methodology, Results, Discussion) |
