import pandas as pd
import os
import re
import plotly.express as px
from scipy.stats import chi2_contingency
import matplotlib.pyplot as plt
import seaborn as sns

# === Load Data ===
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'G-.xlsx')
df = pd.read_excel(file_path, sheet_name='Arkusz1')
df.columns = df.columns.str.strip()

# === Clean and filter ===
df = df[df['Rodzaj/gatunek (po czyszczeniu)'].notna()]
df = df[~df['Rodzaj/gatunek (po czyszczeniu)'].astype(str).str.contains('NNNNN|no significant', case=False, na=False)]

# === Normalize medium names ===
def normalize_medium(raw):
    if pd.isnull(raw): return 'unknown'
    s = str(raw).lower()
    if 'cled' in s:
        return 'Cled'
    elif 'cetr' in s:
        return 'Cetr'
    elif 'emb' in s:
        return 'EMB'
    elif 'b.e.c' in s or 'bec' in s:
        return 'BEC'
#    return 'Other'

df['Medium'] = df['Podłoże z którego wyhodowano/morfologia kolonii'].apply(normalize_medium)

# === Remove Cled ===
df = df[df['Medium'] != 'Cled']

# === Extract Genus ===
def extract_genus(name):
    if pd.isnull(name): return ''
    name = re.sub(r'[\[\]\(\)]', '', str(name))
    name = re.sub(r'^[Aa]\s+', '', name)
    name = name.strip().split('/')[0]
    return name.split()[0] if name else ''

df['Genus'] = df['Rodzaj/gatunek (po czyszczeniu)'].apply(extract_genus)

# === Define target bacteria for each medium ===
target_bacteria = {
    'Cetr': ['Pseudomonas'],
    'EMB': ['Klebsiella'],
    'BEC': ['Pantoea', 'Enterobacter', 'Klebsiella', 'Citrobacter',
            'Erwinia', 'Moellerella', 'Leclercia', 'Kluyvera', 'Buttiauxella']
}

# === Flag whether genus matches target for the medium ===
df['IsTarget'] = df.apply(
    lambda row: row['Genus'] in target_bacteria.get(row['Medium'], []),
    axis=1
)

# === Create summary table for each medium ===
summary = df.groupby(['Medium', 'IsTarget']).size().unstack(fill_value=0)
summary.columns = ['NonTarget', 'Target'] if True in summary.columns else ['NonTarget']
summary = summary.fillna(0)
summary['Total'] = summary.sum(axis=1)
summary['TargetFraction'] = summary.get('Target', 0) / summary['Total']

# === Chi-squared test ===
results = []
for medium in summary.index:
    if 'Target' not in summary.columns:
        continue
    obs = [
        [summary.loc[medium, 'Target'], summary.loc[medium, 'NonTarget']],
        [summary['Target'].sum() - summary.loc[medium, 'Target'],
         summary['NonTarget'].sum() - summary.loc[medium, 'NonTarget']]
    ]
    chi2, p, _, _ = chi2_contingency(obs)
    results.append({
        'Medium': medium,
        'Chi2': chi2,
        'p-value': p,
        'Significant (p<0.05)': p < 0.05
    })

results_df = pd.DataFrame(results)
print("=== Chi-squared test for medium specificity ===")
print(results_df)

# === Bar plot of target fraction ===
plt.figure(figsize=(8, 5))
sns.barplot(data=summary.reset_index(), x='Medium', y='TargetFraction', palette='Set2')
plt.axhline(0.5, linestyle='--', color='gray', label='50% threshold')
plt.ylabel("Fraction of target bacteria")
plt.title("Specificity of media for target genera")
plt.ylim(0, 1)
plt.legend()
plt.tight_layout()
plt.show()
