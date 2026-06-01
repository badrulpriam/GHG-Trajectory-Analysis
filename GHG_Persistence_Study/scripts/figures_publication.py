# =============================================================================
# PUBLICATION FIGURES — ELSEVIER JOURNAL STANDARD
# Project  : GHG Persistence Study
# Figures  : 1 (distribution) | 2 (trajectories) | 3 (heatmap)
# Format   : TIFF LZW 600 DPI + PDF vector  (Elsevier preferred)
# Width    : 190mm double-column
# =============================================================================

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.lines as mlines
import matplotlib.gridspec as gridspec
from matplotlib.ticker import MaxNLocator
from scipy import stats
from scipy.stats import gaussian_kde, norm

warnings.filterwarnings('ignore')

# ── PATHS ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH    = os.path.join(PROJECT_ROOT, "data", "processed", "ghg_clean.csv")
FIG_PATH     = os.path.join(PROJECT_ROOT, "outputs", "figures")

# ── ELSEVIER DIMENSIONS ───────────────────────────────────────────────────────
W2  = 7.48      # 190mm in inches — Elsevier double column
DPI = 600

# ── GLOBAL STYLE ─────────────────────────────────────────────────────────────
# Applied ONCE before any figure is created
matplotlib.rcParams.update({
    'font.family'        : 'Arial',        # Elsevier preferred font
    'font.size'          : 9,
    'axes.titlesize'     : 10,
    'axes.labelsize'     : 9,
    'xtick.labelsize'    : 8,
    'ytick.labelsize'    : 8,
    'legend.fontsize'    : 8,
    'axes.linewidth'     : 0.8,
    'xtick.major.width'  : 0.6,
    'ytick.major.width'  : 0.6,
    'xtick.direction'    : 'out',
    'ytick.direction'    : 'out',
    'figure.facecolor'   : 'white',
    'axes.facecolor'     : 'white',
    'savefig.facecolor'  : 'white',
    'axes.spines.top'    : False,
    'axes.spines.right'  : False,
    'axes.grid'          : False,          # controlled per-axis below
})

# ── CONSISTENT COLOUR ASSIGNMENTS ─────────────────────────────────────────────
BAR_COLOR  = '#4A90C4'    # histogram bars — both panels same
KDE_COLOR  = '#C0392B'    # KDE curve
NORM_COLOR = '#7F8C8D'    # normal reference line

# Wong (2011) colourblind-safe palette for trajectory lines
TRAJ_COLOURS = {
    'China'          : '#000000',
    'United States'  : '#D55E00',
    'Russia'         : '#CC79A7',
    'India'          : '#009E73',
    'Japan'          : '#0072B2',
    'Germany'        : '#56B4E9',
    'Brazil'         : '#E69F00',
    'United Kingdom' : '#8B4513',
    'Canada'         : '#3CB371',
    'Ukraine'        : '#7B2D8B',
}

SHOCKS = {
    2009 : ('#0072B2', 'GFC trough (2009)'),
    2015 : ('#009E73', 'Paris Agreement (2015)'),
    2020 : ('#D55E00', 'COVID-19 (2020)'),
}

# ── SAVE HELPER — TIFF LZW + PDF ─────────────────────────────────────────────
def save_fig(fig, stem):
    """Save as both TIFF (Elsevier submission) and PDF (vector backup)."""
    tiff_path = os.path.join(FIG_PATH, f'{stem}.tiff')
    pdf_path  = os.path.join(FIG_PATH, f'{stem}.pdf')
    fig.savefig(
        tiff_path, dpi=DPI, format='tiff',
        facecolor='white', edgecolor='none',
        bbox_inches='tight',
        pil_kwargs={'compression': 'tiff_lzw'}   # LZW: lossless, smaller file
    )
    fig.savefig(
        pdf_path, format='pdf',
        facecolor='white', edgecolor='none',
        bbox_inches='tight'
    )

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
print("=" * 62)
print("  GHG PERSISTENCE STUDY — PUBLICATION FIGURES")
print("=" * 62)

df          = pd.read_csv(DATA_PATH)
df['Year']  = df['Year'].astype(int)
raw_vals    = df['GHG_Emissions'].dropna().values
log_vals    = df['log_GHG'].dropna().values
mean_emis   = df.groupby('Country')['GHG_Emissions'].mean()
top10       = mean_emis.nlargest(10).index.tolist()
top20       = mean_emis.nlargest(20).index.tolist()

print(f"  Observations : {len(df):,}  |  Countries : {df['Country'].nunique()}")


# =============================================================================
# FIGURE 1 — Raw vs Log-Transformed Distribution
# Two side-by-side panels with shared y-label via fig.supylabel()
# =============================================================================
print("\n[1/3]  Figure 1: Distribution ...")

fig1, (ax1, ax2) = plt.subplots(
    1, 2,
    figsize=(W2, 3.20),                # exact 190mm × ~81mm
    constrained_layout=True            # safer than tight_layout
)

# ── Panel (a): Raw ────────────────────────────────────────────────────────────
p99    = np.percentile(raw_vals, 99)
nexcl  = (raw_vals > p99).sum()
d_clip = raw_vals[raw_vals <= p99]

ax1.hist(d_clip, bins=60,
         color=BAR_COLOR, alpha=0.80,
         edgecolor='white', linewidth=0.3,
         zorder=3)

# KDE — Scott bandwidth, scaled to frequency
kde1      = gaussian_kde(d_clip, bw_method='scott')
x1        = np.linspace(d_clip.min(), d_clip.max(), 500)
bin_w1    = (d_clip.max() - d_clip.min()) / 60
ax1.plot(x1, kde1(x1) * len(d_clip) * bin_w1,
         color=KDE_COLOR, lw=1.5, zorder=4)

# Horizontal grid only — cleaner than full grid
ax1.yaxis.grid(True, color='#CCCCCC', linewidth=0.4, alpha=0.7, zorder=0)
ax1.set_axisbelow(True)

ax1.set_xlabel(r'GHG Emissions (Mt CO$_2$-eq)', labelpad=4)
ax1.set_ylabel('Frequency', labelpad=4)  # will be replaced by supylabel below
ax1.xaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f'{x:,.0f}')
)
ax1.set_xlim(left=0)

# Skewness and kurtosis — computed via scipy for accuracy
skew_raw = float(stats.skew(raw_vals))
kurt_raw = float(stats.kurtosis(raw_vals))          # excess kurtosis

stats_a = (
    f'$n$ = {len(raw_vals):,}\n'
    f'Mean     = {raw_vals.mean():.1f}\n'
    f'Median  = {np.median(raw_vals):.1f}\n'
    f'Skewness = {skew_raw:.2f}\n'
    f'Kurtosis  = {kurt_raw:.1f}'
)
ax1.text(0.97, 0.97, stats_a,
         transform=ax1.transAxes, ha='right', va='top', fontsize=7.5,
         bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                   edgecolor='#AAAAAA', linewidth=0.6, alpha=0.9),
         linespacing=1.6, family='monospace')

ax1.text(0.97, 0.04,
         f'{nexcl} values >99th pct. excluded',
         transform=ax1.transAxes, ha='right', va='bottom',
         fontsize=7, color='#555555', style='italic')

ax1.text(-0.12, 1.05, '(a)', transform=ax1.transAxes,
         fontsize=10, fontweight='bold', va='top')

# ── Panel (b): Log-transformed ────────────────────────────────────────────────
ax2.hist(log_vals, bins=60,
         color=BAR_COLOR, alpha=0.80,  # same colour as panel (a)
         edgecolor='white', linewidth=0.3,
         zorder=3)

kde2   = gaussian_kde(log_vals, bw_method='scott')
x2     = np.linspace(log_vals.min(), log_vals.max(), 500)
bin_w2 = (log_vals.max() - log_vals.min()) / 60
ax2.plot(x2, kde2(x2) * len(log_vals) * bin_w2,
         color=KDE_COLOR, lw=1.5, zorder=4, label='KDE')

# Normal fit overlay — shows near-normality achieved
mu2, sd2 = log_vals.mean(), log_vals.std()
ax2.plot(x2, norm.pdf(x2, mu2, sd2) * len(log_vals) * bin_w2,
         color=NORM_COLOR, lw=1.2, ls='--', zorder=4, label='Normal fit')

ax2.yaxis.grid(True, color='#CCCCCC', linewidth=0.4, alpha=0.7, zorder=0)
ax2.set_axisbelow(True)
ax2.set_xlabel(r'ln(GHG Emissions)', labelpad=4)

# Remove duplicate y-label and tick labels from right panel
ax2.set_ylabel('')
ax2.tick_params(labelleft=False)

skew_log = float(stats.skew(log_vals))
kurt_log = float(stats.kurtosis(log_vals))

stats_b = (
    f'$n$ = {len(log_vals):,}\n'
    f'Mean     = {mu2:.3f}\n'
    f'Median  = {np.median(log_vals):.3f}\n'
    f'Skewness = {skew_log:.3f}\n'
    f'Kurtosis  = {kurt_log:.3f}'
)
ax2.text(0.03, 0.97, stats_b,
         transform=ax2.transAxes, ha='left', va='top', fontsize=7.5,
         bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                   edgecolor='#AAAAAA', linewidth=0.6, alpha=0.9),
         linespacing=1.6, family='monospace')

ax2.legend(loc='upper right', framealpha=0.9,
           edgecolor='#AAAAAA', fancybox=False,
           handlelength=1.8, handletextpad=0.5)

ax2.text(-0.08, 1.05, '(b)', transform=ax2.transAxes,
         fontsize=10, fontweight='bold', va='top')

# Single shared y-label — replaces per-panel labels
fig1.supylabel('Frequency', x=0.01, fontsize=9)

save_fig(fig1, 'fig1_distribution')
plt.close(fig1)
print("   ✓  fig1_distribution.tiff / .pdf")


# =============================================================================
# FIGURE 2 — Emission Trajectories: Top 10 Emitters (1970–2024)
# =============================================================================
print("[2/3]  Figure 2: Trajectories ...")

df10     = df[df['Country'].isin(top10)].copy()
last2024 = (df10[df10['Year'] == 2024]
            .set_index('Country')['log_GHG']
            .sort_values(ascending=False))
order10  = last2024.index.tolist()

fig2, ax = plt.subplots(
    figsize=(W2, 3.80),
    constrained_layout=True
)

for country in order10:
    data = df10[df10['Country'] == country].sort_values('Year')
    col  = TRAJ_COLOURS.get(country, '#444444')
    ax.plot(data['Year'], data['log_GHG'],
            color=col, linewidth=1.6,
            solid_capstyle='round', zorder=4)

    # Inline country label at line end — no legend box needed
    last = data[data['Year'] == data['Year'].max()]
    if not last.empty:
        ax.annotate(
            country,
            xy=(last['Year'].values[0], last['log_GHG'].values[0]),
            xytext=(5, 0),
            textcoords='offset points',
            fontsize=7.0, color=col,
            va='center', fontweight='medium'
        )

# Shock year markers — subtle band + dashed line
shock_handles = []
for yr, (col, label) in SHOCKS.items():
    ax.axvspan(yr - 0.5, yr + 0.5,
               color=col, alpha=0.12, zorder=2, linewidth=0)
    ax.axvline(yr, color=col, linewidth=1.0,
               linestyle='--', alpha=0.70, zorder=3)
    shock_handles.append(
        mlines.Line2D([], [], color=col, linewidth=1.3,
                      linestyle='--', alpha=0.85, label=label)
    )

ax.set_xlim(1969, 2030)
ax.set_xlabel('Year', labelpad=5)
ax.set_ylabel(r'ln(GHG Emissions, Mt CO$_2$-eq)', labelpad=5)
ax.xaxis.set_major_locator(mticker.MultipleLocator(10))
ax.xaxis.set_minor_locator(mticker.MultipleLocator(5))
ax.tick_params(axis='x', which='minor', length=2.5, width=0.5)

# Horizontal grid only
ax.yaxis.grid(True, color='#CCCCCC', linewidth=0.4, alpha=0.7)
ax.set_axisbelow(True)

leg = ax.legend(
    handles=shock_handles,
    loc='upper left',
    title='Structural shock years',
    title_fontsize=8,
    fontsize=7.8,
    frameon=True, framealpha=0.95,
    edgecolor='#AAAAAA',
    borderpad=0.6, labelspacing=0.40,
    handlelength=2.0,
)
leg.get_title().set_fontweight('medium')

save_fig(fig2, 'fig2_trajectories')
plt.close(fig2)
print("   ✓  fig2_trajectories.tiff / .pdf")


# =============================================================================
# FIGURE 3 — Panel Heatmap: Top 20 Emitters (1970–2024)
# Landscape | Horizontal colorbar below | YlOrBr colourmap
# =============================================================================
print("[3/3]  Figure 3: Heatmap ...")

df20  = df[df['Country'].isin(top20)].copy()
pivot = df20.pivot(index='Country', columns='Year', values='log_GHG')

row_order = (
    df[df['Country'].isin(top20)]
    .groupby('Country')['GHG_Emissions']
    .mean()
    .sort_values(ascending=False)
    .index.tolist()
)
pivot   = pivot.loc[row_order]
yr_cols = list(pivot.columns)
n_c     = len(row_order)

fig3 = plt.figure(figsize=(W2, 4.80), facecolor='white',
                  layout='constrained')
gs3  = gridspec.GridSpec(2, 1,
                         height_ratios=[22, 1],
                         hspace=0.08,
                         figure=fig3)
ax_hm = fig3.add_subplot(gs3[0])
ax_cb = fig3.add_subplot(gs3[1])

im = ax_hm.imshow(
    pivot.values,
    aspect='auto',
    cmap='YlOrBr',
    interpolation='nearest',
    vmin=pivot.values.min(),
    vmax=pivot.values.max()
)

# Horizontal colorbar in dedicated subplot
cbar = fig3.colorbar(im, cax=ax_cb, orientation='horizontal')
cbar.set_label(r'ln(GHG Emissions, Mt CO$_2$-eq)', fontsize=8.5, labelpad=4)
cbar.ax.tick_params(labelsize=8)
cbar.outline.set_linewidth(0.5)
cbar.locator = MaxNLocator(nbins=6)
cbar.update_ticks()

# Shock year lines — white with year annotation at top of heatmap
for yr, (col, _) in SHOCKS.items():
    if yr in yr_cols:
        xp = yr_cols.index(yr)
        ax_hm.axvline(xp, color='white', linewidth=2.0, alpha=0.95, zorder=5)
        ax_hm.text(xp, n_c - 0.4, str(yr),
                   fontsize=7.5, color='white',
                   ha='center', va='top', fontweight='bold')

# Y-axis: country names ≥8pt
ax_hm.set_yticks(range(n_c))
ax_hm.set_yticklabels(row_order, fontsize=8.5)

# X-axis: decade ticks only
dec_idx = [i for i, y in enumerate(yr_cols) if y % 10 == 0]
dec_lab = [str(y) for y in yr_cols if y % 10 == 0]
ax_hm.set_xticks(dec_idx)
ax_hm.set_xticklabels(dec_lab, fontsize=8.5)
ax_hm.tick_params(axis='x', bottom=True, top=False, length=3)

ax_hm.set_xlabel('Year', labelpad=5)
ax_hm.set_ylabel('Country (ranked by mean emissions, 1970–2024)', labelpad=6)
ax_hm.grid(False)

for spine in ax_hm.spines.values():
    spine.set_linewidth(0.5)
    spine.set_edgecolor('#999999')

fig3.text(
    0.5, -0.01,
    'Note: Light yellow = lower emissions; dark brown = higher emissions. '
    'White vertical lines denote structural shock years. '
    'Top 20 emitters ranked by mean GHG emissions, 1970–2024.',
    ha='center', fontsize=6.8, style='italic', color='#555555'
)

save_fig(fig3, 'fig3_heatmap')
plt.close(fig3)
print("   ✓  fig3_heatmap.tiff / .pdf")

# ── COMPLETION ────────────────────────────────────────────────────────────────
print(f"\n{'=' * 62}")
print("  ALL FIGURES COMPLETE")
print(f"{'=' * 62}")
print(f"  Font         : Arial  (Elsevier preferred)")
print(f"  Format       : TIFF LZW 600 DPI  +  PDF vector")
print(f"  Width        : 190 mm  (double column)")
print(f"  Fig 1        : supylabel, monospace stats, shared y-axis")
print(f"  Fig 2        : inline labels, 3 shock years, horizontal grid")
print(f"  Fig 3        : landscape, 20 countries, horizontal colorbar")
print(f"  Location     : outputs/figures/")
print(f"{'=' * 62}")
