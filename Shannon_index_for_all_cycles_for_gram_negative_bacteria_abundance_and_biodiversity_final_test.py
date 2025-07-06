
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates
from matplotlib.patches import Patch
from datetime import datetime
from scipy import stats  # Using scipy.stats instead of statsmodels

# === Load data ===
file_path = 'Wyniki_powietrze-3.xlsx'
sheet_name = 'Powietrze zewnątrz-G(-)'
df = pd.read_excel(file_path, sheet_name=sheet_name)

# === Convert 'Data' to datetime with correct day-first format ===
df['Data'] = pd.to_datetime(df['Data'], errors='coerce', dayfirst=True)

# === Drop rows with missing key values ===
df = df.dropna(subset=['Data', 'Miejsce poboru', 'Rodzaj/gatunek', 'Pobór'])

# === Rename columns for clarity ===
df.rename(columns={
    'Miejsce poboru': 'Location',
    'Rodzaj/gatunek': 'Species',
    'Pobór': 'Cycle'
}, inplace=True)

# === Filter for Gram-negative bacteria ===
gram_negative_keywords = [
    'Pseudomonas', 'Acinetobacter', 'Enterobacter', 'Klebsiella', 'Serratia',
    'Stenotrophomonas', 'Rahnella', 'Pantoea', 'Escherichia', 'Shigella',
    'Neisseria', 'Salmonella', 'Bacteroides', 'Haemophilus', 'Azotobacter',
    'Erwinia', 'Lelliottia', 'Rhizobium', 'Oligella', 'Comamonas', 'Burkholderia',
    'Sphingomonas', 'Moraxella', 'Shewanella', 'Citrobacter', 'Morganella',
    'Proteus', 'Providencia', 'Yersinia', 'Vibrio', 'Aeromonas', 'Campylobacter',
    'Helicobacter', 'Bordetella', 'Brucella', 'Legionella', 'Francisella',
    'Fusobacterium', 'Porphyromonas', 'Prevotella', 'Stutzerimonas', 'Kluyvera',
    'Buttiauxella', 'Leclercia', 'Psychrobacter', 'Enterobacteriaceae', 'Moellerella', 'Gamma'
]
df = df[df['Species'].str.contains('|'.join(gram_negative_keywords), case=False, na=False)]

# === Shannon Index function ===
def calculate_shannon(series):
    counts = series.value_counts()
    proportions = counts / counts.sum()
    return -(proportions * np.log(proportions)).sum()

# === Aggregate by date and location ===
shannon_df = df.groupby(['Data', 'Location'])['Species'].apply(calculate_shannon).reset_index()
shannon_df.rename(columns={'Species': 'Shannon_H'}, inplace=True)

# === Compute abundance per date-location ===
abundance_df = df.groupby(['Data', 'Location']).size().reset_index(name='Abundance')

# === Merge Shannon and Abundance ===
merged_df = pd.merge(shannon_df, abundance_df, on=['Data', 'Location'])

# === Fixed seasonal definitions ===
season_ranges = {
    'Winter': [('12-01', '02-28')],
    'Spring': [('03-01', '05-31')],
    'Summer': [('06-01', '08-31')],
    'Autumn': [('09-01', '11-30')],
}
season_colors = {
    'Winter': '#cce5ff',
    'Spring': '#d4edda',
    'Summer': '#fff3cd',
    'Autumn': '#f8d7da'
}

# === Build season spans ===
min_date = merged_df['Data'].min()
max_date = merged_df['Data'].max()
years = list(range(min_date.year - 1, max_date.year + 2))

season_spans = []
for year in years:
    for season, periods in season_ranges.items():
        for start_suffix, end_suffix in periods:
            if season == 'Winter':
                start = pd.to_datetime(f'{year}-12-01')
                end = pd.to_datetime(f'{year + 1}-02-28')
            else:
                start = pd.to_datetime(f'{year}-{start_suffix}')
                end = pd.to_datetime(f'{year}-{end_suffix}')
            if end >= min_date and start <= max_date:
                season_spans.append((season, start, end))

# === Assign season to each row ===
def get_season(date):
    for season, start, end in season_spans:
        if start <= date <= end:
            return season
    return 'Unknown'

merged_df['Season'] = merged_df['Data'].apply(get_season)

# === Violin plots ===
plt.figure(figsize=(16, 6))

# Shannon vs Season
plt.subplot(1, 2, 1)
sns.violinplot(data=merged_df, x='Season', y='Shannon_H', hue='Location', inner='box')
plt.title('Shannon Diversity by Season and Location')
plt.ylabel("Shannon Index (H')")
plt.xticks(rotation=45)

# Abundance vs Season
plt.subplot(1, 2, 2)
sns.violinplot(data=merged_df, x='Season', y='Abundance', hue='Location', inner='box')
plt.title('Abundance by Season and Location')
plt.ylabel("Abundance (Isolate Count)")
plt.xticks(rotation=45)

plt.tight_layout()
plt.show()

# === Correlation plot (Shannon vs Abundance) ===
sns.lmplot(data=merged_df, x='Abundance', y='Shannon_H', hue='Location', col='Season', height=5)
plt.suptitle('Shannon vs Abundance by Season and Location', y=1.05)
plt.show()

# === Statistical tests using scipy.stats ===
# Two-way ANOVA for Shannon
seasons = merged_df['Season'].unique()
locations = merged_df['Location'].unique()

print("=== Two-way ANOVA for Shannon Diversity ===")
shannon_groups = [merged_df[merged_df['Season'] == season]['Shannon_H'] for season in seasons]
f_stat, p_val = stats.f_oneway(*shannon_groups)
print(f"Season effect - F-statistic: {f_stat:.4f}, p-value: {p_val:.4f}")

shannon_loc_groups = [merged_df[merged_df['Location'] == loc]['Shannon_H'] for loc in locations]
f_stat, p_val = stats.f_oneway(*shannon_loc_groups)
print(f"Location effect - F-statistic: {f_stat:.4f}, p-value: {p_val:.4f}")

print("\n=== Two-way ANOVA for Abundance ===")
abundance_groups = [merged_df[merged_df['Season'] == season]['Abundance'] for season in seasons]
f_stat, p_val = stats.f_oneway(*abundance_groups)
print(f"Season effect - F-statistic: {f_stat:.4f}, p-value: {p_val:.4f}")

abundance_loc_groups = [merged_df[merged_df['Location'] == loc]['Abundance'] for loc in locations]
f_stat, p_val = stats.f_oneway(*abundance_loc_groups)
print(f"Location effect - F-statistic: {f_stat:.4f}, p-value: {p_val:.4f}")

from statsmodels.stats.multicomp import pairwise_tukeyhsd

# === Tukey HSD for Abundance by Location ===
print("\n=== Tukey HSD for Abundance by Location ===")
tukey_location = pairwise_tukeyhsd(endog=merged_df['Abundance'],
                                   groups=merged_df['Location'],
                                   alpha=0.05)
print(tukey_location)

# === Tukey HSD for Abundance by Season ===
print("\n=== Tukey HSD for Abundance by Season ===")
tukey_season = pairwise_tukeyhsd(endog=merged_df['Abundance'],
                                 groups=merged_df['Season'],
                                 alpha=0.05)
print(tukey_season)

tukey_location.plot_simultaneous()
plt.title("Tukey HSD - Abundance by Location")
plt.xlabel("Abundance")
plt.show()

tukey_season.plot_simultaneous()
plt.title("Tukey HSD - Abundance by Season")
plt.xlabel("Abundance")
plt.show()

# Pivot for heatmap
heatmap_data = merged_df.pivot_table(index='Location', columns='Season', values='Shannon_H', aggfunc='mean')

# Plot
plt.figure(figsize=(10, 6))
sns.heatmap(heatmap_data, annot=True, fmt=".2f", cmap="YlGnBu")
plt.title("Average Shannon Index by Location and Season")
plt.show()

# Pivot table for abundance
abundance_heatmap_data = merged_df.pivot_table(
    index='Location',
    columns='Season',
    values='Abundance',
    aggfunc='mean'
)

# Plot heatmap
plt.figure(figsize=(10, 6))
sns.heatmap(abundance_heatmap_data, annot=True, fmt=".1f", cmap="YlOrRd", linewidths=0.5, linecolor='gray')
plt.title("Average Abundance by Location and Season")
plt.ylabel("Location")
plt.xlabel("Season")
plt.tight_layout()
plt.show()

# Aggregate mean values
agg_df = merged_df.groupby(['Location', 'Season']).agg(
    Shannon_H_mean=('Shannon_H', 'mean'),
    Abundance_mean=('Abundance', 'mean')
).reset_index()

# Pivot to get grid layout
locations = agg_df['Location'].unique()
seasons = agg_df['Season'].unique()
locations.sort()
seasons.sort()

# Plot
plt.figure(figsize=(12, 6))
for i, loc in enumerate(locations):
    for j, season in enumerate(seasons):
        sub = agg_df[(agg_df['Location'] == loc) & (agg_df['Season'] == season)]
        if not sub.empty:
            shannon = sub['Shannon_H_mean'].values[0]
            abundance = sub['Abundance_mean'].values[0]
            plt.scatter(j, i, s=abundance * 10, c=shannon, cmap='coolwarm', edgecolors='k')

# Formatting
plt.xticks(ticks=np.arange(len(seasons)), labels=seasons)
plt.yticks(ticks=np.arange(len(locations)), labels=locations)
plt.xlabel("Season")
plt.ylabel("Location")
plt.title("Overlay: Shannon (color) & Abundance (size)")
plt.colorbar(label="Mean Shannon Index")
plt.grid(True)
plt.tight_layout()
plt.show()

# Annotate each point
for _, row in merged_df.iterrows():
    plt.text(row['Abundance'] + 0.1, row['Shannon_H'], f"{row['Location']} ({row['Season']})", fontsize=8)

plt.xlabel("Abundance (Isolate Count)")
plt.ylabel("Shannon Index (H')")
plt.title("Shannon Diversity vs Abundance\nAnnotated by Location and Season")
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()

import matplotlib.pyplot as plt
from adjustText import adjust_text
import seaborn as sns

plt.figure(figsize=(12, 8))

# Base scatterplot
sns.scatterplot(
    data=merged_df,
    x='Abundance',
    y='Shannon_H',
    hue='Season',
    style='Location',
    palette='tab10',
    s=100
)

# Prepare label annotations
texts = []
for _, row in merged_df.iterrows():
    label = f"{row['Location']} ({row['Season']})"
    texts.append(plt.text(row['Abundance'], row['Shannon_H'], label, fontsize=8))

# Automatically adjust label positions
adjust_text(texts, arrowprops=dict(arrowstyle='-', color='gray', lw=0.5))

# Labels and formatting
plt.xlabel("Abundance (Isolate Count)")
plt.ylabel("Shannon Index (H')")
plt.title("Shannon vs Abundance (Labeled by Location and Season)")
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()
