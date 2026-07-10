"""
02_fetch_pubchem.py

Retrieve molecular information from PubChem.

Input:
    data/processed/candidate_compounds_clean.csv

Outputs:
    data/processed/pubchem_compounds.csv
    data/reports/pubchem_failures.csv
"""

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import pandas as pd
from tqdm import tqdm

from src.pubchem_client import PubChemClient

# ----------------------------------------------------
# Paths
# ----------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "candidate_compounds_clean.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "pubchem_compounds.csv"
)

FAILURE_FILE = (
    BASE_DIR
    / "data"
    / "reports"
    / "pubchem_failures.csv"
)

# ----------------------------------------------------
# Load data
# ----------------------------------------------------

df = pd.read_csv(INPUT_FILE)

print(f"\nLoaded {len(df)} compounds")

# ----------------------------------------------------
# PubChem client
# ----------------------------------------------------

client = PubChemClient()

results = []
failures = []

# ----------------------------------------------------
# Retrieve compounds
# ----------------------------------------------------

for _, row in tqdm(df.iterrows(), total=len(df), desc="Querying PubChem"):

    compound = str(row["Compound_Name"]).strip()

    label = row.get("Label", "")

    compound_class = row.get("Class", "")

    category = row.get("Category", "")

    try:

        info = client.get_compound(compound)

        if (
            "Status" in info
            and str(info["Status"]).lower().startswith("error")
        ):

            failures.append({

                "Compound_Name": compound,

                "Reason": info["Status"]

            })

            continue

        info["Compound_Name"] = compound
        info["Label"] = label
        info["Class"] = compound_class
        info["Category"] = category

        results.append(info)

    except Exception as e:

        failures.append({

            "Compound_Name": compound,

            "Reason": str(e)

        })

# ----------------------------------------------------
# Save
# ----------------------------------------------------

results_df = pd.DataFrame(results)

# rename for consistency

results_df.rename(
    columns={
        "SMILES": "Canonical_SMILES",
        "ConnectivitySMILES": "Connectivity_SMILES",
    },
    inplace=True,
)

results_df.to_csv(
    OUTPUT_FILE,
    index=False,
)

pd.DataFrame(failures).to_csv(
    FAILURE_FILE,
    index=False,
)

# ----------------------------------------------------
# Summary
# ----------------------------------------------------

print("\n========== PUBCHEM SUMMARY ==========")

print(f"Input compounds      : {len(df)}")
print(f"Successful retrieval : {len(results_df)}")
print(f"Failed retrieval     : {len(failures)}")

print("\nSaved:")

print(f"  ✓ {OUTPUT_FILE}")

print(f"  ✓ {FAILURE_FILE}")

print("\nDone!")