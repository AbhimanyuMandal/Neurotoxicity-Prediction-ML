"""
04_generate_rdkit_descriptors.py

Generate all RDKit molecular descriptors.

Input:
    data/processed/validated_compounds.csv

Output:
    data/processed/rdkit_descriptors.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

from rdkit import Chem
from rdkit.Chem import Descriptors

# ----------------------------------------------------
# Paths
# ----------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "processed" / "validated_compounds.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "rdkit_descriptors.csv"

REPORT_DIR = BASE_DIR / "data" / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------
# Load dataset
# ----------------------------------------------------

df = pd.read_csv(INPUT_FILE)

print(f"\nLoaded {len(df)} validated compounds.")

# ----------------------------------------------------
# Get all RDKit descriptors
# ----------------------------------------------------

descriptor_list = Descriptors.descList

print(f"Found {len(descriptor_list)} RDKit descriptors.")

rows = []

# ----------------------------------------------------
# Compute descriptors
# ----------------------------------------------------

for _, row in tqdm(df.iterrows(), total=len(df)):

    smiles = row["Canonical_SMILES"]

    mol = Chem.MolFromSmiles(smiles)

    if mol is None:
        continue

    descriptor_values = {}

    for descriptor_name, descriptor_function in descriptor_list:

        try:
            descriptor_values[descriptor_name] = descriptor_function(mol)

        except Exception:
            descriptor_values[descriptor_name] = np.nan

    # -------------------------
    # Preserve metadata
    # -------------------------

    descriptor_values["Compound_Name"] = row["Compound_Name"]

    descriptor_values["Label"] = row["Label"]

    descriptor_values["CID"] = row["CID"]

    descriptor_values["Canonical_SMILES"] = smiles

    descriptor_values["MolecularFormula"] = row.get("MolecularFormula")

    descriptor_values["MolecularWeight"] = row.get("MolecularWeight")

    descriptor_values["InChIKey"] = row.get("RDKit_InChIKey")

    rows.append(descriptor_values)

# ----------------------------------------------------
# Create dataframe
# ----------------------------------------------------

descriptor_df = pd.DataFrame(rows)

# ==========================================================
# Clean descriptor matrix
# ==========================================================


print("\nCleaning descriptor matrix...")

# Metadata columns
metadata = [
    "Compound_Name",
    "Label",
    "CID",
    "Canonical_SMILES",
    "MolecularFormula",
    "MolecularWeight",
    "InChIKey",
]

descriptor_columns = [
    c for c in descriptor_df.columns
    if c not in metadata
]

X = descriptor_df[descriptor_columns]

# Convert everything to numeric
X = X.apply(pd.to_numeric, errors="coerce")

# Replace Inf
X = X.replace([np.inf, -np.inf], np.nan)

print(f"Original descriptors : {X.shape[1]}")

# ==========================================================
# Remove known unstable RDKit descriptors
# ==========================================================

DESCRIPTORS_TO_REMOVE = [
    "Ipc",
    "AvgIpc",
    "BalabanJ",
    "BertzCT",
]

existing = [d for d in DESCRIPTORS_TO_REMOVE if d in X.columns]

if existing:
    print(f"Removing known unstable descriptors: {existing}")
    X = X.drop(columns=existing)

print(f"Remaining descriptors: {X.shape[1]}")

# Remove columns with any missing values
bad_columns = X.columns[X.isna().any()]

print(f"Removing {len(bad_columns)} unstable descriptors.")

X = X.drop(columns=bad_columns)

# ==========================================================
# Remove descriptors with extremely large values
# ==========================================================

MAX_ALLOWED = 1e8

large_value_columns = []

for col in X.columns:

    max_value = X[col].abs().max()

    if pd.notna(max_value) and max_value > MAX_ALLOWED:
        large_value_columns.append(col)

print(f"Removing {len(large_value_columns)} descriptors with huge values.")

X = X.drop(columns=large_value_columns)


# Remove constant descriptors
constant_columns = X.columns[X.nunique() <= 1]

print(f"Removing {len(constant_columns)} constant descriptors.")

X = X.drop(columns=constant_columns)

# Remove descriptors with >95% identical values

low_variance = []

for col in X.columns:

    counts = X[col].value_counts(normalize=True)

    if len(counts) == 0:
        continue

    if counts.iloc[0] > 0.99:
        low_variance.append(col)

print(f"Removing {len(low_variance)} low-information descriptors.")

X = X.drop(columns=low_variance)

# ----------------------------------------------------
# Move metadata columns to front
# ----------------------------------------------------

X = X.reindex(sorted(X.columns), axis=1)

# ============================================
# Rebuild dataframe
# ============================================

descriptor_df = pd.concat(
    [
        descriptor_df[metadata],
        X
    ],
    axis=1
)

print("\nDescriptor Cleaning Summary")
print("-" * 40)
print(f"Final descriptors: {X.shape[1]}")
print(f"Final dataset shape: {descriptor_df.shape}")

print(f"Final descriptors : {X.shape[1]}")
# ============================================
# Save cleaning report
# ============================================

removed = (
    list(existing)
    + list(bad_columns)
    + list(large_value_columns)
    + list(constant_columns)
    + list(low_variance)
)

cleaning_report = pd.DataFrame({
    "Removed_Descriptors": removed
})

cleaning_report.to_csv(
    REPORT_DIR / "removed_descriptors.csv",
    index=False
)

# ============================================
# Save cleaned descriptor matrix
# ============================================

descriptor_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("Saved!")