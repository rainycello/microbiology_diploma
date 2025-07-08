import pandas as pd
import matplotlib.pyplot as plt
from adjustText import adjust_text
from collections import Counter

# === Load data ===
file_path = 'Wyniki_powietrze-3.xlsx'
sheet_name = 'Powietrze zewnątrz-G(+)'
df = pd.read_excel(file_path, sheet_name=sheet_name)
df.columns = df.columns.str.strip()

# === Define proper Roman cycle order ===
roman_order = ['V', 'VI', 'VII', 'VIII', 'IX', 'X']
df = df[df['Pobór'].isin(roman_order)]
df['Pobór'] = pd.Categorical(df['Pobór'], categories=roman_order, ordered=True)
df = df.sort_values('Pobór')

# === Clean and normalize problematic text in 'Rodzaj/gatunek' ===
df['Rodzaj/gatunek'] = (
    df['Rodzaj/gatunek']
    .astype(str)
    .str.strip()
    .str.replace('\u00a0', ' ', regex=False)  # non-breaking space
    .str.replace('\n', ' ', regex=False)
    .str.replace('\r', ' ', regex=False)
    .str.replace('\t', ' ', regex=False)
    .str.replace(' +', ' ', regex=True)
)

# === Prepare keywords ===
specific_bacteria = {
    'Enterococcus': ['Enterococcus'],
    'B. anthracis': ['anthracis'],
    'B. cereus': ['cereus'],
    'B. thuringiensis': ['thuringiensis'],
    'B. mycoides': ['mycoides'],
    'B. cereus group': ['wiedmannii', 'bombysepticus', 'cytotoxicus', 'mobilis',
                        'toyonensis', 'bingmayongensis', 'clarus', 'luti', 'tropicus', 'pseudomycoides'],
    'nuc': [],
    'mecA': []
}

# === Filter non-empty records ===
df = df[df['Rodzaj/gatunek'].notna() | df['mecA'].notna() | df['nuc'].notna()]
df['Pobór'] = df['Pobór'].astype(str)
cycles = roman_order

# === Collect results ===
results = []

for label, keywords in specific_bacteria.items():
    for cycle in cycles:
        df_cycle = df[df['Pobór'] == cycle]

        if label in ['mecA', 'nuc']:
            found = df_cycle[df_cycle[label].astype(str).str.contains(label, case=False, na=False)]

        elif label == 'B. cereus group':
            group_exclusive = set(keywords) - set(
                specific_bacteria['B. anthracis'] +
                specific_bacteria['B. cereus'] +
                specific_bacteria['B. thuringiensis'] +
                specific_bacteria['B. mycoides']
            )
            pattern = '|'.join(group_exclusive)
            found = df_cycle[
                df_cycle['Rodzaj/gatunek']
                .str.lower()
                .str.contains(pattern.lower(), na=False)
            ]

        else:
            pattern = '|'.join(keywords)
            found = df_cycle[
                df_cycle['Rodzaj/gatunek']
                .str.lower()
                .str.contains(pattern.lower(), na=False)
            ]

        desc_list = []
        for _, row in found.iterrows():
            desc = f"{label}: {row['Miejsce poboru']} / {row['Metoda identyfikacji']}"
            if label == 'B. cereus group' or 'api' in str(row['Metoda identyfikacji']).lower():
                species = str(row['Rodzaj/gatunek']).strip()
                desc += f"\n↳ {species}"
            if label in ['mecA', 'nuc'] and 'sekwencjon' in str(row['Metoda identyfikacji']).lower():
                species = str(row['Rodzaj/gatunek']).strip()
                desc += f"\n↳ {species}"
            desc_list.append(desc)

        # Group repeated records with xN
        desc_counter = Counter(desc_list)
        descriptions = [f"{d} x{c}" if c > 1 else d for d, c in desc_counter.items()]

        if not descriptions:
            descriptions = [""]

        results.append({
            'Bacteria': label,
            'Cycle': cycle,
            'Count': len(desc_list),
            'Descriptions': descriptions
        })

# === Create DataFrame from results ===
all_df = pd.DataFrame(results)

# === Plotting Function ===
def plot_dotplot(category_labels, title):
    plot_df = all_df[all_df['Bacteria'].isin(category_labels)].copy()

    fig, ax = plt.subplots(figsize=(12, 6))
    texts = []

    for label in category_labels:
        sub = plot_df[plot_df['Bacteria'] == label]
        x = sub['Cycle']
        y = sub['Count']
        ax.plot(x, y, '-o', label=label)

        for xi, yi, descriptions in zip(x, y, sub['Descriptions']):
            # Scal opis w jeden tekst z łamaniem linii
            full_desc = '\n'.join(descriptions)
            texts.append(ax.text(xi, yi + 0.15, full_desc, fontsize=8, ha='center', va='bottom', multialignment='center'))

    adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='-', lw=0.5))
    ax.set_title(title)
    ax.set_xlabel('Cycle')
    ax.set_ylabel('Count')
    ax.legend()
    ax.grid(True)
    plt.tight_layout()
    plt.show()

# === Plot each category ===
plot_dotplot(['Enterococcus'], "Enterococcus occurrences by cycle")
plot_dotplot(['B. anthracis', 'B. cereus', 'B. thuringiensis', 'B. mycoides', 'B. cereus group'], "Bacillus group occurrences by cycle")
plot_dotplot(['mecA', 'nuc'], "mecA and nuc marker occurrences by cycle")
