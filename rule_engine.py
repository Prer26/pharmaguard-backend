# -----------------------------
# PHENOTYPE LOGIC
# -----------------------------
def get_phenotype(gene: str, star: str):
    star = (star or "").lower()

    if gene == "CYP2C19":
        if "*2" in star or "*3" in star:
            return "Poor Metabolizer"
        elif "*1" in star:
            return "Normal Metabolizer"
        return "Intermediate Metabolizer"

    if gene == "CYP2C9":
        if "*3" in star:
            return "Poor Metabolizer"
        elif "*2" in star:
            return "Intermediate Metabolizer"
        return "Normal Metabolizer"

    if gene == "CYP2D6":
        if "xn" in star or "dup" in star:
            return "Ultra Rapid Metabolizer"
        elif "*4" in star:
            return "Poor Metabolizer"
        return "Normal Metabolizer"

    if gene == "SLCO1B1":
        if "*5" in star:
            return "Poor Transporter"
        return "Normal Transporter"

    if gene == "HLA-B":
        if "15:02" in star or "57:01" in star:
            return "High Risk"
        return "Normal"

    return "Unknown"


# -----------------------------
# SMART VARIANT SELECTION 🔥
# -----------------------------
def select_variant_for_drug(variants, drug):
    drug = drug.upper()

    for v in variants:
        gene = v.get("gene")

        if drug == "CLOPIDOGREL" and gene == "CYP2C19":
            return v

        if drug == "WARFARIN" and gene == "CYP2C9":
            return v

        if drug == "CODEINE" and gene == "CYP2D6":
            return v

        if drug == "SIMVASTATIN" and gene == "SLCO1B1":
            return v

        if drug in ["CARBAMAZEPINE", "ABACAVIR"] and gene == "HLA-B":
            return v

    # fallback
    return variants[0] if variants else {"gene": "N/A", "star": ""}


# -----------------------------
# MAIN ENGINE
# -----------------------------
def analyze_variants(variants, drug):
    drug = drug.upper()

    # 🔥 FIXED: correct variant selection
    variant = select_variant_for_drug(variants, drug)

    gene = variant.get("gene", "N/A")
    star = variant.get("star", "")
    diplotype = star if star else "*1/*1"

    phenotype = get_phenotype(gene, star)

    # =====================================================
    # 🩸 WARFARIN
    # =====================================================
    if drug == "WARFARIN":
        if phenotype == "Poor Metabolizer":
            return {
                "risk": "Adjust Dosage",
                "severity": "high",
                "gene": gene,
                "diplotype": diplotype,
                "phenotype": phenotype,
                "recommendation": "Reduce dose significantly and monitor INR"
            }

        elif phenotype == "Intermediate Metabolizer":
            return {
                "risk": "Adjust Dosage",
                "severity": "medium",
                "gene": gene,
                "diplotype": diplotype,
                "phenotype": phenotype,
                "recommendation": "Moderate dose reduction required"
            }

        return {
            "risk": "Safe",
            "severity": "low",
            "gene": gene,
            "diplotype": diplotype,
            "phenotype": phenotype,
            "recommendation": "Standard dosing recommended"
        }

    # =====================================================
    # ❤️ CLOPIDOGREL (CORRECTED 🔥)
    # =====================================================
    if drug == "CLOPIDOGREL":
        if phenotype == "Poor Metabolizer":
            return {
                "risk": "Ineffective Drug",
                "severity": "high",
                "gene": gene,
                "diplotype": diplotype,
                "phenotype": phenotype,
                "recommendation": "Use alternative: prasugrel or ticagrelor"
            }

        elif phenotype == "Intermediate Metabolizer":
            return {
                "risk": "Reduced Efficacy",
                "severity": "medium",
                "gene": gene,
                "diplotype": diplotype,
                "phenotype": phenotype,
                "recommendation": "Consider alternative therapy"
            }

        return {
            "risk": "Safe",
            "severity": "low",
            "gene": gene,
            "diplotype": diplotype,
            "phenotype": phenotype,
            "recommendation": "Standard dosing recommended"
        }

    # =====================================================
    # 😴 CODEINE
    # =====================================================
    if drug == "CODEINE":
        if phenotype == "Ultra Rapid Metabolizer":
            return {
                "risk": "Toxic",
                "severity": "high",
                "gene": gene,
                "diplotype": diplotype,
                "phenotype": phenotype,
                "recommendation": "Avoid codeine"
            }

        elif phenotype == "Poor Metabolizer":
            return {
                "risk": "Ineffective Drug",
                "severity": "medium",
                "gene": gene,
                "diplotype": diplotype,
                "phenotype": phenotype,
                "recommendation": "Use alternative analgesic"
            }

        return {
            "risk": "Safe",
            "severity": "low",
            "gene": gene,
            "diplotype": diplotype,
            "phenotype": phenotype,
            "recommendation": "Standard dosing"
        }

    # =====================================================
    # 🧠 CARBAMAZEPINE
    # =====================================================
    if drug == "CARBAMAZEPINE":
        if phenotype == "High Risk":
            return {
                "risk": "Contraindicated",
                "severity": "high",
                "gene": gene,
                "diplotype": diplotype,
                "phenotype": phenotype,
                "recommendation": "DO NOT USE"
            }

        return {
            "risk": "Safe",
            "severity": "low",
            "gene": gene,
            "diplotype": diplotype,
            "phenotype": phenotype,
            "recommendation": "Standard dosing"
        }

    # =====================================================
    # 💪 SIMVASTATIN
    # =====================================================
    if drug == "SIMVASTATIN":
        if phenotype == "Poor Transporter":
            return {
                "risk": "Toxic",
                "severity": "medium",
                "gene": gene,
                "diplotype": diplotype,
                "phenotype": phenotype,
                "recommendation": "Reduce dose or switch statin"
            }

        return {
            "risk": "Safe",
            "severity": "low",
            "gene": gene,
            "diplotype": diplotype,
            "phenotype": phenotype,
            "recommendation": "Standard dosing"
        }

    # =====================================================
    # DEFAULT
    # =====================================================
    return {
        "risk": "Unknown",
        "severity": "low",
        "gene": gene,
        "diplotype": diplotype,
        "phenotype": phenotype,
        "recommendation": "No guideline available"
    }