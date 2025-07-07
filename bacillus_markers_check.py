
import pandas as pd
import matplotlib.pyplot as plt
import re
from collections import defaultdict

# === Load data ===
file_path = 'Wyniki_powietrze-3.xlsx'
sheet_name = 'Powietrze zewnątrz-G(+)'
df = pd.read_excel(file_path, sheet_name=sheet_name)
df.columns = df.columns.str.strip()

# === Marker-to-species expectations ===
marker_expected = {
    'BTJH': ['thuringiensis'],
    'BCGSH': ['wiedmannii', 'bombysepticus', 'cytotoxicus', 'mobilis',
              'toyonensis', 'bingmayongensis', 'clarus', 'luti',
              'tropicus', 'pseudomycoides'],
    'BASH': ['anthracis'],
    'BCJH': ['cereus'],
    'BMSH': ['mycoides']
}

# === Reverse species -> marker lookup ===
species_to_marker = {}
for marker, species_list in marker_expected.items():
    for s in species_list:
        species_to_marker[s.lower()] = marker

# === Clean ===
df = df[df['Rodzaj/gatunek'].notna()]
df['Rodzaj/gatunek'] = df['Rodzaj/gatunek'].astype(str)

marker_results = []
detailed_hits = []

# === Classify results per marker ===
for marker, expected_species in marker_expected.items():
    if marker not in df.columns:
        continue

    detected = df[df[marker].notna()]
    correct = 0
    correlated = 0
    unexpected = 0

    for _, row in detected.iterrows():
        raw_species = str(row['Rodzaj/gatunek']).strip().lower()
        match = re.search(r"\b\w+\s+(\w+)", raw_species)
        species_name = match.group(1).lower() if match else raw_species.split()[-1]

        if species_name in [s.lower() for s in expected_species]:
            match_type = "✅ Correct"
            correct += 1
        elif species_name in species_to_marker and species_to_marker[species_name] != marker:
            match_type = f"⚠️ Correlated ({species_to_marker[species_name]})"
            correlated += 1
        elif "bacillus" in raw_species:
            match_type = "❌ Unexpected Bacillus"
            unexpected += 1
        else:
            match_type = "❓ Other"
            unexpected += 1

        detailed_hits.append({
            'Marker': marker,
            'Detected Species': row['Rodzaj/gatunek'],
            'Species ID': species_name,
            'Match Type': match_type,
            'Sample': row['Miejsce poboru'],
            'Method': row['Metoda identyfikacji']
        })

    marker_results.append({
        'Marker': marker,
        'Detected': len(detected),
        'Correct': correct,
        'Correlated': correlated,
        'Unexpected': unexpected
    })

# === Create summary DataFrame ===
summary_df = pd.DataFrame(marker_results)
print("\n=== Marker Summary ===")
print(summary_df)

# === Create detailed match DataFrame ===
detailed_df = pd.DataFrame(detailed_hits)
print("\n=== Detailed Matches ===")
print(detailed_df[['Marker', 'Detected Species', 'Match Type', 'Sample', 'Method']])

# === Plot bar chart per marker ===
match_types = ['Correct', 'Correlated', 'Unexpected']
colors = ['green', 'orange', 'red']
labels = ['Correct', 'Correlated', 'Unexpected']

fig, ax = plt.subplots(figsize=(10, 6))
bar_data = {
    'Marker': [],
    'Match Type': [],
    'Count': []
}

for row in summary_df.itertuples():
    for mtype in match_types:
        bar_data['Marker'].append(row.Marker)
        bar_data['Match Type'].append(mtype)
        bar_data['Count'].append(getattr(row, mtype))

bar_df = pd.DataFrame(bar_data)

# Plot
for i, (mtype, label) in enumerate(zip(match_types, labels)):
    subset = bar_df[bar_df['Match Type'] == mtype]
    ax.bar(subset['Marker'], subset['Count'], label=label,
           bottom=bar_df[bar_df['Match Type'].isin(match_types[:i])].groupby('Marker')['Count'].sum().reindex(subset['Marker']).fillna(0).values,
           color=colors[i])

ax.set_title("PCR Marker Match Types")
ax.set_ylabel("Number of Matches")
ax.set_xlabel("PCR Marker")
ax.legend(title="Match Type")
plt.tight_layout()
plt.grid(True, axis='y')
plt.show()