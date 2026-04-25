def get_genes_for_drug(drug: str):
    drug = drug.upper()

    DRUG_GENE_MAP = {
        "WARFARIN": ["CYP2C9", "VKORC1"],
        "CLOPIDOGREL": ["CYP2C19"],  # ✅ CRITICAL FIX
        "CODEINE": ["CYP2D6"],
        "SIMVASTATIN": ["SLCO1B1"],
        "PHENYTOIN": ["CYP2C9"],
        "OMEPRAZOLE": ["CYP2C19"],
        "TAMOXIFEN": ["CYP2D6"],
        "ABACAVIR": ["HLA-B"],
        "CARBAMAZEPINE": ["HLA-B"],
        "ALLOPURINOL": ["HLA-B"],
        "AZATHIOPRINE": ["TPMT"],
    }

    return DRUG_GENE_MAP.get(drug, [])