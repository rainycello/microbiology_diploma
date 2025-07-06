import pandas as pd
import os
import re
import plotly.express as px

# Load data
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'G-.xlsx')
df = pd.read_excel(file_path, sheet_name='Arkusz1')
df.columns = df.columns.str.strip()

# Filter
df = df[df['Rodzaj/gatunek (po czyszczeniu)'].notna()]
df = df[~df['Rodzaj/gatunek (po czyszczeniu)'].astype(str).str.contains('NNNNN|no significant', case=False, na=False)]

# Normalize medium names
def normalize_podloze(raw):
    if pd.isnull(raw): return 'nieznane'
    s = str(raw).lower()
    if 'cled' in s: return 'Cled'
    elif 'cetr' in s: return 'Cetr'
    elif 'emb' in s: return 'EMB'
    elif 'b.e.c' in s or 'bec' in s: return 'BEC'
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

# Group by medium and genus
grouped = df.groupby(['Podloze', 'Rodzaj']).size().reset_index(name='count')

# Generate donut chart for each medium
for medium in grouped['Podloze'].unique():
    data = grouped[grouped['Podloze'] == medium].copy()
    total = data['count'].sum()
    data['percent'] = (data['count'] / total * 100).round(3)
    data['label'] = data.apply(lambda row: f"{row['Rodzaj']} ({row['percent']}%)", axis=1)

    # Create figure using Rodzaj as name (to keep clean legend)
    fig = px.pie(
        data,
        names='Rodzaj',
        values='count',
        title=f"Bacteria on medium: {medium}",
        hole=0.3
    )

    # Update text inside the donut only to show percent in parentheses
    fig.update_traces(
        text=data['percent'].astype(str) + '%',
        textposition='inside',
        hovertemplate='%{label} (%{percent})<extra></extra>',
        textinfo='text'  # Only show custom text, not default label
    )

    # Display with 2 decimal places in both the text and hovertemplate
    data['percent_str'] = data['percent'].map(lambda x: f"{x:.2f}%")

    fig.update_traces(
        text=data['percent_str'],
        textposition='inside',
        hovertemplate='%{label} (%{percent:.2f}%)<extra></extra>',
        textinfo='text'
    )

    # Keep the legend readable (Rodzaj only)
    fig.update_layout(
        margin=dict(t=50, b=0, l=0, r=0),
        showlegend=True
    )

    fig.show()

target_bacteria = {
    'Cetr': ['Pseudomonas'],
    'EMB': ['Klebsiella'],
    'BEC': ['Pantoea', 'Enterobacter', 'Klebsiella', 'Citrobacter', 'Erwinia',
            'Moellerella', 'Leclercia', 'Kluyvera', 'Buttiauxella']
}

from scipy.stats import chi2_contingency

# Kontenery na wyniki
results = []

# Analiza dla każdego podłoża zdefiniowanego w `target_bacteria`
for medium, targets in target_bacteria.items():
    medium_df = df[df['Podloze'] == medium].copy()

    # Liczba targetowych bakterii
    target_count = medium_df['Rodzaj'].isin(targets).sum()
    other_count = len(medium_df) - target_count

    # Porównanie do reszty danych (inne podłoża)
    other_df = df[df['Podloze'] != medium].copy()
    other_target_count = other_df['Rodzaj'].isin(targets).sum()
    other_non_target_count = len(other_df) - other_target_count

    # Tabela kontyngencji
    contingency_table = [
        [target_count, other_count],
        [other_target_count, other_non_target_count]
    ]

    # Test chi-kwadrat
    chi2, p, dof, expected = chi2_contingency(contingency_table)

    # Zapisz wynik
    results.append({
        'Podloze': medium,
        'Target genus': ', '.join(targets),
        'On medium (target)': target_count,
        'On medium (non-target)': other_count,
        'Other media (target)': other_target_count,
        'Other media (non-target)': other_non_target_count,
        'Chi2': round(chi2, 3),
        'p-value': round(p, 4),
        'Significant (p<0.05)': p < 0.05
    })

# Wyniki jako DataFrame
spec_df = pd.DataFrame(results)
print(spec_df)

import seaborn as sns
import matplotlib.pyplot as plt

# Czy target czy nie
df['Czy_target'] = df.apply(lambda row: row['Rodzaj'] in target_bacteria.get(row['Podloze'], []), axis=1)

# Policz odsetki targetów na podłożach
plot_df = df.groupby(['Podloze', 'Czy_target']).size().reset_index(name='count')
plot_df = plot_df.pivot(index='Podloze', columns='Czy_target', values='count').fillna(0)
plot_df['target_frac'] = plot_df[True] / (plot_df[True] + plot_df[False])

plot_df['target_frac'].plot(kind='bar', title='Odsetek targetowych bakterii na danym podłożu', ylabel='Frakcja targetów', xlabel='Podłoże')
plt.axhline(0.5, linestyle='--', color='gray', label='50% próg')
plt.legend()
plt.tight_layout()
plt.show()
