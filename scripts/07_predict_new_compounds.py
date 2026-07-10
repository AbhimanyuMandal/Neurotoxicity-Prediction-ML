"""
08_predict_new_compounds.py

Predict neurotoxicity of new compounds from SMILES.

Input:
    data/new_compounds.csv

Output:
    reports/prediction_report.csv
"""

from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

import joblib
import numpy as np
import pandas as pd

from rdkit import Chem
from rdkit.Chem import Descriptors


# ======================================================
# PATHS
# ======================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "new_compounds.csv"

MODEL_FILE = BASE_DIR / "models" / "best_model.joblib"

FEATURE_FILE = BASE_DIR / "models" / "feature_columns.pkl"

OUTPUT_FILE = BASE_DIR / "reports" / "prediction_report.csv"


# ======================================================
# LOAD MODEL
# ======================================================

print("Loading trained model...")

model = joblib.load(MODEL_FILE)

feature_columns = joblib.load(FEATURE_FILE)


# ======================================================
# LOAD DATA
# ======================================================

df = pd.read_csv(INPUT_FILE)

print(f"Loaded {len(df)} compounds.")


# ======================================================
# RDKit descriptor list
# ======================================================

descriptor_list = Descriptors.descList


# ======================================================
# Generate descriptors
# ======================================================

rows = []

for _, row in df.iterrows():

    smiles = row["SMILES"]

    mol = Chem.MolFromSmiles(smiles)

    if mol is None:

        print(f"Skipping invalid SMILES: {smiles}")

        continue

    descriptor_values = {}

    for name, func in descriptor_list:

        try:

            descriptor_values[name] = func(mol)

        except Exception:

            descriptor_values[name] = np.nan

    descriptor_values["Compound_Name"] = row["Compound_Name"]

    rows.append(descriptor_values)


descriptor_df = pd.DataFrame(rows)


# ======================================================
# Remove unstable descriptors
# ======================================================

REMOVE = [

    "Ipc",

    "AvgIpc",

    "BalabanJ",

    "BertzCT",

]

existing = [

    c

    for c in REMOVE

    if c in descriptor_df.columns

]

descriptor_df.drop(

    columns=existing,

    inplace=True,

    errors="ignore"

)


# ======================================================
# Keep only training descriptors
# ======================================================

X = descriptor_df.copy()

X = X.drop(

    columns=["Compound_Name"],

    errors="ignore"

)

X = X.apply(

    pd.to_numeric,

    errors="coerce"

)

X = X.replace(

    [np.inf, -np.inf],

    np.nan

)

X = X.fillna(

    X.median(numeric_only=True)

)

# Add missing descriptors if necessary

for col in feature_columns:

    if col not in X.columns:

        X[col] = 0

# Keep correct order

X = X[feature_columns]


# ======================================================
# Prediction
# ======================================================

prediction = model.predict(X)

probability = model.predict_proba(X)


# ======================================================
# Build prediction report
# ======================================================

results = pd.DataFrame({
    "Compound_Name": descriptor_df["Compound_Name"],

    "Prediction": np.where(
        prediction == 1,
        "Neurotoxic",
        "Neuroprotective"
    ),

    "Confidence": np.max(
        probability,
        axis=1
    ).round(4),

    "Neuroprotective_Probability": probability[:, 0].round(4),

    "Neurotoxic_Probability": probability[:, 1].round(4),
})

# ---------------------------------------
# Assign Risk Level
# ---------------------------------------

def get_risk(prob):

    if prob >= 0.90:
        return "🔴 High"

    elif prob >= 0.70:
        return "🟠 Medium"

    else:
        return "🟢 Low"

results["Risk_Level"] = results[
    "Neurotoxic_Probability"
].apply(get_risk)

# Rearrange columns

results = results[
    [
        "Compound_Name",
        "Prediction",
        "Risk_Level",
        "Confidence",
        "Neuroprotective_Probability",
        "Neurotoxic_Probability",
    ]
]

results.to_csv(

    OUTPUT_FILE,

    index=False

)

# ======================================================
# PROFESSIONAL HTML REPORT
# ======================================================

from datetime import datetime

html_file = BASE_DIR / "reports" / "prediction_report.html"

total = len(results)
neurotoxic = (results["Prediction"] == "Neurotoxic").sum()
neuroprotective = (results["Prediction"] == "Neuroprotective").sum()
avg_conf = results["Confidence"].mean() * 100

# --------------------------------------------------
# Format display values
# --------------------------------------------------

display = results.copy()

display["Confidence"] = (display["Confidence"] * 100).round(1)

display["Neuroprotective_Probability"] = (
    display["Neuroprotective_Probability"] * 100
).round(1)

display["Neurotoxic_Probability"] = (
    display["Neurotoxic_Probability"] * 100
).round(1)


def risk_badge(r):

    if "High" in r:
        return '<span class="high">High</span>'

    elif "Medium" in r:
        return '<span class="medium">Medium</span>'

    else:
        return '<span class="low">Low</span>'


def prediction_color(p):

    if p == "Neurotoxic":
        return '<span class="danger">Neurotoxic</span>'

    return '<span class="safe">Neuroprotective</span>'


def confidence_bar(v):

    return f"""
    <div class="bar">
        <div class="fill" style="width:{v}%">
            {v:.1f}%
        </div>
    </div>
    """


table = ""

for _, row in display.iterrows():

    table += f"""
<tr>

<td>{row['Compound_Name']}</td>

<td>{prediction_color(row['Prediction'])}</td>

<td>{risk_badge(row['Risk_Level'])}</td>

<td>{confidence_bar(row['Confidence'])}</td>

<td>{row['Neuroprotective_Probability']}%</td>

<td>{row['Neurotoxic_Probability']}%</td>

</tr>
"""

html = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="utf-8">

<title>Neurotoxicity Prediction ML Report</title>

<style>

body{{
font-family:Arial;
background:#f5f7fa;
margin:40px;
}}

.header{{
background:white;
padding:30px;
border-radius:12px;
box-shadow:0 2px 8px rgba(0,0,0,.08);
margin-bottom:25px;
}}

h1{{
color:#234e7d;
}}

.cards{{
display:flex;
gap:20px;
margin-top:20px;
margin-bottom:30px;
flex-wrap:wrap;
}}

.card{{
background:white;
padding:20px;
width:180px;
text-align:center;
border-radius:10px;
box-shadow:0 2px 8px rgba(0,0,0,.08);
}}

.card h2{{
margin:0;
color:#1f77b4;
}}

.card p{{
font-size:14px;
color:#666;
}}

table{{
width:100%;
border-collapse:collapse;
background:white;
box-shadow:0 2px 8px rgba(0,0,0,.08);
}}

th{{
background:#1f77b4;
color:white;
padding:12px;
position:sticky;
top:0;
}}

td{{
padding:10px;
text-align:center;
border-bottom:1px solid #ddd;
}}

tr:nth-child(even){{
background:#f8f8f8;
}}

.high{{
background:#dc3545;
color:white;
padding:6px 14px;
border-radius:20px;
font-weight:bold;
}}

.medium{{
background:#fd7e14;
color:white;
padding:6px 14px;
border-radius:20px;
font-weight:bold;
}}

.low{{
background:#198754;
color:white;
padding:6px 14px;
border-radius:20px;
font-weight:bold;
}}

.safe{{
color:#198754;
font-weight:bold;
}}

.danger{{
color:#dc3545;
font-weight:bold;
}}

.bar{{
background:#ddd;
height:22px;
border-radius:20px;
overflow:hidden;
}}

.fill{{
background:#1f77b4;
height:100%;
color:white;
font-size:12px;
line-height:22px;
}}

.footer{{
margin-top:35px;
background:white;
padding:20px;
border-radius:10px;
box-shadow:0 2px 8px rgba(0,0,0,.08);
}}

small{{
color:#666;
}}

</style>

</head>

<body>

<div class="header">

<h1>🧬 Neurotoxicity Prediction Report</h1>

<p>

<b>Model Used:</b> Logistic Regression<br>

<b>Prediction Date:</b> {datetime.now().strftime("%d %b %Y %H:%M")}<br>

<b>RDKit Descriptors:</b> 170

</p>

</div>

<div class="cards">

<div class="card">
<h2>{total}</h2>
<p>Total Compounds</p>
</div>

<div class="card">
<h2>{neurotoxic}</h2>
<p>Neurotoxic</p>
</div>

<div class="card">
<h2>{neuroprotective}</h2>
<p>Neuroprotective</p>
</div>

<div class="card">
<h2>{avg_conf:.1f}%</h2>
<p>Average Confidence</p>
</div>

</div>

<table>

<tr>

<th>Compound</th>

<th>Prediction</th>

<th>Risk</th>

<th>Confidence</th>

<th>Neuroprotective</th>

<th>Neurotoxic</th>

</tr>

{table}

</table>

<div class="footer">

<b>Disclaimer</b>

<p>

This report was generated using the Neurotoxicity Prediction ML pipeline.
Predictions are intended for research purposes only and should not replace
experimental validation.

</p>

<hr>
  s
<small>

Developed by <b>Abhimanyu Mandal</b><br>

Computational Biology • Cheminformatics • Machine Learning

</small>

</div>

</body>

</html>
"""

with open(html_file, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nHTML report saved to:\n{html_file}")