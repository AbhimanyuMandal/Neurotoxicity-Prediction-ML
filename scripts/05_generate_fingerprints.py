"""
05_generate_fingerprints.py

Generate Morgan (ECFP4) fingerprints.

Input:
    data/processed/validated_compounds.csv

Output:
    data/processed/fingerprints.csv
"""

from pathlib import Path

import pandas as pd
from tqdm import tqdm

from rdkit import Chem
from rdkit.Chem import AllChem

# ==========================================================
# Paths
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR /
    "data" /
    "processed" /
    "validated_compounds.csv"
)

OUTPUT_FILE = (
    BASE_DIR /
    "data" /
    "processed" /
    "fingerprints.csv"
)

# ==========================================================
# Parameters
# ==========================================================

RADIUS = 2
N_BITS = 2048

# ==========================================================
# Load
# ==========================================================

df = pd.read_csv(INPUT_FILE)

print(f"\nLoaded {len(df)} validated molecules.")

rows = []

# ==========================================================
# Generate fingerprints
# ==========================================================

for _, row in tqdm(df.iterrows(), total=len(df)):

    smiles = row["RDKit_SMILES"]

    mol = Chem.MolFromSmiles(smiles)

    if mol is None:
        continue

    fp = AllChem.GetMorganFingerprintAsBitVect(
        mol,
        radius=RADIUS,
        nBits=N_BITS
    )

    bits = list(fp)

    fingerprint = {
        "Compound_Name": row["Compound_Name"],
        "Label": row["Label"],
        "CID": row["CID"]
    }

    for i, bit in enumerate(bits):
        fingerprint[f"Bit_{i}"] = bit

    rows.append(fingerprint)

# ==========================================================
# Save
# ==========================================================

fingerprint_df = pd.DataFrame(rows)

fingerprint_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n========== SUMMARY ==========")

print(f"Molecules processed : {len(fingerprint_df)}")
print(f"Fingerprint size    : {N_BITS}")

print("\nSaved:")

print(OUTPUT_FILE)

print("\nDone!")