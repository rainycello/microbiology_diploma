import pandas as pd
import numpy as np
import re
import plotly.express as px
import os

# Wczytaj plik Excela
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'Wyniki_powietrze-3.xlsx')
df = pd.read_excel(file_path, sheet_name="Powietrze zewnętrzne-dane")

# Wybierz potrzebne kolumny
df_clean = df[[
    "lokalizacja",
    "Ogólna Liczba drobnoustrojów/m3 -sedymentacja",
    "Ogólna liczba drobnoustrojów/m3-płuczka"
]].copy()

# Funkcja do parsowania wartości zapisanych jako notacja naukowa (np. 2,4×10^2)
def parse_scientific_notation(val):
    if pd.isna(val): return np.nan
    val = str(val).strip().replace(',', '.').replace('×', 'x').replace('^', '**')
    match = re.match(r'([\d.]+)\s*[xX]\s*10\s*\**\s*(\d+)', val)
    if match:
        base = float(match.group(1))
        exponent = int(match.group(2))
        return base * (10 ** exponent)
    try:
        return float(val)
    except:
        return np.nan

# Przekształć dane
df_clean["sedymentacja"] = df_clean["Ogólna Liczba drobnoustrojów/m3 -sedymentacja"].apply(parse_scientific_notation)
df_clean["pluczka"] = df_clean["Ogólna liczba drobnoustrojów/m3-płuczka"].apply(parse_scientific_notation)

# Oblicz średnie dla każdej lokalizacji
avg_bacteria = df_clean.groupby("lokalizacja")[["sedymentacja", "pluczka"]].mean().reset_index()

# Skaluje wartości do postaci a × 10²
def scale_to_e2(val):
    if pd.isna(val): return np.nan
    scaled = val / 100
    return scaled

# Przeskaluj dane do ×10² i zapisz etykiety tekstowe
avg_bacteria["sedymentacja_scaled"] = avg_bacteria["sedymentacja"].apply(scale_to_e2)
avg_bacteria["pluczka_scaled"] = avg_bacteria["pluczka"].apply(scale_to_e2)

# Przekształć do długiego formatu
df_melted = avg_bacteria.melt(
    id_vars='lokalizacja',
    value_vars=['sedymentacja_scaled', 'pluczka_scaled'],
    var_name='Method',
    value_name='Wartosc_scaled'
)

# Przypisz etykiety tekstowe z ×10²
df_melted["label"] = df_melted["Wartosc_scaled"].apply(lambda x: f"{x:.2f} × 10²" if pd.notna(x) else "")

# Nazwy metod ładniejsze
df_melted["Method"] = df_melted["Method"].map({
    "sedymentacja_scaled": "Sedimentation",
    "pluczka_scaled": "Scrubber"
})

# Wykres słupkowy z etykietami
fig = px.bar(
    df_melted,
    x="lokalizacja",
    y="Wartosc_scaled",
    color="Method",
    barmode="group",
    text="label",
    title="Average amount of bacteria per localization (scaled to ×10²)"
)

fig.update_layout(
    yaxis_title="Bacteria amount (×10² / m³)",
    xaxis_title="Localization",
    title_x=0.5,
    bargap=0.3
)

fig.update_traces(textposition='outside')

fig.show()
