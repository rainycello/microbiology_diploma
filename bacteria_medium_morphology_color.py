import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Wczytaj dane
file_path = 'statistics_general_number_of_bacteria.xlsx'
df = pd.read_excel(file_path, sheet_name='Arkusz2')
df.columns = df.columns.str.strip()

# Diagnostyka: pokaż kolumny
print("Kolumny w danych:", df.columns.tolist())

# Wypełnij brakujące nazwy bakterii w dół
df['Bacteria'] = df['Bacteria'].ffill()

# Usuń wiersze z brakującym Medium lub Color
df = df.dropna(subset=['Medium', 'Color'])

# Diagnostyka: ile danych po wstępnym czyszczeniu
print("Liczba wierszy po usunięciu braków Medium/Color:", len(df))

# Słownik tłumaczeń kolorów (PL → EN)
color_translation = {
    'transparent': 'transparent',
    'przezroczysty': 'transparent',
    'żółty': 'yellow',
    'różowy': 'pink',
    'czarny': 'black',
    'biały': 'white',
    'białe': 'white',
    'fioletowy': 'purple',
    'pomarańczowy': 'orange',
    'zielony': 'green',
    'czerwony': 'red',
    'biało-różowy': 'white-pink',
    'żółto-biały': 'yellow-white',
    'różowo-przezroczysty': 'pink-transparent',
    'różowo-żółty': 'pink-yellow',
    'różowy, fioletowy': 'pink, purple',
    'żółty, biały': 'yellow, white',
    'z czarnym środkiem': 'with black center',
    'białe wyniosły': 'white raised',
    'biały (różowo-przezroczysty)': 'white (pink-transparent)',
    'różowy, biały (różowo-przezroczysty)': 'pink, white (pink-transparent)',
    'przezroczysty, różowy': 'transparent, pink'
}

# Funkcja tłumacząca kolory
def translate_colors(color_str):
    color_str = str(color_str).lower().strip()

    if color_str in color_translation:
        return color_translation[color_str]

    colors = [c.strip() for c in color_str.split(',')]
    translated = []
    for c in colors:
        if c in color_translation:
            translated.append(color_translation[c])
        else:
            if '-' in c:
                parts = c.split('-')
                parts_translated = [color_translation.get(p.strip(), p.strip()) for p in parts]
                translated.append('-'.join(parts_translated))
            else:
                translated.append(color_translation.get(c, c))
    return ', '.join(translated)

# Przetłumacz kolory
df['Color'] = df['Color'].astype(str)
df['Color_EN'] = df['Color'].apply(translate_colors)

print("\nPrzykładowe kolory po tłumaczeniu:")
print(df[['Color', 'Color_EN']].drop_duplicates().head(10))

df['Color_EN'] = df['Color_EN'].str.split(',')
df = df.explode('Color_EN')
df['Color_EN'] = df['Color_EN'].str.strip()

df = df.drop_duplicates(subset=['Bacteria', 'Medium', 'Color_EN'])

print("\nLiczba unikalnych punktów (Bacteria-Medium-Color):", len(df))
print(df[['Bacteria', 'Medium', 'Color_EN']].drop_duplicates().head())

df['Size'] = 1

# Lista uporządkowanych kolorów dla osi x
unique_colors = sorted(df['Color_EN'].unique())

# Jeśli dane są puste, zakończ
if df.empty:
    print("\nUWAGA: Dane są puste. Sprawdź format danych wejściowych.")
else:
    plt.figure(figsize=(18, 12))
    sns.set(style='whitegrid')

    # Stripplot
    ax = sns.stripplot(
        data=df,
        x='Color_EN',
        y='Bacteria',
        hue='Medium',
        dodge=True,
        jitter=0.25,
        size=6,
        alpha=0.7,
        palette='tab10',
        order=unique_colors
    )

    # Dodaj wertykalne linie oddzielające kategorie kolorów
    xticks_locs = range(len(unique_colors))
    for x in xticks_locs:
        plt.axvline(x=x + 0.5, color='gray', linestyle='--', alpha=0.2)

    plt.title('Colors of bacterial colonies on different media (presence)', fontsize=16)
    plt.xlabel('Color')
    plt.ylabel('Bacteria')
    plt.xticks(ticks=xticks_locs, labels=unique_colors, rotation=45)
    plt.legend(title='Medium', bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout()
    plt.show()
