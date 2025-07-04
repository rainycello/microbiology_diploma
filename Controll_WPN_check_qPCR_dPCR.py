import pandas as pd
import numpy as np
import re
from scipy.stats import shapiro, ttest_ind, mannwhitneyu
import plotly.express as px
import os

# === Paths ===
script_dir = os.path.dirname(os.path.abspath(__file__))
file_culture = os.path.join(script_dir, 'Wyniki_powietrze-3.xlsx')
file_qpcr = os.path.join(script_dir, 'podsumowanie obliczeń dPCR, qPCR.xlsx')

# === Load and clean culture data ===
df_culture = pd.read_excel(file_culture, sheet_name="Powietrze zewnętrzne-dane")

# Helper to parse scientific notation with various formats
def parse_scientific(val):
    if pd.isna(val):
        return np.nan
    val = str(val).replace(',', '.').replace('×', 'x').replace('^', '**')
    match = re.match(r'([\d.]+)\s*[xX]\s*10\s*\**\s*(-?\d+)', val)
    if match:
        return float(match.group(1)) * (10 ** int(match.group(2)))
    try:
        return float(val)
    except:
        return np.nan

df_culture["lokalizacja"] = df_culture["lokalizacja"].astype(str)
df_culture["group"] = df_culture["lokalizacja"].apply(lambda x: "WPN (control)" if "WPN" in x else "Other locations")
df_culture["sedimentation"] = df_culture["Ogólna Liczba drobnoustrojów/m3 -sedymentacja"].apply(parse_scientific)

# === Load and clean qPCR/dPCR data ===
df_qpcr = pd.read_excel(file_qpcr, sheet_name="Arkusz1")
df_qpcr.rename(columns={
    "Lokalizacja": "lokalizacja",
    "qPCR Starting Quantity (SQ) Mean": "qPCR",
    "sec, mean DNA amount for m3": "sec",
    "regA, mean DNA amount for m3": "regA"
}, inplace=True)

# Parse scientific notation in relevant columns
for col in ["qPCR", "sec", "regA"]:
    df_qpcr[col] = df_qpcr[col].apply(parse_scientific)

df_qpcr["group"] = df_qpcr["lokalizacja"].astype(str).apply(lambda x: "WPN (control)" if "WPN" in x else "Other locations")

# === Merge dataframes ===
df = pd.merge(
    df_culture[["lokalizacja", "group", "sedimentation"]],
    df_qpcr[["lokalizacja", "group", "qPCR", "sec", "regA"]],
    on=["lokalizacja", "group"],
    how="outer"
)

# === Analysis + Plotting function ===
def analyze_and_plot(df, var_col, group_col="group"):
    print(f"\n📊 Analyzing: {var_col}")
    vals_wpn = df[df[group_col] == "WPN (control)"][var_col].dropna()
    vals_other = df[df[group_col] == "Other locations"][var_col].dropna()

    if len(vals_wpn) < 1 or len(vals_other) < 1:
        print("Not enough data.")
        return

    # Normality test
    if len(vals_wpn) >= 3 and len(vals_other) >= 3:
        _, p1 = shapiro(vals_wpn)
        _, p2 = shapiro(vals_other)
    else:
        p1 = p2 = 0

    # Select statistical test
    if p1 > 0.05 and p2 > 0.05:
        stat_name = "t-test"
        _, p_val = ttest_ind(vals_wpn, vals_other, equal_var=False, alternative='less')
    else:
        stat_name = "Mann–Whitney U"
        _, p_val = mannwhitneyu(vals_wpn, vals_other, alternative='less')

    print(f"{stat_name}: p = {p_val:.4f}")

    # Plot boxplot with all data points
    fig = px.box(
        df,
        x=group_col,
        y=var_col,
        points="all",
        color=group_col,
        title=f"{var_col} – WPN vs Other locations",
        labels={group_col: "Group", var_col: var_col}
    )

    fig.update_layout(title_x=0.5, showlegend=False)
    fig.add_annotation(
        text=f"{stat_name}, p = {p_val:.4f}",
        xref="paper", yref="paper",
        x=0.5, y=1.08, showarrow=False,
        font=dict(size=14)
    )

    fig.show()

# === Run analysis and plotting ===
for col in ["sedimentation", "qPCR", "sec", "regA"]:
    if col in df.columns:
        analyze_and_plot(df, col)
