import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re
import os

# Load data
file_path = '/home/dmytro/Downloads/microbiology_diploma/G-.xlsx'
df = pd.read_excel(file_path, sheet_name='Arkusz1')
df.columns = df.columns.str.strip()

# Remove unwanted rows
df = df[df['Rodzaj/gatunek (po czyszczeniu)'].notna()]
df = df[~df['Rodzaj/gatunek (po czyszczeniu)'].astype(str).str.contains('NNNNN|no significant', case=False, na=False)]

# Normalize medium names
def normalize_podloze(raw):
    if pd.isnull(raw):
        return 'nieznane'
    s = str(raw).lower().replace('.', '').replace('-', ' ').replace(',', ' ')
    if re.search(r'\bcled\b', s): return 'Cled'
    if re.search(r'\bcetr\b', s): return 'Cetr'
    if re.search(r'\bemb\b', s): return 'EMB'
    if re.search(r'\bbec\b', s) or re.search(r'\bb e c\b', s): return 'BEC'
    return 'inne'
df['Podloze'] = df['Podłoże z którego wyhodowano/morfologia kolonii'].apply(normalize_podloze)

# Gram classification
gram_negative_keywords = [
    'Pseudomonas', 'Acinetobacter', 'Enterobacter', 'Klebsiella', 'Serratia',
    'Stenotrophomonas', 'Rahnella', 'Pantoea', 'Escherichia', 'Shigella',
    'Neisseria', 'Salmonella', 'Bacteroides', 'Haemophilus', 'Azotobacter',
    'Erwinia', 'Lelliottia', 'Rhizobium', 'Oligella', 'Comamonas', 'Burkholderia',
    'Sphingomonas', 'Moraxella', 'Shewanella', 'Citrobacter', 'Morganella',
    'Proteus', 'Providencia', 'Yersinia', 'Vibrio', 'Aeromonas', 'Campylobacter',
    'Helicobacter', 'Bordetella', 'Brucella', 'Legionella', 'Francisella',
    'Fusobacterium', 'Porphyromonas', 'Prevotella'
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
    'Priestia', 'Terribacillus', 'Trichococcus'
]
def classify_gram(species_name):
    if pd.isnull(species_name): return 'Nieokreślony'
    species_name_lower = str(species_name).lower()
    if any(k.lower() in species_name_lower for k in gram_negative_keywords): return 'Gram-ujemna'
    if any(k.lower() in species_name_lower for k in gram_positive_keywords): return 'Gram-dodatnia'
    return 'Nieokreślony'
df['Typ Grama'] = df['Rodzaj/gatunek (po czyszczeniu)'].apply(classify_gram)

# Extract genus and species (first two words)
def extract_genus_species(name):
    if pd.isnull(name): return ''
    name = re.sub(r'[\[\]\(\),]', '', str(name))
    words = name.strip().split()
    if len(words) >= 2: return f"{words[0]} {words[1]}"
    elif len(words) == 1: return words[0]
    else: return ''
df['Rodzaj_gatunek'] = df['Rodzaj/gatunek (po czyszczeniu)'].apply(extract_genus_species)

# Colors
gram_colors = {'Gram-ujemna': '#8ecae6', 'Gram-dodatnia': '#888888', 'Nieokreślony': '#e0e0e0'}

def plot_nested_donut(data, cycle):
    # Outer ring: bacteria
    outer_labels = []
    outer_sizes = []
    outer_colors = []

    for podloze, subset in data.groupby('Podloze'):
        species_counts = subset['Rodzaj_gatunek'].value_counts()
        for species, count in species_counts.items():
            outer_labels.append(f"{species}\n({podloze})")
            outer_sizes.append(count)
            gram_type = subset[subset['Rodzaj_gatunek'] == species]['Typ Grama'].iloc[0]
            outer_colors.append(gram_colors.get(gram_type, '#cccccc'))

    total = sum(outer_sizes)
    outer_fracs = np.array(outer_sizes) / total

    # Inner ring: media
    podloza_counts = data['Podloze'].value_counts()
    podloza_names = podloza_counts.index.tolist()
    podloza_sizes = podloza_counts.values
    podloza_fracs = podloza_sizes / podloza_sizes.sum()

    fig, ax = plt.subplots(figsize=(12, 12))

    # Outer ring (bacteria)
    wedges2, _ = ax.pie(
        outer_fracs,
        radius=1.0,
        labels=None,
        labeldistance=1.13,
        wedgeprops=dict(width=0.3, edgecolor='w', alpha=1.0),
        startangle=90,
        colors=outer_colors
    )

    # Inner ring (media) - gray
    wedges1, _ = ax.pie(
        podloza_fracs,
        radius=1.0 - 0.3,
        labels=podloza_names,
        labeldistance=0.6,
        wedgeprops=dict(width=0.4, edgecolor='w', alpha=1.0),
        startangle=90,
        colors=['#cccccc'] * len(podloza_names)
    )

    # Add percent labels to outer ring
    angle = 90
    for i, (frac, label) in enumerate(zip(outer_fracs, outer_labels)):
        theta = (angle - frac * 360 / 2)
        angle -= frac * 360
        x = np.cos(np.deg2rad(theta)) * 1.18
        y = np.sin(np.deg2rad(theta)) * 1.18
        percent = f"{frac*100:.1f}%"
        if frac > 0.03:  # only for larger sectors
            ax.text(x, y, f"{label}\n{percent}", ha='center', va='center', fontsize=10, color='black')

    # Legend
    legend_labels = [
        plt.Line2D([0], [0], marker='o', color='w', label='Gram-negative', markerfacecolor=gram_colors['Gram-ujemna'], markersize=15),
        plt.Line2D([0], [0], marker='o', color='w', label='Gram-positive', markerfacecolor=gram_colors['Gram-dodatnia'], markersize=15)
    ]
    ax.legend(handles=legend_labels, loc='upper left', bbox_to_anchor=(1, 1.05), fontsize=13)
    ax.set(aspect="equal", title=f"Cycle {cycle}: bacteria (outer, color = Gram type) and media (inner, gray)")
    plt.tight_layout()
    plt.show()


# Plot for each cycle
for cycle in sorted(df['Pobór'].unique()):
    data_cycle = df[df['Pobór'] == cycle]
    plot_nested_donut(data_cycle, cycle)
