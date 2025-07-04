import pandas as pd
import plotly.express as px
import os
import re

# Set up paths
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'G-.xlsx')

# Load and clean data
df = pd.read_excel(file_path, sheet_name='Arkusz1')
df.columns = df.columns.str.strip()
df = df[df['Rodzaj/gatunek (po czyszczeniu)'].notna()]
df = df[~df['Rodzaj/gatunek (po czyszczeniu)'].astype(str).str.contains('NNNNN|no significant', case=False, na=False)]


# Normalize media names
def normalize_podloze(raw):
    if pd.isnull(raw): return 'nieznane'
    s = str(raw).lower()
    if 'cled' in s:
        return 'Cled'
    elif 'cetr' in s:
        return 'Cetr'
    elif 'emb' in s:
        return 'EMB'
    elif 'b.e.c' in s or 'bec' in s:
        return 'BEC'
    return 'inne'


df['Podloze'] = df['Podłoże z którego wyhodowano/morfologia kolonii'].apply(normalize_podloze)


# Extract genus
def extract_genus(name):
    if pd.isnull(name): return ''
    name = re.sub(r'[\[\]\(\)]', '', str(name))
    name = re.sub(r'^[Aa]\s+', '', name)
    name = name.strip().split('/')[0]
    return name.split()[0] if name else ''


df['Rodzaj'] = df['Rodzaj/gatunek (po czyszczeniu)'].apply(extract_genus)

# Classify Gram
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
    if not genus:
        return 'Unidentified by 16S sequencing'
    g = genus.lower()
    if any(k.lower() == g for k in gram_negative_keywords):
        return 'Gram-ujemna'
    if any(k.lower() == g for k in gram_positive_keywords):
        return 'Gram-dodatnia'
    return 'Unidentified by 16S sequencing'


df['Typ Grama'] = df['Rodzaj'].apply(classify_gram)

# Color map for Gram types
gram_colors = {
    'Gram-ujemna': '#8ecae6',  # Blue for Gram-negative
    'Gram-dodatnia': '#888888',  # Dark gray for Gram-positive
    'Unidentified by 16S sequencing': '#e0e0e0'  # Light gray for unidentified
}

# Add localization layer from 'Miejsce_poboru'
df['Localization'] = df['Miejsce_poboru'].fillna('Unknown')

# Build enhanced sunburst per cycle with localization
for cycle in sorted(df['Pobór'].dropna().unique()):
    df_cycle = df[df['Pobór'] == cycle].copy()

    # Group and count
    counts = df_cycle.groupby(['Localization', 'Podloze', 'Rodzaj', 'Typ Grama']).size().reset_index(name='count')

    # Add % for localisation and podloze
    total = counts['count'].sum()
    counts['percent'] = (counts['count'] / total * 100).round(1)

    # Label for Rodzaj (Genus)
    counts['Rodzaj_label'] = counts.apply(
        lambda row: f"{row['Rodzaj']} ({row['Podloze']}) – {row['percent']}%" if row['Rodzaj'] else 'Unidentified',
        axis=1
    )

    # Set a uniform color for localisation and podloze (we'll choose a neutral gray)
    podloze_localization_colors = {
        'Podloze': '#d3d3d3',  # Gray color for Podloze
        'Localization': '#d3d3d3',  # Same gray for localization
    }

    # Build sunburst chart with localization and podloze layers
    fig = px.sunburst(
        counts,
        path=['Localization', 'Podloze', 'Rodzaj_label'],
        values='count',
        color='Typ Grama',
        color_discrete_map=gram_colors,
        title=f'Sunburst – Bacteria, Medium and Localisation (Cycle {cycle})'
    )

    # Set gray color for localization and podloze
    fig.update_traces(marker=dict(colorscale=[[0, podloze_localization_colors['Localization']]]))

    fig.update_layout(margin=dict(t=50, l=0, r=0, b=0))
    fig.show()
