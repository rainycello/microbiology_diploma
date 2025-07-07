import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.lines as mlines
from adjustText import adjust_text
import re
from collections import Counter

# === Load data ===
file_path = 'Wyniki_powietrze-3.xlsx'
sheet_name = 'Powietrze zewnątrz-G(+)'
df = pd.read_excel(file_path, sheet_name=sheet_name)

# === Clean and prepare ===
df.columns = df.columns.str.strip()
df['Pobór'] = df['Pobór'].astype(str)

# Map Roman numerals to numeric for sorting
roman_map = {'I':1, 'II':2, 'III':3, 'IV':4, 'V':5, 'VI':6, 'VII':7, 'VIII':8,
             'IX':9, 'X':10, 'XI':11, 'XII':12, 'XIII':13, 'XIV':14, 'XV':15}
df['Pobór_num'] = df['Pobór'].map(roman_map)
df = df[df['Pobór_num'].notna()]
df = df.sort_values('Pobór_num')
cycles_sorted = sorted(df['Pobór'].unique(), key=lambda x: roman_map.get(x, 0))
df['Pobór'] = pd.Categorical(df['Pobór'], categories=cycles_sorted, ordered=True)

# === Define bacteria groups ===
specific_bacteria = {
    'Enterococcus': ['Enterococcus'],
    'B. anthracis': ['anthracis'],
    'B. cereus': ['cereus'],
    'B. thuringiensis': ['thuringiensis'],
    'B. mycoides': ['mycoides'],
    'B. cereus group': ['wiedmannii', 'bombysepticus', 'cytotoxicus', 'bingmayongensis', 'pseudomycoides'],
    'nuc': ['nuc'],
    'mecA': ['mecA']
}

# === Build results ===
results = []
for label, keywords in specific_bacteria.items():
    for cycle in cycles_sorted:
        df_cycle = df[df['Pobór'] == cycle]

        if label in ['mecA', 'nuc']:
            found = df_cycle[df_cycle[label].astype(str).str.contains(label, case=False, na=False)]
        elif label == 'B. cereus group':
            group_exclusive = set(keywords) - set(
                specific_bacteria['B. anthracis'] + specific_bacteria['B. cereus'] +
                specific_bacteria['B. thuringiensis'] + specific_bacteria['B. mycoides']
            )
            pattern = '|'.join(group_exclusive)
            found = df_cycle[df_cycle['Rodzaj/gatunek'].astype(str).str.contains(pattern, case=False, na=False)]
        else:
            pattern = '|'.join(keywords)
            found = df_cycle[df_cycle['Rodzaj/gatunek'].astype(str).str.contains(pattern, case=False, na=False)]

        count = len(found)

        if count > 0:
            records = []
            for _, row in found.iterrows():
                kind = label
                if label in ['mecA', 'nuc'] and pd.notna(row['Rodzaj/gatunek']):
                    kind += f" / {row['Rodzaj/gatunek']}"
                elif label == 'B. cereus group':
                    kind += f" / {row['Rodzaj/gatunek']}"
                elif 'Api' in str(row['Metoda identyfikacji']):
                    kind += f" / {row['Rodzaj/gatunek']}"
                record = f"{kind} / {row['Miejsce poboru']} / {row['Metoda identyfikacji']}"
                records.append(record)

            counted = Counter(records)
            label_texts = [f"{text} x{counted[text]}" if counted[text] > 1 else text for text in sorted(counted)]
        else:
            label_texts = ['']

        results.append({
            'Bacteria': label,
            'Cycle': cycle,
            'Count': count,
            'Labels': label_texts
        })

plot_df = pd.DataFrame(results)

# === Plot each bacteria group ===
groups = {
    'Enterococcus': ['Enterococcus'],
    'Bacillus': ['B. anthracis', 'B. cereus', 'B. thuringiensis', 'B. mycoides', 'B. cereus group'],
    'nuc & mecA': ['nuc', 'mecA']
}

for group_name, group_labels in groups.items():
    subset = plot_df[plot_df['Bacteria'].isin(group_labels)]

    fig, ax = plt.subplots(figsize=(14, 6))

    texts = []
    for label in group_labels:
        label_df = subset[subset['Bacteria'] == label]
        x = label_df['Cycle']
        y = label_df['Count']
        ax.plot(x, y, marker='o', label=label)

        for i, row in label_df.iterrows():
            for idx, label_text in enumerate(row['Labels']):
                if label_text.strip():
                    # offset labels vertically to reduce overlapping
                    texts.append(ax.text(row['Cycle'], row['Count'] + 0.1 + idx * 0.1, label_text, fontsize=7))

    adjust_text(texts, arrowprops=dict(arrowstyle='-', color='gray', lw=0.5), force_text=1.2, force_points=0.3, expand_text=(1.2, 1.5), expand_points=(1.5, 2))
    ax.set_title(f"{group_name} across cycles")
    ax.set_xlabel("Cycle")
    ax.set_ylabel("Isolate Count")
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
