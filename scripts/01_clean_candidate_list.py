"""
01_clean_candidate_list.py

Clean candidate compounds before PubChem retrieval.

Features
--------
✓ Remove parentheses
✓ Remove salt forms
✓ Standardize compound names
✓ Remove biologics/peptides/antibodies
✓ Remove undefined compound classes
✓ Remove duplicate compounds
✓ Infer categories
✓ Generate cleanup report
✓ Generate removed compounds report

Input
-----
data/raw/candidate_compounds.csv

Output
------
data/processed/candidate_compounds_clean.csv
data/reports/cleanup_report.csv
data/reports/removed_compounds.csv
"""

from pathlib import Path
import pandas as pd
import re

# =====================================================
# PATHS
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "raw" / "candidate_compounds.csv"

OUTPUT_DIR = BASE_DIR / "data" / "processed"
REPORT_DIR = BASE_DIR / "data" / "reports"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# =====================================================
# LOAD
# =====================================================

df = pd.read_csv(INPUT_FILE)

print(f"\nLoaded {len(df)} compounds")

# =====================================================
# CONFIG
# =====================================================

SALT_SUFFIXES = [
    " Hydrochloride",
    " Hydrobromide",
    " Mesylate",
    " Tartrate",
    " Sodium",
    " Potassium",
    " Calcium",
    " Magnesium",
    " Acetate",
    " Citrate",
    " Maleate",
    " Succinate",
    " Phosphate",
    " Sulfate",
    " Besylate",
    " Hyclate",
    " Monohydrate",
    " Dihydrate",
    " Carbonate",
]

STANDARD_NAMES = {

    "NAC": "N-Acetylcysteine",

    "EGCG": "Epigallocatechin gallate",

    "CoQ10": "Coenzyme Q10",

    "ALA": "Alpha-Lipoic Acid",

    "DHA": "Docosahexaenoic Acid",

    "EPA": "Eicosapentaenoic Acid",

}

REMOVE_KEYWORDS = [

    "mab",

    "antibody",

    "growth factor",

    "interleukin",

    "Cerebrolysin",

    "Semaglutide",

    "Liraglutide",

    "Dulaglutide",

    "Exenatide",

    "Oxytocin",

]

REMOVE_EXACT = {

    "Anthocyanins",

    "Proanthocyanidins",

    "Curcuminoid Complex",

    "Thearubigins",

}

CATEGORY_RULES = {

    "Paclitaxel":"Taxane",
    "Docetaxel":"Taxane",
    "Cabazitaxel":"Taxane",

    "Vincristine":"Vinca Alkaloid",
    "Vinblastine":"Vinca Alkaloid",
    "Vinorelbine":"Vinca Alkaloid",

    "Cisplatin":"Platinum Chemotherapy",
    "Carboplatin":"Platinum Chemotherapy",
    "Oxaliplatin":"Platinum Chemotherapy",

    "Curcumin":"Polyphenol",
    "Resveratrol":"Polyphenol",

    "Quercetin":"Flavonoid",
    "Kaempferol":"Flavonoid",
    "Apigenin":"Flavonoid",
    "Luteolin":"Flavonoid",

    "Donepezil":"Acetylcholinesterase Inhibitor",
    "Galantamine":"Acetylcholinesterase Inhibitor",
    "Rivastigmine":"Acetylcholinesterase Inhibitor",

    "Memantine":"NMDA Receptor Antagonist",

    "Edaravone":"Free Radical Scavenger",

    "Paraquat":"Herbicide",

    "Rotenone":"Environmental Toxicant",

    "Chlorpyrifos":"Organophosphate",

}

cleanup_log = []
removed_log = []

# =====================================================
# CLEANING FUNCTIONS
# =====================================================

def remove_parentheses(name):

    cleaned = re.sub(r"\(.*?\)", "", str(name)).strip()

    if cleaned != name:

        cleanup_log.append({

            "Original":name,

            "Cleaned":cleaned,

            "Action":"Removed parentheses"

        })

    return cleaned


def remove_salts(name):

    original = name

    for salt in SALT_SUFFIXES:

        if name.endswith(salt):

            name = name.replace(salt,"").strip()

    if original != name:

        cleanup_log.append({

            "Original":original,

            "Cleaned":name,

            "Action":"Salt removed"

        })

    return name


def standardize(name):

    if name in STANDARD_NAMES:

        cleanup_log.append({

            "Original":name,

            "Cleaned":STANDARD_NAMES[name],

            "Action":"Standardized"

        })

        return STANDARD_NAMES[name]

    return name


def infer_category(name):

    return CATEGORY_RULES.get(name,"Other")


# =====================================================
# PROCESS
# =====================================================

clean_names = []

keep_rows = []

for _, row in df.iterrows():

    original = str(row["Compound_Name"]).strip()

    name = remove_parentheses(original)

    name = remove_salts(name)

    name = standardize(name)

    lower = name.lower()

    remove = False

    reason = ""

    for keyword in REMOVE_KEYWORDS:

        if keyword.lower() in lower:

            remove = True

            reason = "Filtered"

            break

    if name in REMOVE_EXACT:

        remove = True

        reason = "Compound class"

    if remove:

        removed_log.append({

            "Compound_Name":original,

            "Reason":reason

        })

        continue

    row["Compound_Name"] = name

    row["Category"] = infer_category(name)

    keep_rows.append(row)

# =====================================================
# CREATE CLEAN DATAFRAME
# =====================================================

clean_df = pd.DataFrame(keep_rows)

before = len(clean_df)

clean_df = clean_df.drop_duplicates(
    subset="Compound_Name"
)

duplicates_removed = before - len(clean_df)

clean_df = clean_df.sort_values(
    "Compound_Name"
)

# =====================================================
# SAVE
# =====================================================

clean_df.to_csv(
    OUTPUT_DIR / "candidate_compounds_clean.csv",
    index=False
)

pd.DataFrame(cleanup_log).to_csv(
    REPORT_DIR / "cleanup_report.csv",
    index=False
)

pd.DataFrame(removed_log).to_csv(
    REPORT_DIR / "removed_compounds.csv",
    index=False
)

# =====================================================
# SUMMARY
# =====================================================

print("\n========== CLEANUP SUMMARY ==========")

print(f"Original compounds : {len(df)}")
print(f"Final compounds    : {len(clean_df)}")
print(f"Duplicates removed : {duplicates_removed}")
print(f"Filtered compounds : {len(removed_log)}")
print(f"Name changes       : {len(cleanup_log)}")

print("\nSaved:")

print(OUTPUT_DIR / "candidate_compounds_clean.csv")
print(REPORT_DIR / "cleanup_report.csv")
print(REPORT_DIR / "removed_compounds.csv")

print("\nDone.")