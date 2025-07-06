import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# === Load data ===
file_path = 'Wyniki_powietrze-3.xlsx'
sheet_name = 'Powietrze zewnątrz-G(-)'
df = pd.read_excel(file_path, sheet_name=sheet_name)

# === Coliform-related genera keywords ===
coli_keywords = ['Pantoea', 'Enterobacter', 'Klebsiella', 'Citrobacter', 'Erwinia',
                 'Moellerella', 'Leclercia', 'Kluyvera', 'Buttiauxella']

# === Pseudomonas-related genera keywords ===
pseudomonas_keywords = ['Pseudomonas']

# === Filter for coliform-related bacteria ===
df_coli = df[df['Rodzaj/gatunek'].astype(str).str.contains('|'.join(coli_keywords), case=False, na=False)].copy()

# === Filter for Pseudomonas-related bacteria ===
df_pseudomonas = df[df['Rodzaj/gatunek'].astype(str).str.contains('|'.join(pseudomonas_keywords), case=False, na=False)].copy()

# === Standardize sampling method ===
def detect_method(text):
    text = str(text).lower()
    if 'hodowla' in text:
        return 'Liquid BHI'
    elif 'płuczka' in text:
        return 'Scrubber'
    elif 'sedymentacja' in text:
        return 'Sedimentation'
    else:
        return 'Other'

df_coli['Method'] = df_coli['Metoda poboru'].apply(detect_method)
df_pseudomonas['Method'] = df_pseudomonas['Metoda poboru'].apply(detect_method)

# === Create location-method combinations ===
method_list = ['Sedimentation', 'Scrubber', 'Liquid BHI']
locations = sorted(df['Miejsce poboru'].dropna().unique())
combinations = pd.MultiIndex.from_product([locations, method_list], names=['Miejsce poboru', 'Method'])

# === Shannon Diversity Index function ===
def calculate_shannon(series):
    counts = series.value_counts()
    proportions = counts / counts.sum()
    return -(proportions * np.log(proportions)).sum()

# === Create summary table for Coliforms ===
summary_coli = df_coli.groupby(['Miejsce poboru', 'Method']).agg(
    Sample_count=('Rodzaj/gatunek', 'count'),
    Diversity=('Rodzaj/gatunek', pd.Series.nunique),
    Shannon_H=('Rodzaj/gatunek', calculate_shannon)
).reindex(combinations, fill_value=0).reset_index()

summary_coli.rename(columns={'Miejsce poboru': 'Location'}, inplace=True)

# === Create summary table for Pseudomonas ===
summary_pseudomonas = df_pseudomonas.groupby(['Miejsce poboru', 'Method']).agg(
    Sample_count=('Rodzaj/gatunek', 'count'),
    Diversity=('Rodzaj/gatunek', pd.Series.nunique),
    Shannon_H=('Rodzaj/gatunek', calculate_shannon)
).reindex(combinations, fill_value=0).reset_index()

summary_pseudomonas.rename(columns={'Miejsce poboru': 'Location'}, inplace=True)

# === Fixed method colors ===
method_colors = {
    'Sedimentation': 'steelblue',
    'Scrubber': 'forestgreen',
    'Liquid BHI': 'gold'
}

# === Plotting function ===
def plot_grouped_bar(df, value_column, title, ylabel):
    x = np.arange(len(locations))  # base x positions
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 6))

    for i, method in enumerate(method_list):
        values = df[df['Method'] == method][value_column].values
        ax.bar(x + i * width, values, width, label=method, color=method_colors[method])

    ax.set_xticks(x + width)
    ax.set_xticklabels(locations, rotation=45)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(title='Sampling method')
    plt.tight_layout()
    plt.show()

# === Draw Coliforms charts ===
plot_grouped_bar(summary_coli, 'Sample_count',
                 'Number of coliform bacteria samples by location and sampling method',
                 'Number of isolates')

plot_grouped_bar(summary_coli, 'Diversity',
                 'Diversity of coliform bacteria by location and sampling method',
                 'Unique genera/species')

plot_grouped_bar(summary_coli, 'Shannon_H',
                 'Shannon diversity index (H\') of coliform bacteria by location and sampling method',
                 'H\'')

# === Draw Pseudomonas charts ===
plot_grouped_bar(summary_pseudomonas, 'Sample_count',
                 'Number of Pseudomonas bacteria samples by location and sampling method',
                 'Number of isolates')

plot_grouped_bar(summary_pseudomonas, 'Diversity',
                 'Diversity of Pseudomonas bacteria by location and sampling method',
                 'Unique genera/species')

plot_grouped_bar(summary_pseudomonas, 'Shannon_H',
                 'Shannon diversity index (H\') of Pseudomonas bacteria by location and sampling method',
                 'H\'')

def plot_shannon_heatmap(df, title):
    heatmap_data = df.pivot(index='Location', columns='Method', values='Shannon_H')

    plt.figure(figsize=(10, 6))
    sns.heatmap(heatmap_data, annot=True, fmt=".2f", cmap='viridis', cbar_kws={'label': "Shannon Diversity Index (H')"})
    plt.title(title)
    plt.ylabel('Sampling Location')
    plt.xlabel('Sampling Method')
    plt.tight_layout()
    plt.show()

summary_coli['Shannon_H'] = summary_coli['Shannon_H'].replace(-0.0, 0.0)
summary_pseudomonas['Shannon_H'] = summary_pseudomonas['Shannon_H'].replace(-0.0, 0.0)

# Heatmapy Shannon Diversity Index
plot_shannon_heatmap(summary_coli, "Shannon Diversity Index Heatmap for Coliform Bacteria")
plot_shannon_heatmap(summary_pseudomonas, "Shannon Diversity Index Heatmap for Pseudomonas Bacteria")

