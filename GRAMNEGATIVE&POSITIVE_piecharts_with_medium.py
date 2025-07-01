import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re
from matplotlib.patches import Patch

# Load data
file_path = '/home/dmytro/Downloads/microbiology_diploma/G-.xlsx'
df = pd.read_excel(file_path, sheet_name='Arkusz1')
df.columns = df.columns.str.strip()

# Remove unwanted rows
df = df[df['Rodzaj/gatunek (po czyszczeniu)'].notna()]
df = df[~df['Rodzaj/gatunek (po czyszczeniu)'].astype(str).str.contains('NNNNN|no significant', case=False, na=False)]

# Normalize medium names: keep only base medium ignoring colors/details
def normalize_podloze(raw):
    if pd.isnull(raw):
        return 'nieznane'
    s = str(raw).lower()
    if 'cled' in s:
        return 'Cled'
    elif 'cetr' in s:
        return 'Cetr'
    elif 'emb' in s:
        return 'EMB'
    elif 'b.e.c' in s or 'bec' in s:
        return 'BEC'
    else:
        return 'inne'

df['Podloze'] = df['Podłoże z którego wyhodowano/morfologia kolonii'].apply(normalize_podloze)

# Extract genus only (ignore species)
def extract_genus(name):
    if pd.isnull(name):
        return ''
    # Remove brackets, parentheses, prefixes like 'A ', and extra whitespace
    name = re.sub(r'[\[\]\(\)]', '', str(name))
    name = re.sub(r'^[Aa]\s+', '', name)
    name = name.strip()
    # If multiple taxa separated by '/', take the first
    name = name.split('/')[0]
    genus = name.split()[0] if len(name.split()) > 0 else ''
    return genus

df['Rodzaj'] = df['Rodzaj/gatunek (po czyszczeniu)'].apply(extract_genus)

# Gram classification keywords
gram_negative_keywords = [
    'Pseudomonas', 'Acinetobacter', 'Enterobacter', 'Klebsiella', 'Serratia',
    'Stenotrophomonas', 'Rahnella', 'Pantoea', 'Escherichia', 'Shigella',
    'Neisseria', 'Salmonella', 'Bacteroides', 'Haemophilus', 'Azotobacter',
    'Erwinia', 'Lelliottia', 'Rhizobium', 'Oligella', 'Comamonas', 'Burkholderia',
    'Sphingomonas', 'Moraxella', 'Shewanella', 'Citrobacter', 'Morganella',
    'Proteus', 'Providencia', 'Yersinia', 'Vibrio', 'Aeromonas', 'Campylobacter',
    'Helicobacter', 'Bordetella', 'Brucella', 'Legionella', 'Francisella',
    'Fusobacterium', 'Porphyromonas', 'Prevotella', 'Stutzerimonas', 'Kluyvera',
    'Buttiauxella', 'Leclercia', 'Psychrobacter', 'Enterobacteriaceae', 'Moellerella'
]
gram_positive_keywords = [
    'Staphylococcus', 'Streptococcus', 'Bacillus', 'Clostridium', 'Listeria',
    'Corynebacterium', 'Enterococcus', 'Micrococcus', 'Arthrobacter', 'Kocuria',
    'Mycobacterium', 'Paenibacillus', 'Streptomyces', 'Rhodococcus',
    'Actinomyces', 'Nocardia', 'Propionibacterium', 'Bifidobacterium',
    'Lactobacillus', 'Cutibacterium', 'Trueperella', 'Rothia', 'Aerococcus',
    'Tsukamurella', 'Gordonia', 'Dermatophilus', 'Brevibacterium',
    'Cellulomonas', 'Curtobacterium', 'Exiguobacterium', 'Geobacillus',
    'Lysinibacillus', 'Planococcus', 'Sporosarcina', 'Rossellomorea',
    'Priestia', 'Terribacillus', 'Trichococcus', 'Mesobacillus', 'Microbacterium',
    'Okibacterium'
]

def classify_gram(genus):
    if not genus or genus == '':
        return 'Unidentified by 16S sequencing'
    genus_lower = genus.lower()
    if any(k.lower() == genus_lower for k in gram_negative_keywords):
        return 'Gram-ujemna'
    if any(k.lower() == genus_lower for k in gram_positive_keywords):
        return 'Gram-dodatnia'
    return 'Unidentified by 16S sequencing'

df['Typ Grama'] = df['Rodzaj'].apply(classify_gram)

# Color definitions for Gram types
gram_colors = {
    'Gram-ujemna': '#8ecae6',        # light blue
    'Gram-dodatnia': '#888888',      # gray
    'Unidentified by 16S sequencing': '#e0e0e0'  # light gray
}

# Plot nested donut chart: inner = medium, outer = genus colored by Gram
def plot_nested_donut(data, cycle):
    # Aggregate counts by medium and genus
    grouped = data.groupby(['Podloze', 'Rodzaj']).size().reset_index(name='count')

    # Inner ring data: medium counts
    podloza_counts = data['Podloze'].value_counts()
    podloza_names = podloza_counts.index.tolist()
    podloza_sizes = podloza_counts.values
    podloza_fracs = podloza_sizes / podloza_sizes.sum()

    # Outer ring data: genus counts within each medium
    outer_sizes = grouped['count'].values
    # Label with genus + medium on outer ring
    outer_labels = [f"{row['Rodzaj']}\n({row['Podloze']})" if row['Rodzaj'] else 'Unidentified' for _, row in grouped.iterrows()]
    outer_colors = [gram_colors.get(classify_gram(row['Rodzaj']), '#cccccc') for _, row in grouped.iterrows()]

    total = outer_sizes.sum()
    if total == 0:
        print(f"No data for cycle {cycle}")
        return

    outer_fracs = outer_sizes / total

    fig, ax = plt.subplots(figsize=(12, 12))

    # Outer ring (genus) with labels and autopct
    wedges2, texts2, autotexts2 = ax.pie(
        outer_fracs,
        radius=1.0,
        labels=outer_labels,
        labeldistance=1.1,
        autopct=lambda pct: f'{pct:.1f}%' if pct > 3 else '',
        pctdistance=0.85,
        wedgeprops=dict(width=0.3, edgecolor='w'),
        startangle=90,
        colors=outer_colors,
        textprops={'fontsize': 9, 'weight': 'bold'}
    )

    # Inner ring (medium) with labels and percentages
    wedges1, texts1, autotexts1 = ax.pie(
        podloza_fracs,
        radius=0.7,
        labels=podloza_names,
        labeldistance=0.6,
        autopct=lambda pct: f'{pct:.1f}%',
        pctdistance=0.4,
        wedgeprops=dict(width=0.3, edgecolor='w'),
        startangle=90,
        textprops={'fontsize': 11, 'weight': 'bold'}
    )

    # Legend for Gram types
    legend_patches = [Patch(color=c, label=l) for l, c in gram_colors.items()]
    ax.legend(handles=legend_patches, title='Gram', loc='upper right', fontsize=12)

    plt.title(f'Wielowarstwowy wykres pierścieniowy - Cykl {cycle}', fontsize=16, weight='bold')
    plt.tight_layout()
    plt.show()

# Plot for each cycle
for cycle in sorted(df['Pobór'].unique()):
    data_cycle = df[df['Pobór'] == cycle]
    plot_nested_donut(data_cycle, cycle)
