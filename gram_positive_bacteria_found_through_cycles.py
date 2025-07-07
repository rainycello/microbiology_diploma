import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# === Load the data ===
file_path = 'Wyniki_powietrze-3.xlsx'
sheet_name = 'Powietrze zewnątrz-G(+)'
df = pd.read_excel(file_path, sheet_name=sheet_name)
df.columns = df.columns.str.strip()

# === Define specific groups ===
exact_species = {
    'anthracis': 'B. anthracis',
    'cereus': 'B. cereus',
    'mycoides': 'B. mycoides',
    'thuringiensis': 'B. thuringiensis'
}

cereus_group_other = [
    'wiedmannii', 'toyonensis', 'bombysepticus', 'weihenstephanensis',
    'cytotoxicus', 'psuedoanthracis', 'bingmayongensis', 'clarus'
]

# === Classification function ===
def classify_target(row):
    species = str(row.get('Rodzaj/gatunek', '')).lower()
    genes = f"{row.get('mecA', '')} {row.get('nuc', '')}".lower()

    # Check for gene presence
    if 'meca' in genes:
        return 'mecA'
    if 'nuc' in genes:
        return 'nuc'

    # Exact matches for main Bacillus
    for key, label in exact_species.items():
        if key in species:
            return label

    # Group Bacillus cereus complex (rest)
    for keyword in cereus_group_other:
        if keyword in species:
            return 'B. cereus group (other)'

    # Enterococcus
    if 'enterococcus' in species:
        return 'Enterococcus'

    return None

# === Apply classification ===
df['TargetClass'] = df.apply(classify_target, axis=1)
df = df[df['TargetClass'].notna()]  # Keep only matching rows

# === Rename for clarity ===
df.rename(columns={
    'Miejsce poboru': 'Location',
    'Pobór': 'Cycle',
    'Metoda identyfikacji': 'ID_method'
}, inplace=True)

# === Group and count ===
summary = df.groupby(['Location', 'Cycle', 'ID_method', 'TargetClass']).size().reset_index(name='Count')

# === Pivot for heatmaps ===
pivot_table = summary.pivot_table(index=['Location', 'Cycle', 'ID_method'],
                                   columns='TargetClass', values='Count', fill_value=0).reset_index()

# === Melt for bubble plot ===
melted = summary.copy()
total_counts = melted.groupby(['Location', 'Cycle', 'ID_method'])['Count'].sum().reset_index(name='Total')
merged = pd.merge(melted, total_counts, on=['Location', 'Cycle', 'ID_method'])
merged['Fraction'] = merged['Count'] / merged['Total']

# === Bubble Plot ===
sns.set(style='whitegrid')
g = sns.FacetGrid(merged, col='TargetClass', col_wrap=3, height=5, sharex=False, sharey=False)
g.map_dataframe(sns.scatterplot,
                x='Cycle', y='Location',
                size='Count', hue='ID_method',
                sizes=(50, 500), alpha=0.8)
g.add_legend()
g.fig.suptitle('Distribution of Gram-positive Targets by Type, Location, and Cycle', y=1.02)
plt.tight_layout()
plt.show()

# === Heatmaps ===
target_classes = merged['TargetClass'].unique()

for target in target_classes:
    sub = summary[summary['TargetClass'] == target]
    heat = sub.pivot_table(index='Location', columns='Cycle', values='Count', fill_value=0)
    plt.figure(figsize=(10, 6))
    sns.heatmap(heat, annot=True, fmt='d', cmap='YlOrBr')
    plt.title(f'Heatmap of {target} Count by Location and Cycle')
    plt.ylabel('Location')
    plt.xlabel('Cycle')
    plt.tight_layout()
    plt.show()
