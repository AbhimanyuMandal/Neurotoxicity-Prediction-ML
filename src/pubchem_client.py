"""
Reusable PubChem API Client
"""

import time
import requests

BASE_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name"
)

PROPERTIES = ",".join([
    "CanonicalSMILES",
    "IsomericSMILES",
    "MolecularFormula",
    "MolecularWeight",
    "InChI",
    "InChIKey",
    "IUPACName",
    "XLogP",
    "TPSA",
    "HBondDonorCount",
    "HBondAcceptorCount",
    "RotatableBondCount",
    "HeavyAtomCount"
])


class PubChemClient:

    def __init__(self, delay=0.2, timeout=20):
        self.delay = delay
        self.timeout = timeout

    def get_compound(self, compound_name):

        url = (
            f"{BASE_URL}/{compound_name}"
            f"/property/{PROPERTIES}/JSON"
        )

        try:

            response = requests.get(
                url,
                timeout=self.timeout
            )

            response.raise_for_status()

            data = response.json()

            props = data["PropertyTable"]["Properties"][0]

            props["Status"] = "Success"

            time.sleep(self.delay)

            return props

        except Exception as e:

            return {
                "Status": f"Error: {e}"
            }