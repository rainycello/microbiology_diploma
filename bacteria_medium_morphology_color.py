import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# === Wczytaj dane ===
file_path = 'statistics_general_number_of_bacteria.xlsx'
df = pd.read_excel(file_path, sheet_name='Arkusz2')
df.columns = df.columns.str.strip()

# === Przygotuj dane ===
df = df[['Rodzaj', 'Gatunek', 'Podłoże', 'Kolor']].dropna()
df['Bakteria'] = df['Rodzaj'].str.strip() + ' ' + df['Gatunek'].str.strip()

# === Grupuj i zliczaj ===
grouped = df.groupby(['Bakteria', 'Kolor', 'Podłoże']).size().reset_index(name='Liczba')

# === Bubble plot ===
plt.figure(figsize=(18, 10))
sns.set(style='whitegrid')

sns.scatterplot(
    data=grouped,
    x='Kolor',
    y='Bakteria',
    size='Liczba',
    hue='Podłoże',
    palette='tab10',
    sizes=(50, 800),
    alpha=0.6,
    legend='brief'
)

# === Wygląd wykresu ===
plt.title('Najczęstsze kolory bakterii (Rodzaj + Gatunek) na różnych podłożach', fontsize=16)
plt.xlabel('Kolor')
plt.ylabel('Bakteria')
plt.xticks(rotation=45)
plt.legend(title='Podłoże', bbox_to_anchor=(1.02, 1), loc='upper left')
plt.tight_layout()
plt.show()
