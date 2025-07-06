import pandas as pd
import matplotlib.pyplot as plt

# === CONFIGURATION ===
file_path = 'Wyniki_powietrze-3.xlsx'  # Replace with your file name
sheet_name = 'Powietrze zewnątrz-G(+)'  # Target sheet
start_row = 336  # Skip 336 rows to start from row 337

# === LOAD DATA ===
df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=start_row, engine='openpyxl')

# Convert rows to single strings to search across all columns
df_str = df.astype(str).apply(lambda row: ' '.join(row.values), axis=1)

# === SEARCH TERMS ===
mask_enterococcus = df_str.str.contains(r'enterococcus', case=False)
mask_nuc_meca = df_str.str.contains(r'\bnuc\b|\bmecA\b', case=False)

# === FILTERED DATA ===
df_enterococcus = df[mask_enterococcus]
df_nuc_meca = df[mask_nuc_meca]

# === COUNT RESULTS ===
enterococcus_count = df_enterococcus.shape[0]
nuc_meca_count = df_nuc_meca.shape[0]

# === EXPORT MATCHED ROWS ===
df_enterococcus.to_excel('enterococcus_results.xlsx', index=False)
df_nuc_meca.to_excel('nuc_meca_results.xlsx', index=False)

# === PLOT RESULTS ===
plt.figure(figsize=(6, 4))
plt.bar(['Enterococcus', 'nuc/mecA'], [enterococcus_count, nuc_meca_count], color=['blue', 'green'])
plt.title('Occurrences in Dataset')
plt.ylabel('Number of Matches')
plt.tight_layout()
plt.savefig('match_summary_plot.png')
plt.show()
