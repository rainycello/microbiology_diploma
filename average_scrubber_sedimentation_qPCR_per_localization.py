import pandas as pd
import numpy as np
import re
import plotly.express as px
import os

# === FILE PATHS ===
script_dir = os.path.dirname(os.path.abspath(__file__))

file_culture = os.path.join(script_dir, 'Wyniki_powietrze-3.xlsx')
file_qpcr = os.path.join(script_dir, 'podsumowanie obliczeń dPCR, qPCR.xlsx')

# === LOAD CULTURE DATA ===
df_culture = pd.read_excel(file_culture, sheet_name="Powietrze zewnętrzne-dane")

df_clean = df_culture[[
    "lokalizacja",
    "Ogólna Liczba drobnoustrojów/m3 -sedymentacja",
    "Ogólna liczba drobnoustrojów/m3-płuczka"
]].copy()

# === PARSE SCIENTIFIC FORMAT (e.g., 3,6×10^2 → 360) ===
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

# Apply parsing
df_clean["sedymentacja"] = df_clean["Ogólna Liczba drobnoustrojów/m3 -sedymentacja"].apply(parse_scientific_notation)
df_clean["pluczka"] = df_clean["Ogólna liczba drobnoustrojów/m3-płuczka"].apply(parse_scientific_notation)

# AVERAGE per localization
avg_bacteria = df_clean.groupby("lokalizacja")[["sedymentacja", "pluczka"]].mean().reset_index()

# === LOAD qPCR DATA ===
df_qpcr = pd.read_excel(file_qpcr, sheet_name="Arkusz1")

# Keep only relevant columns and rename to match case
df_qpcr = df_qpcr[[
    "Lokalizacja",
    "qPCR Starting Quantity (SQ) Mean",
    "sec, mean DNA amount for m3",
    "regA, mean DNA amount for m3"
]].copy()

df_qpcr.rename(columns={
    "Lokalizacja": "lokalizacja",
    "qPCR Starting Quantity (SQ) Mean": "qPCR",
    "sec, mean DNA amount for m3": "DNA_sec",
    "regA, mean DNA amount for m3": "DNA_regA"
}, inplace=True)

# Convert to numeric
for col in ["qPCR", "DNA_sec", "DNA_regA"]:
    df_qpcr[col] = pd.to_numeric(df_qpcr[col], errors='coerce')

# AVERAGE per localization
df_qpcr_avg = df_qpcr.groupby("lokalizacja")[["qPCR", "DNA_sec", "DNA_regA"]].mean().reset_index()

# === MERGE ALL ===
merged = pd.merge(avg_bacteria, df_qpcr_avg, on="lokalizacja", how="outer")

# === SCALE TO ×10² ===
def scale_to_e2(val):
    if pd.isna(val): return np.nan
    return val / 100

for col in ['sedymentacja', 'pluczka', 'qPCR', 'DNA_sec', 'DNA_regA']:
    merged[f"{col}_scaled"] = merged[col].apply(scale_to_e2)

# === MELT FOR PLOTTING ===
df_melted = merged.melt(
    id_vars='lokalizacja',
    value_vars=[
        'sedymentacja_scaled',
        'pluczka_scaled',
        'qPCR_scaled',
        'DNA_sec_scaled',
        'DNA_regA_scaled'
    ],
    var_name='Method',
    value_name='Wartosc_scaled'
)

# === LABELS ===
df_melted["Method"] = df_melted["Method"].map({
#    "sedymentacja_scaled": "Sedimentation",
#    "pluczka_scaled": "Scrubber",
#    "qPCR_scaled": "qPCR 16S",
#    "DNA_sec_scaled": "dPCR (sec)",
    "DNA_regA_scaled": "dPCR (regA)"
})

df_melted["label"] = df_melted["Wartosc_scaled"].apply(
    lambda x: f"{x:.2f} × 10²" if pd.notna(x) else ""
)

# === OPTIONAL: SORT LOCATIONS BY TOTAL VALUES ===
merged['sum_all'] = merged[[
    'sedymentacja_scaled',
    'pluczka_scaled',
    'qPCR_scaled',
    'DNA_sec_scaled',
    'DNA_regA_scaled'
]].sum(axis=1)

lokalizacja_order = merged.sort_values('sum_all')['lokalizacja'].tolist()
df_melted["lokalizacja"] = pd.Categorical(df_melted["lokalizacja"], categories=lokalizacja_order, ordered=True)

# === PLOT ===
fig = px.bar(
    df_melted,
    x="lokalizacja",
    y="Wartosc_scaled",
    color="Method",
    barmode="group",
    text="label",
    title="Average bacterial amount per localization (scaled to ×10²)"
)

fig.update_layout(
    yaxis_title="DNA amount (×10² / m³)",
    xaxis_title="Localization",
    title_x=0.5,
    bargap=0.3
)

fig.update_traces(textposition='outside')
fig.show()
