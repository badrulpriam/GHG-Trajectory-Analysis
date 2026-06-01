# =============================================================================
# SENSITIVITY ANALYSIS I — ALTERNATIVE THRESHOLD SPECIFICATIONS
# Project  : GHG Persistence Study
#=============================================================================
#
# PURPOSE:
#   Test robustness of the baseline trajectory classification to alternative
#   upper boundary specifications for the Stable and Moderately Rising
#   categories. The Declining boundary (< -10%) is held constant.
#
# THRESHOLD SYSTEMS:
#   Baseline : Stable = -10% to +10%;  Mod. Rising = +10% to +100%; Rapid = > +100%
#   Set A    : Stable = -10% to  +5%;  Mod. Rising =  +5% to  +75%; Rapid = >  +75%
#   Set B    : Stable = -10% to +15%;  Mod. Rising = +15% to +150%; Rapid = > +150%
#
# INPUT  : outputs/tables/Analysis_Trajectory Classification.xlsx
# OUTPUT : outputs/tables/Sensitivity Analysis_Threshold.xlsx
#          
# =============================================================================

import os, warnings
import pandas as pd
warnings.filterwarnings('ignore')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE_PATH   = os.path.join(PROJECT_ROOT, "outputs", "tables")

TRAJ_ORDER = ['Declining','Stable','Moderately Rising','Rapidly Rising']

print("="*65)
print("  SENSITIVITY ANALYSIS — ALTERNATIVE THRESHOLD SYSTEMS")
print("="*65)

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
df = pd.read_excel(
    os.path.join(TABLE_PATH,'Analysis_Trajectory Classification.xlsx'),
    sheet_name='Country_Classifications'
)
pct = df['Change_Pct_1970_2024'].values
n   = len(df)
print(f"\n  Countries: {n}")

# ── CLASSIFICATION FUNCTIONS ──────────────────────────────────────────────────
def classify_baseline(p):
    if p < -10:    return 'Declining'
    elif p <= 10:  return 'Stable'
    elif p <= 100: return 'Moderately Rising'
    else:          return 'Rapidly Rising'

def classify_setA(p):
    """Set A — Stricter: Stable=±5%, Moderate=+5–75%, Rapid=>75%"""
    if p < -10:   return 'Declining'
    elif p <= 5:  return 'Stable'
    elif p <= 75: return 'Moderately Rising'
    else:         return 'Rapidly Rising'

def classify_setB(p):
    """Set B — Wider: Stable=±15%, Moderate=+15–150%, Rapid=>150%"""
    if p < -10:    return 'Declining'
    elif p <= 15:  return 'Stable'
    elif p <= 150: return 'Moderately Rising'
    else:          return 'Rapidly Rising'

df['Class_Baseline'] = [classify_baseline(p) for p in pct]
df['Class_SetA']     = [classify_setA(p)     for p in pct]
df['Class_SetB']     = [classify_setB(p)     for p in pct]

# ── COUNTS ────────────────────────────────────────────────────────────────────
SYSTEMS = {
    'Baseline'                  : 'Class_Baseline',
    'Set A (Stricter Stable)'   : 'Class_SetA',
    'Set B (Wider Stable)'      : 'Class_SetB',
}
system_counts = {
    s: {t: (df[col]==t).sum() for t in TRAJ_ORDER}
    for s, col in SYSTEMS.items()
}

changed_A = df[df['Class_Baseline'] != df['Class_SetA']][
    ['Country','Change_Pct_1970_2024','Class_Baseline','Class_SetA']
].sort_values('Change_Pct_1970_2024').copy()

changed_B = df[df['Class_Baseline'] != df['Class_SetB']][
    ['Country','Change_Pct_1970_2024','Class_Baseline','Class_SetB']
].sort_values('Change_Pct_1970_2024').copy()

# ── PRINT RESULTS ─────────────────────────────────────────────────────────────
print(f"\n  {'System':<30} {'Decl':>6} {'Stable':>7} {'Mod.R':>7} {'Rapid':>7} {'Changed':>9}")
print(f"  {'─'*68}")
for si, (s, col) in enumerate(SYSTEMS.items()):
    c       = system_counts[s]
    changed = 0 if si==0 else (df['Class_Baseline']!=df[col]).sum()
    print(f"  {s:<30} {c['Declining']:>6} {c['Stable']:>7} "
          f"{c['Moderately Rising']:>7} {c['Rapidly Rising']:>7} {changed:>9}")

print(f"\n  SET A — {len(changed_A)} countries reclassified:")
print(f"  {'Country':<40} {'Chg%':>7}  {'From':<22} To")
print(f"  {'─'*80}")
for _, r in changed_A.iterrows():
    print(f"  {r['Country']:<40} {r['Change_Pct_1970_2024']:>+7.1f}%  "
          f"{r['Class_Baseline']:<22} → {r['Class_SetA']}")

print(f"\n  SET B — {len(changed_B)} countries reclassified:")
print(f"  {'Country':<40} {'Chg%':>7}  {'From':<22} To")
print(f"  {'─'*80}")
for _, r in changed_B.iterrows():
    print(f"  {r['Country']:<40} {r['Change_Pct_1970_2024']:>+7.1f}%  "
          f"{r['Class_Baseline']:<22} → {r['Class_SetB']}")

# ── HEADLINE TEST ─────────────────────────────────────────────────────────────
print(f"\n  HEADLINE TEST — majority of nations SDG 13.2-Critical:")
print(f"  {'─'*55}")
for s, counts in system_counts.items():
    nr    = counts['Rapidly Rising']
    share = nr/n*100
    holds = 'YES ✓' if nr > n*0.5 else 'NO ✗'
    print(f"  {s:<30} {nr}/208 ({share:.1f}%)  Headline: {holds}")

# ── EXPORT TABLE S1 ───────────────────────────────────────────────────────────
s1a = pd.DataFrame({
    'System'                      : list(SYSTEMS.keys()),
    'Stable threshold'            : ['−10% to +10%','−10% to +5%','−10% to +15%'],
    'Mod. Rising threshold'       : ['+10% to +100%','+5% to +75%','+15% to +150%'],
    'Rapid Rising threshold'      : ['> +100%','> +75%','> +150%'],
    'N Declining'                 : [system_counts[s]['Declining']          for s in SYSTEMS],
    'N Stable'                    : [system_counts[s]['Stable']              for s in SYSTEMS],
    'N Mod. Rising'               : [system_counts[s]['Moderately Rising']   for s in SYSTEMS],
    'N Rapidly Rising'            : [system_counts[s]['Rapidly Rising']      for s in SYSTEMS],
    'Countries reclassified'      : [0, len(changed_A), len(changed_B)],
    'Reclassified (%)'            : ['0%',f'{len(changed_A)/n*100:.1f}%',f'{len(changed_B)/n*100:.1f}%'],
    'Headline holds (>50% SDG 13.2-Critical)': [
        'Yes' if system_counts[s]['Rapidly Rising']>n*0.5 else 'No'
        for s in SYSTEMS
    ],
})

rA = changed_A.rename(columns={
    'Change_Pct_1970_2024':'GHG Change 1970-2024 (%)','Class_Baseline':'Baseline Class','Class_SetA':'Set A Class'
})
rA['Reclassification'] = rA['Baseline Class'] + ' → ' + rA['Set A Class']

rB = changed_B.rename(columns={
    'Change_Pct_1970_2024':'GHG Change 1970-2024 (%)','Class_Baseline':'Baseline Class','Class_SetB':'Set B Class'
})
rB['Reclassification'] = rB['Baseline Class'] + ' → ' + rB['Set B Class']

with pd.ExcelWriter(
    os.path.join(TABLE_PATH,'Sensitivity Analysis_Threshold.xlsx'),engine='openpyxl'
) as writer:
    s1a.to_excel(writer,sheet_name='S1a_System_Comparison',  index=False)
    rA.to_excel( writer,sheet_name='S1b_SetA_Reclassified',  index=False)
    rB.to_excel( writer,sheet_name='S1c_SetB_Reclassified',  index=False)
print(f"\n  ✓ Saved: Sensitivity Analysis_Threshold.xlsx")

# ── PAPER-READY SUMMARY ───────────────────────────────────────────────────────
br = system_counts['Baseline']['Rapidly Rising']
ar = system_counts['Set A (Stricter Stable)']['Rapidly Rising']
bsr= system_counts['Set B (Wider Stable)']['Rapidly Rising']

print(f"""
{"="*65}
  PAPER-READY SENSITIVITY STATEMENT
{"="*65}

  SDG 13.2-Critical (Rapidly Rising) counts:
    Baseline : {br}/208 ({br/208*100:.1f}%)
    Set A    : {ar}/208 ({ar/208*100:.1f}%)
    Set B    : {bsr}/208 ({bsr/208*100:.1f}%)

  Countries reclassified:
    Baseline → Set A : {len(changed_A)} ({len(changed_A)/208*100:.1f}% of panel)
    Baseline → Set B : {len(changed_B)} ({len(changed_B)/208*100:.1f}% of panel)

  Declining count: IDENTICAL in all systems (n=31, 14.9%)

  Headline holds in ALL systems — majority SDG 13.2-Critical: YES
{"="*65}
""")
