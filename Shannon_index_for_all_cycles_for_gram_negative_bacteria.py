import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates
from matplotlib.patches import Patch
from datetime import datetime

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

# === Fixed seasonal definitions ===
season_colors = {
    'Winter': '#cce5ff',
    'Spring': '#d4edda',
    'Summer': '#fff3cd',
    'Autumn': '#f8d7da'
}
season_ranges = {
    'Winter':  [('12-01', '02-28')],
    'Spring':  [('03-01', '05-31')],
    'Summer':  [('06-01', '08-31')],
    'Autumn':  [('09-01', '11-30')],
}

# === Build full seasonal span for each year in data ===
min_date = shannon_df['Data'].min()
max_date = shannon_df['Data'].max()
years = list(range(min_date.year - 1, max_date.year + 2))  # +1 year margin for Winter

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

# === Plot ===
plt.figure(figsize=(12, 6))
ax = plt.gca()

# Draw fixed season bands
for season, start, end in season_spans:
    ax.axvspan(start, end, color=season_colors[season], alpha=0.3, zorder=0)

# Plot points
sns.scatterplot(data=shannon_df, x='Data', y='Shannon_H', hue='Location',
                s=100, edgecolor='black', ax=ax)

# === Custom legend ===
handles_loc, labels_loc = ax.get_legend_handles_labels()
season_handles = [
    Patch(facecolor=color, edgecolor='none', alpha=0.3, label=season)
    for season, color in season_colors.items()
]
# Merge and remove duplicate labels
all_handles = handles_loc + season_handles
all_labels = labels_loc + list(season_colors.keys())
ax.legend(all_handles, all_labels, title='Location / Season')

# Format axes
ax.set_title('Shannon Diversity Index over Time (Gram-Negative Bacteria)')
ax.set_xlabel('Sampling Date')
ax.set_ylabel("Shannon Index (H')")
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.xticks(rotation=45)
ax.grid(True)
plt.tight_layout()
plt.show()
