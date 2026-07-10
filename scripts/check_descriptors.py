import pandas as pd
import numpy as np

df = pd.read_csv("data/processed/rdkit_descriptors.csv")

metadata = [
    "Compound_Name",
    "Label",
    "CID",
    "Canonical_SMILES",
    "MolecularFormula",
    "MolecularWeight",
    "InChIKey",
]

metadata = [c for c in metadata if c in df.columns]

X = df.drop(columns=metadata)

print("=" * 50)
print("Descriptor Quality Check")
print("=" * 50)

print("Shape:", X.shape)
print("NaN values:", X.isna().sum().sum())
print("Infinite values:", np.isinf(X.values).sum())

print("\nLargest value:")
print(X.max().max())

print("\nSmallest value:")
print(X.min().min())

print("\nLabel Distribution")
print(df["Label"].value_counts())