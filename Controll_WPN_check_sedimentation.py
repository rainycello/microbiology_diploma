import pandas as pd
import numpy as np
import re
from scipy.stats import shapiro, ttest_ind, mannwhitneyu
import plotly.express as px
import os

# === Load data ===
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'Wyniki_powietrze-3.xlsx')
df = pd.read_excel(file_path, sheet_name="Powietrze zewnętrzne-dane")

# === Parse scientific notation (e.g. 3,6×10^2) ===
def parse_scientific_notation(val):
    if pd.isna(val):
        return np.nan
    val = str(val).strip().replace(',', '.').replace('×', 'x').replace('^', '**')
    match = re.match(r'([\d.]+)\s*[xX]\s*10\s*\**\s*(-?\d+)', val)  # handles negative exponents too
    if match:
        base = float(match.group(1))
        exponent = int(match.group(2))
        return base * (10 ** exponent)
    try:
        return float(val)
    except:
        return np.nan

# === Prepare data ===
df_clean = df[["lokalizacja", "Ogólna Liczba drobnoustrojów/m3 -sedymentacja"]].copy()
df_clean["sedimentation"] = df_clean["Ogólna Liczba drobnoustrojów/m3 -sedymentacja"].apply(parse_scientific_notation)
df_clean["lokalizacja"] = df_clean["lokalizacja"].astype(str)

# Create group column
df_clean["group"] = df_clean["lokalizacja"].apply(lambda x: "WPN (control)" if "WPN" in x else "Other locations")

# --- DEBUG: Check unique locations and groups ---
print("Unique locations:", df_clean["lokalizacja"].unique())
print("Unique groups:", df_clean["group"].unique())

# === Split data into two groups ===
wpn_vals = df_clean[df_clean["group"] == "WPN (control)"]["sedimentation"].dropna()
other_vals = df_clean[df_clean["group"] == "Other locations"]["sedimentation"].dropna()

# --- DEBUG: Check sample sizes and samples ---
print(f"Number of samples WPN: {len(wpn_vals)}")
print(f"Number of samples Other: {len(other_vals)}")
print("WPN samples:", wpn_vals.to_list())
print("Other samples:", other_vals.to_list())

print("\nANALYSIS: SEDIMENTATION\n" + "-"*40)

# === Shapiro-Wilk normality tests ===
if len(wpn_vals) >= 3 and len(other_vals) >= 3:  # minimum sample size for Shapiro
    stat_wpn, p_wpn = shapiro(wpn_vals)
    stat_other, p_other = shapiro(other_vals)
    print(f"Shapiro-Wilk (WPN): p = {p_wpn:.4f} {'normal' if p_wpn > 0.05 else 'not normal'}")
    print(f"Shapiro-Wilk (Other): p = {p_other:.4f} {'normal' if p_other > 0.05 else 'not normal'}")
else:
    p_wpn = p_other = 0  # force nonparametric test
    print("Not enough data for Shapiro normality test. Using nonparametric test.")

# === Group difference test ===
if p_wpn > 0.05 and p_other > 0.05 and len(wpn_vals) > 1 and len(other_vals) > 1:
    t_stat, p_val = ttest_ind(wpn_vals, other_vals, equal_var=False, alternative='less')
    test_name = "t-test"
else:
    if len(wpn_vals) > 0 and len(other_vals) > 0:
        u_stat, p_val = mannwhitneyu(wpn_vals, other_vals, alternative='less')
        test_name = "Mann–Whitney U"
    else:
        p_val = np.nan
        test_name = "Insufficient data for test"

print(f"\n📊 {test_name}: p = {p_val if not np.isnan(p_val) else 'NaN'}")
if not np.isnan(p_val) and p_val < 0.05:
    print("WPN has significantly fewer bacteria")
else:
    print("No significant difference or insufficient data")

# === Calculate CV for WPN ===
if len(wpn_vals) > 1:
    mean = wpn_vals.mean()
    std = wpn_vals.std()
    cv = std / mean * 100 if mean != 0 else np.nan
    print(f"\nMean (WPN): {mean:.2f}")
    print(f"📉 Standard deviation: {std:.2f}")
    print(f"📊 CV% (WPN): {cv:.2f}%")
    if not np.isnan(cv):
        if cv < 15:
            print("Low variability – good control")
        else:
            print("High variability – control may be unstable")
else:
    print("\nNot enough data to calculate CV for WPN")

# === Boxplot ===
fig = px.box(
    df_clean,
    x="group",
    y="sedimentation",
    points="all",
    color="group",
    title="Comparison of bacterial counts (sedimentation) per m³ – WPN vs Other locations",
    labels={"sedimentation": "Bacteria / m³", "group": "Group"}
)

fig.update_layout(
    title_x=0.5,
    showlegend=False
)

# === Add test result annotation ===
fig.add_annotation(
    text=f"{test_name}, p = {p_val:.4f}" if not np.isnan(p_val) else "Insufficient data for test",
    xref="paper", yref="paper",
    x=0.5, y=1.08, showarrow=False,
    font=dict(size=14)
)

fig.show()
