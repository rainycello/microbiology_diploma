import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr, kendalltau
from statsmodels.formula.api import glm
from statsmodels.genmod.families import Poisson, NegativeBinomial

# === Plik i arkusze ===
file_path = 'powietrze wszystkie dane(1).xlsx'
sheets = ['Łódź', 'Rybnik', 'Drawieński park Narodowy']

# === Kolumny bakteryjne ===
bacteria_cols = [
    'Ogólna Liczba drobnoustrojów/m3', 'Liczba bakterii opornych na streptomycynę',
    'Częstość sterptomycynoopornych', 'Liczba szczepów z int I1/m3', 'Częstość intI+',
    'Liczba ESBL', 'LIczba CRE', 'Liczba MRSA', 'Liczba VRE'
]

# === Kolumny pogodowe ===
weather_cols = [
    'Temperatura', 'dzień przed', '2 dni przed', '3 dni przed',
    'Wilgotność', 'dzień przed', '2 dni przed', '3 dni przed',
    'Opad dobowy [mm]', 'dzień przed', '2 dni przed', '3 dni przed',
    'Wiatr dzień poboru [km/h]', 'Wiatr 1 dzień przed', 'Wiatr 2 dni przed', 'Wiatr 3 dni przed',
    'Ciśnienie', 'dzień przed', '2 dni przed', '3 dni przed',
    'AQI dzień poboru', '1 dzien przed poborem', '2 dni przed poborem', '3 dni przed poborem',
    'PM10 dzien poboru', 'PM10 1 dzien przed wyborem', 'PM10 2 dni przed wyborem', 'PM10  3 dni przed wyborem',
    'PM 2.5 dzien poboru', '1dzien przed', '2 dni przed', '3 dni przed',
    'NO2', '1dzien przed', '2 dni przed', '3 dni przed',
    'SO2', '1dzien przed', '2 dni przed', '3 dni przed',
    'CO', '1dzien przed', '2 dni przed', '3 dni przed',
    'PM2.5 (miernik)', 'PM10', 'PM1', 'HCHO', 'TVOC', 'temp', 'humid', 'cisnienie', 'wys. npm'
]

# === Funkcje analityczne ===
def compute_corr(df, x_cols, y_cols, method):
    results = []
    for y in y_cols:
        for x in x_cols:
            try:
                if method == 'spearman':
                    coef, p = spearmanr(df[x], df[y])
                elif method == 'kendall':
                    coef, p = kendalltau(df[x], df[y])
                results.append({'x': x, 'y': y, 'coef': coef, 'p': p, 'method': method})
            except:
                continue
    return pd.DataFrame(results)

def compute_glm(df, x_cols, y_cols, family, method_name):
    results = []
    for y in y_cols:
        for x in x_cols:
            try:
                formula = f'Q("{y}") ~ Q("{x}")'
                model = glm(formula=formula, data=df, family=family()).fit()
                coef = model.params[1]
                p = model.pvalues[1]
                results.append({'x': x, 'y': y, 'coef': coef, 'p': p, 'method': method_name})
            except:
                continue
    return pd.DataFrame(results)

# === Wizualizacja ===
def plot_method(df_method, title):
    method_name = df_method['method'].iloc[0] if not df_method.empty else ""

    plt.figure(figsize=(14, 8))
    plot_data = df_method.copy()
    plot_data = plot_data.dropna(subset=['coef', 'p'])

    # Tu wyłącz filtr lub dopisz 'spearman' jeśli chcesz filtrować:
    if method_name in ['spearman', 'kendall']:
        plot_data = plot_data[(plot_data['coef'] <= -0.1) | (plot_data['coef'] >= 0.1)]

    plot_data.sort_values('coef', inplace=True)

    ax = sns.barplot(
        data=plot_data, x='coef', y='y', hue='x',
        dodge=False, palette='RdYlGn'
    )

    plt.axvline(0, color='black', linestyle='--', linewidth=1)
    plt.title(title, fontsize=16)
    plt.xlabel('Współczynnik korelacji/regresji')
    plt.ylabel('Wskaźnik bakteryjny')
    plt.legend(title='Czynnik pogodowy', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()


# === Główna pętla ===
all_results = []

for sheet in sheets:
    df = pd.read_excel(file_path, sheet_name=sheet)
    df.columns = df.columns.str.strip()
    x_cols = [col for col in weather_cols if col in df.columns]
    y_cols = [col for col in bacteria_cols if col in df.columns]
    df = df[x_cols + y_cols].dropna()

    # Analizy
    df_spearman = compute_corr(df, x_cols, y_cols, method='spearman')
    df_kendall = compute_corr(df, x_cols, y_cols, method='kendall')
    df_poisson = compute_glm(df, x_cols, y_cols, Poisson, method_name='poisson')
    df_nb = compute_glm(df, x_cols, y_cols, NegativeBinomial, method_name='neg_binomial')

    # Dodanie info o arkuszu
    for d in [df_spearman, df_kendall, df_poisson, df_nb]:
        d['sheet'] = sheet

    all_results.extend([df_spearman, df_kendall, df_poisson, df_nb])

    # Wykresy
    for df_plot in [df_spearman, df_kendall, df_poisson, df_nb]:
        plot_method(df_plot, f"{df_plot['method'].iloc[0].upper()} — {sheet}")

# === Zapis do Excela ===
summary_table = pd.concat(all_results, ignore_index=True)
summary_table.to_excel("wyniki_korelacje_regresje_miasta.xlsx", index=False)
