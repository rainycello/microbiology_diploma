import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr, pearsonr, kendalltau
from adjustText import adjust_text
from statsmodels.formula.api import glm
from statsmodels.genmod.families import Poisson, NegativeBinomial

# === Wczytaj dane ===
file_path = 'powietrze wszystkie dane(1).xlsx'
sheet_name = 'Poznań'
df = pd.read_excel(file_path, sheet_name=sheet_name)
df.columns = df.columns.str.strip()

# === Zmienne wejściowe i docelowe ===
weather_cols = [
    'PM10 dzien poboru (ug/m3)',	'PM 2.5 (ug/m3)',	'PM 1 tylko nasz aparat(ug/m3)',	'NO2 (ug/m3)',	'NO (ug/m3)',	'tlenki azotu (ug/m3)',	'SO2 (ug/m3)',	'CO (mg/m3)',	'benzen (ug/m3)', 'ozon (ug/m3)'
]

bacteria_cols = [
    'Ogólna Liczba drobnoustrojów/m3',	'Liczba bakterii opornych na streptomycynę', 'Częstość sterptomycynoopornych',	'Liczba szczepów z int I1/m3',	'Częstość intI+',	'Liczba Campylobacter',	'Liczba Listeria sp/m3',	'Liczba L. monocytogenes/m3',	'Liczba ESBL - na podstawie antybiogramów',	'Liczba CRE - na podstawie antybiogramów',	'Liczba mec+',	'Częstość mec+',	'Liczba VRE'
]

df = df[weather_cols + bacteria_cols].dropna()

# === Funkcje korelacji ===
def compute_corr(df, x_cols, y_cols, method):
    results = []
    for y in y_cols:
        for x in x_cols:
            try:
                if method == 'spearman':
                    coef, p = spearmanr(df[x], df[y])
                elif method == 'pearson':
                    coef, p = pearsonr(df[x], df[y])
                elif method == 'kendall':
                    coef, p = kendalltau(df[x], df[y])
                results.append({'x': x, 'y': y, 'coef': coef, 'p': p, 'method': method})
            except:
                continue
    return pd.DataFrame(results)

# === Funkcje regresji ===
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

# === Obliczenia ===
df_spearman = compute_corr(df, weather_cols, bacteria_cols, method='spearman')
df_pearson = compute_corr(df, weather_cols, bacteria_cols, method='pearson')
df_kendall = compute_corr(df, weather_cols, bacteria_cols, method='kendall')
df_poisson = compute_glm(df, weather_cols, bacteria_cols, Poisson, method_name='poisson')
df_nb = compute_glm(df, weather_cols, bacteria_cols, NegativeBinomial, method_name='neg_binomial')

# === Łączenie wyników ===
all_corrs = pd.concat([df_spearman, df_pearson, df_kendall, df_poisson, df_nb], ignore_index=True)


def significance_stars(p):
    if p < 0.001:
        return '***'
    elif p < 0.01:
        return '**'
    elif p < 0.05:
        return '*'
    else:
        return ''


def plot_method(df_method, title):
    plt.figure(figsize=(14, 8))
    plot_data = df_method.copy()
    plot_data['direction'] = np.where(plot_data['coef'] >= 0, 'Pozytywna', 'Ujemna')
    plot_data.sort_values('coef', inplace=True)

    plot_data['coef_pct'] = (plot_data['coef'] * 100).round(2)
    plot_data['stars'] = plot_data['p'].apply(significance_stars)
    plot_data['label'] = plot_data['coef_pct'].astype(str) + '%' + plot_data['stars']

    ax = sns.barplot(
        data=plot_data, x='coef', y='y', hue='x',
        dodge=False, palette='RdYlGn'
    )
    plt.axvline(0, color='black', linestyle='--', linewidth=1)
    plt.title(title, fontsize=16)
    plt.xlabel('Współczynnik korelacji/regresji')
    plt.ylabel('Wskaźnik bakteryjny')
    plt.legend(title='Czynnik pogodowy', bbox_to_anchor=(1.05, 1), loc='upper left')

    # Dodajemy teksty (procenty + gwiazdki) z adjust_text
    texts = []
    for i, bar in enumerate(ax.patches):
        width = bar.get_width()
        y_pos = bar.get_y() + bar.get_height() / 2
        label = plot_data.iloc[i]['label']
        if width < 0:
            text = ax.text(width - 0.05, y_pos, label, va='center', ha='right', fontsize=9, color='black')
        else:
            text = ax.text(width + 0.02, y_pos, label, va='center', ha='left', fontsize=9, color='black')
        texts.append(text)

    adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='-', color='gray', lw=0.5))

    plt.tight_layout()
    plt.show()


# === Wykresy dla każdej metody ===
for method_name in ['spearman', 'pearson', 'kendall', 'poisson', 'neg_binomial']:
    df_plot = all_corrs[all_corrs['method'] == method_name]
    plot_method(df_plot, f"{method_name.upper()} — Korelacja/regresja pogoda vs bakterie")
