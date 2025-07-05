import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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
df_coli = df[df['Rodzaj/gatunek'].astype(str).str.contains('|'.join(coli_keywords), case=False, na=False)]

# === Filter for Pseudomonas-related bacteria ===
df_pseudomonas = df[df['Rodzaj/gatunek'].astype(str).str.contains('|'.join(pseudomonas_keywords), case=False, na=False)]

# === Standardize sampling method ===
def detect_method(text):
    text = str(text).lower()
    if 'hodowla' in text:
        return 'Culture'
    elif 'płuczka' in text:
        return 'Rinse'
    elif 'sedymentacja' in text:
        return 'Sedimentation'
    else:
        return 'Other'

df_coli['Method'] = df_coli['Metoda poboru'].apply(detect_method)
df_pseudomonas['Method'] = df_pseudomonas['Metoda poboru'].apply(detect_method)

# === Create summary table for Coliforms with zero-fill ===
method_list = ['Sedimentation', 'Rinse', 'Culture']
locations = sorted(df['Miejsce poboru'].dropna().unique())

combinations = pd.MultiIndex.from_product([locations, method_list], names=['Sampling site', 'Method'])
summary_coli = df_coli.groupby(['Miejsce poboru', 'Method']).agg(
    Sample_count=('Rodzaj/gatunek', 'count'),
    Diversity=('Rodzaj/gatunek', pd.Series.nunique)
).reindex(combinations, fill_value=0).reset_index()

summary_coli.rename(columns={'Sampling site': 'Location'}, inplace=True)

# === Create summary table for Pseudomonas with zero-fill ===
summary_pseudomonas = df_pseudomonas.groupby(['Miejsce poboru', 'Method']).agg(
    Sample_count=('Rodzaj/gatunek', 'count'),
    Diversity=('Rodzaj/gatunek', pd.Series.nunique)
).reindex(combinations, fill_value=0).reset_index()

summary_pseudomonas.rename(columns={'Sampling site': 'Location'}, inplace=True)

# === Fixed method colors ===
method_colors = {
    'Sedimentation': 'steelblue',
    'Rinse': 'forestgreen',
    'Culture': 'gold'
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

# === Draw both Coliforms and Pseudomonas charts ===
# Coliforms charts
plot_grouped_bar(summary_coli, 'Sample_count',
                 'Number of coliform bacteria samples by location and sampling method',
                 'Number of isolates')

plot_grouped_bar(summary_coli, 'Diversity',
                 'Diversity of coliform bacteria by location and sampling method',
                 'Unique genera/species')

# Pseudomonas charts
plot_grouped_bar(summary_pseudomonas, 'Sample_count',
                 'Number of Pseudomonas bacteria samples by location and sampling method',
                 'Number of isolates')

plot_grouped_bar(summary_pseudomonas, 'Diversity',
                 'Diversity of Pseudomonas bacteria by location and sampling method',
                 'Unique genera/species')
