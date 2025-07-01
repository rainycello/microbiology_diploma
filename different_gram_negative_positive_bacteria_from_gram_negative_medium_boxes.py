import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Wczytaj plik
file_path = '/home/dmytro/Downloads/microbiology_diploma/G-.xlsx'

df = pd.read_excel(file_path, sheet_name='Arkusz1')

# Czyszczenie nazw kolumn
df.columns = df.columns.str.strip()

# Usunięcie wierszy bez identyfikacji lub z 'NNNNN'
df_cleaned = df[df['Rodzaj/gatunek (po czyszczeniu)'].notna() &
                ~df['Rodzaj/gatunek (po czyszczeniu)'].astype(str).str.contains('NNNNN', na=False)]

# Usunięcie wierszy bez kluczowych danych
df_cleaned = df_cleaned.dropna(subset=['Pobór', 'Podłoże z którego wyhodowano/morfologia kolonii', 'Miejsce poboru'])

# Listy słów kluczowych
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
    if pd.isnull(species_name):
        return 'Nieokreślony'
    species_name_lower = str(species_name).lower()
    if any(keyword.lower() in species_name_lower for keyword in gram_negative_keywords):
        return 'Gram-ujemna'
    elif any(keyword.lower() in species_name_lower for keyword in gram_positive_keywords):
        return 'Gram-dodatnia'
    else:
        return 'Nieokreślony'

df_cleaned['Typ Grama'] = df_cleaned['Rodzaj/gatunek (po czyszczeniu)'].apply(classify_gram)

# Agregacja i procenty
grouped_data = df_cleaned.groupby([
    'Pobór',
    'Typ Grama',
    'Podłoże z którego wyhodowano/morfologia kolonii',
    'Miejsce poboru'
]).size().reset_index(name='Liczba izolatów')
grouped_data['Procent'] = grouped_data.groupby('Pobór')['Liczba izolatów'].transform(lambda x: x / x.sum() * 100)

# Wizualizacja
plt.figure(figsize=(18, 10))
g = sns.catplot(
    data=grouped_data,
    x='Podłoże z którego wyhodowano/morfologia kolonii',
    y='Procent',
    hue='Miejsce poboru',
    col='Pobór',
    row='Typ Grama',
    kind='bar',
    height=6, aspect=1.5,
    palette='tab10',
    legend_out=True
)
g.set_axis_labels("Podłoże", "Procent (%)")
g.set_titles("Cykl {col_name}, {row_name}")
g.set_xticklabels(rotation=45, ha='right')
plt.suptitle('Procentowy udział bakterii Gram-ujemnych i Gram-dodatnich w cyklach, podłożach i lokalizacjach',
             y=1.02, fontsize=16)
plt.tight_layout(rect=[0, 0, 1, 0.98])
plt.show()

