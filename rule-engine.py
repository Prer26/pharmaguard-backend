# rule_engine.py

from phenotype_engine import (
    calculate_phenotype,
    get_diplotype,
    get_activity_score
)


# -----------------------------
# WARFARIN DOSE CALCULATION
# -----------------------------
def calculate_warfarin_dose(cyp_pheno, vkorc1_pheno):
    base_dose = 5.0  # mg/day baseline

    # CYP2C9 metabolism
    if cyp_pheno == "PM":
        base_dose *= 0.4
    elif cyp_pheno == "IM":
        base_dose *= 0.7

    # VKORC1 sensitivity
    if vkorc1_pheno == "High Sensitivity":
        base_dose *= 0.5
    elif vkorc1_pheno == "Moderate Sensitivity":
        base_dose *= 0.8

    return round(base_dose, 2)


# -----------------------------
# DRUG CONFIG
# -----------------------------
DRUG_RULES = {

    "CODEINE": {
        "gene": "CYP2D6",
        "type": "cyp",
        "pm": ("Ineffective", "Avoid codeine"),
        "im": ("Reduced Response", "Use lower dose"),
        "nm": ("Safe", "Standard dosing"),
        "um": ("Toxicity Risk", "Avoid or reduce dose"),
    },

    "CLOPIDOGREL": {
        "gene": "CYP2C19",
        "type": "cyp",
        "pm": ("Ineffective", "Use alternative drug"),
        "im": ("Reduced Response", "Consider alternative"),
        "nm": ("Safe", "Standard dosing"),
    },

    "SIMVASTATIN": {
        "gene": "SLCO1B1",
        "type": "slco",
        "low": ("Myopathy Risk", "Lower dose"),
        "normal": ("Safe", "Standard dosing"),
    },

    "ABACAVIR": {
        "gene": "HLA-B",
        "type": "hla",
        "positive": ("Severe Hypersensitivity", "Avoid drug"),
        "negative": ("Safe", "Standard use"),
    },

    # 🧬 MULTI-GENE WARFARIN
    "WARFARIN": {
        "gene": ["CYP2C9", "VKORC1"],
        "type": "multi"
    },
}


# -----------------------------
# DEFAULT RESPONSE
# -----------------------------
def default_response(variants):
    return {
        "risk": "Safe",
        "severity": "none",
        "gene": "N/A",
        "diplotype": {},
        "phenotype": {},
        "activity_score": 0,
        "variants": variants,
        "recommendation": "Standard dosing",
    }


# -----------------------------
# MAIN FUNCTION
# -----------------------------
def analyze_variants(variants, drug):

    drug = drug.upper()

    if drug not in DRUG_RULES:
        return default_response(variants)

    config = DRUG_RULES[drug]
    rule_type = config["type"]

    # -----------------------------
    # MULTI-GENE WARFARIN
    # -----------------------------
    if rule_type == "multi":

        cyp_stars = [v.get("star") for v in variants if v.get("gene") == "CYP2C9"]
        vkorc1_stars = [v.get("star") for v in variants if v.get("gene") == "VKORC1"]

        cyp_pheno = calculate_phenotype("CYP2C9", cyp_stars)
        vkorc1_pheno = calculate_phenotype("VKORC1", vkorc1_stars)

        dose = calculate_warfarin_dose(cyp_pheno, vkorc1_pheno)

        if cyp_pheno == "PM" or vkorc1_pheno == "High Sensitivity":
            risk = "Very High Bleeding Risk"
            rec = "Strongly reduce dose"
            severity = "high"

        elif cyp_pheno == "IM" or vkorc1_pheno == "Moderate Sensitivity":
            risk = "Moderate Bleeding Risk"
            rec = "Adjust dose"
            severity = "moderate"

        else:
            risk = "Normal"
            rec = "Standard dosing"
            severity = "none"

        return {
            "risk": risk,
            "severity": severity,

            "gene": "CYP2C9 + VKORC1",

            "diplotype": {
                "CYP2C9": "/".join(cyp_stars) if cyp_stars else "*1/*1",
                "VKORC1": ",".join(vkorc1_stars) if vkorc1_stars else "GG"
            },

            "phenotype": {
                "CYP2C9": cyp_pheno,
                "VKORC1": vkorc1_pheno
            },

            "activity_score": get_activity_score(cyp_stars),
            "estimated_dose_mg_per_day": dose,

            "variants": variants,
            "recommendation": rec,
        }

    # -----------------------------
    # SINGLE GENE LOGIC
    # -----------------------------
    gene = config["gene"]

    stars = [v.get("star") for v in variants if v.get("gene") == gene]

    phenotype = calculate_phenotype(gene, stars)
    diplotype = get_diplotype(stars)
    activity_score = get_activity_score(stars)

    if rule_type == "cyp":

        if phenotype == "PM":
            risk, rec = config["pm"]
            severity = "high"
        elif phenotype == "IM":
            risk, rec = config["im"]
            severity = "moderate"
        elif phenotype == "UM":
            risk, rec = config.get("um", ("Unknown", "Consult"))
            severity = "moderate"
        else:
            risk, rec = config["nm"]
            severity = "none"

    elif rule_type == "hla":

        if phenotype == "Positive":
            risk, rec = config["positive"]
            severity = "high"
        else:
            risk, rec = config["negative"]
            severity = "none"

    elif rule_type == "slco":

        if phenotype == "Low Function":
            risk, rec = config["low"]
            severity = "moderate"
        else:
            risk, rec = config["normal"]
            severity = "none"

    else:
        return default_response(variants)

    return {
        "risk": risk,
        "severity": severity,

        "gene": gene,

        "diplotype": {
            gene: diplotype
        },

        "phenotype": {
            gene: phenotype
        },

        "activity_score": activity_score,
        "variants": variants,
        "recommendation": rec,
    }


# -----------------------------
# TEST
# -----------------------------
if __name__ == "__main__":

    sample = [
        {"gene": "CYP2C9", "star": "*3"},
        {"gene": "VKORC1", "star": "AA"}
    ]

    print(analyze_variants(sample, "WARFARIN"))