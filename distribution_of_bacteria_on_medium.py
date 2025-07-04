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
