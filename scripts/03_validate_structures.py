"""
03_validate_structures.py

Validate molecular structures using RDKit.

Input:
    data/processed/pubchem_compounds.csv

Outputs:
    data/processed/validated_compounds.csv
    data/reports/invalid_compounds.csv
    data/reports/duplicate_structures.csv
"""

from pathlib import Path

import pandas as pd

from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit.Chem import rdMolDescriptors

# ==========================================================
# Paths
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR /
    "data" /
    "processed" /
    "pubchem_compounds.csv"
)

OUTPUT_FILE = (
    BASE_DIR /
    "data" /
    "processed" /
    "validated_compounds.csv"
)

INVALID_FILE = (
    BASE_DIR /
    "data" /
    "reports" /
    "invalid_compounds.csv"
)

DUPLICATE_FILE = (
    BASE_DIR /
    "data" /
    "reports" /
    "duplicate_structures.csv"
)

# ==========================================================
# Load
# ==========================================================

df = pd.read_csv(INPUT_FILE)

print(f"\nLoaded {len(df)} compounds")

validated = []
invalid = []

# ==========================================================
# Validate structures
# ==========================================================

for _, row in df.iterrows():

    smiles = str(row.get("Canonical_SMILES", "")).strip()

    compound = row.get("Compound_Name", "")

    if smiles == "" or smiles.lower() == "nan":

        row["Validation_Status"] = "Missing SMILES"

        invalid.append(row)

        continue

    try:

        mol = Chem.MolFromSmiles(smiles)

        if mol is None:

            row["Validation_Status"] = "Invalid SMILES"

            invalid.append(row)

            continue

        # Canonical RDKit SMILES
        row["RDKit_SMILES"] = Chem.MolToSmiles(
            mol,
            canonical=True
        )

        # InChIKey
        row["RDKit_InChIKey"] = Chem.MolToInchiKey(mol)

        # Exact MW
        row["ExactMolWt"] = round(
            Descriptors.ExactMolWt(mol),
            4
        )

        # Atom counts
        row["NumAtoms"] = mol.GetNumAtoms()

        row["HeavyAtomCount"] = mol.GetNumHeavyAtoms()

        # Ring count
        row["RingCount"] = rdMolDescriptors.CalcNumRings(mol)

        # Formal charge
        row["FormalCharge"] = Chem.GetFormalCharge(mol)

        row["Validation_Status"] = "Valid"

        validated.append(row)

    except Exception as e:

        row["Validation_Status"] = str(e)

        invalid.append(row)

# ==========================================================
# Convert
# ==========================================================

validated_df = pd.DataFrame(validated)

invalid_df = pd.DataFrame(invalid)

# ==========================================================
# Remove duplicate structures
# ==========================================================

duplicates = validated_df[
    validated_df.duplicated(
        subset="RDKit_InChIKey",
        keep="first"
    )
]

validated_df = validated_df.drop_duplicates(
    subset="RDKit_InChIKey",
    keep="first"
)

# ==========================================================
# Save
# ==========================================================

validated_df.to_csv(
    OUTPUT_FILE,
    index=False
)

invalid_df.to_csv(
    INVALID_FILE,
    index=False
)

duplicates.to_csv(
    DUPLICATE_FILE,
    index=False
)

# ==========================================================
# Summary
# ==========================================================

print("\n========== VALIDATION SUMMARY ==========")

print(f"Input molecules      : {len(df)}")
print(f"Valid molecules      : {len(validated_df)}")
print(f"Invalid molecules    : {len(invalid_df)}")
print(f"Duplicate structures : {len(duplicates)}")

print("\nSaved:")

print(f"✓ {OUTPUT_FILE}")
print(f"✓ {INVALID_FILE}")
print(f"✓ {DUPLICATE_FILE}")

print("\nDone!")