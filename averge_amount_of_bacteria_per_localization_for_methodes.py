import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# === Wczytaj dane ===
file_path = 'Wyniki_powietrze-3.xlsx'
sheet_name = 'Powietrze zewnątrz-G(-)'
df = pd.read_excel(file_path, sheet_name=sheet_name)

# === Lista bakterii coli ===
coli_keywords = ['Pantoea', 'Enterobacter', 'Klebsiella', 'Citrobacter', 'Erwinia',
                 'Moellerella', 'Leclercia', 'Kluyvera', 'Buttiauxella']

# === Filtruj tylko bakterie coli ===
df_coli = df[df['Rodzaj/gatunek'].astype(str).str.contains('|'.join(coli_keywords), case=False, na=False)]

# === Przypisz uproszczone metody ===
def detect_method(text):
    text = str(text).lower()
    if 'hodowla' in text:
        return 'Hodowla'
    elif 'płuczka' in text:
        return 'Płuczka'
    elif 'sedymentacja' in text:
        return 'Sedymentacja'
    else:
        return 'Inna'

df_coli['Metoda'] = df_coli['Metoda poboru'].apply(detect_method)

# === Przygotuj podsumowanie ===
metody_lista = ['Sedymentacja', 'Płuczka', 'Hodowla']
lokalizacje = sorted(df['Miejsce poboru'].dropna().unique())

kombinacje = pd.MultiIndex.from_product([lokalizacje, metody_lista], names=['Miejsce poboru', 'Metoda'])
summary = df_coli.groupby(['Miejsce poboru', 'Metoda']).agg(
    Liczba_prób=('Rodzaj/gatunek', 'count'),
    Różnorodność=('Rodzaj/gatunek', pd.Series.nunique)
).reindex(kombinacje, fill_value=0).reset_index()

# === Kolory metod ===
kolory_metod = {
    'Sedymentacja': 'steelblue',
    'Płuczka': 'forestgreen',
    'Hodowla': 'gold'
}

# === Funkcja rysująca ===
def rysuj_wykres_pogrupowany(df, wartosc, tytul, ylabel):
    x = np.arange(len(lokalizacje))  # pozycje bazowe
    width = 0.25  # szerokość słupka

    fig, ax = plt.subplots(figsize=(10, 6))

    for i, metoda in enumerate(metody_lista):
        dane = df[df['Metoda'] == metoda][wartosc].values
        ax.bar(x + i * width, dane, width, label=metoda, color=kolory_metod[metoda])

    ax.set_xticks(x + width)
    ax.set_xticklabels(lokalizacje, rotation=45)
    ax.set_ylabel(ylabel)
    ax.set_title(tytul)
    ax.legend(title='Metoda')
    plt.tight_layout()
    plt.show()

# === Rysuj wykresy ===
rysuj_wykres_pogrupowany(summary, 'Liczba_prób', 'Liczba prób bakterii coli wg lokalizacji i metody', 'Liczba prób')
rysuj_wykres_pogrupowany(summary, 'Różnorodność', 'Różnorodność bakterii coli wg lokalizacji i metody', 'Liczba unikalnych rodzajów/gatunków')
