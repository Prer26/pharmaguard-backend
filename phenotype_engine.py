# phenotype_engine.py

# -----------------------------
# ACTIVITY SCORE MAP
# -----------------------------
ALLELE_ACTIVITY = {
    # CYP2D6
    "*1": 1.0,
    "*2": 1.0,
    "*4": 0.0,
    "*5": 0.0,
    "*10": 0.25,
    "*17": 0.5,

    # CYP2C19
    "*1": 1.0,
    "*2": 0.0,
    "*3": 0.0,
    "*17": 1.5,

    # CYP2C9
    "*1": 1.0,
    "*2": 0.5,
    "*3": 0.0,
}


# -----------------------------
# ACTIVITY SCORE
# -----------------------------
def get_activity_score(stars):
    if not stars:
        return 2.0  # assume normal baseline

    return sum(ALLELE_ACTIVITY.get(s, 1.0) for s in stars)


# -----------------------------
# PHENOTYPE CALCULATION
# -----------------------------
def calculate_phenotype(gene, stars):

    if not stars:
        return "Unknown"

    score = get_activity_score(stars)

    # -----------------------------
    # CYP2D6
    # -----------------------------
    if gene == "CYP2D6":
        if score == 0:
            return "PM"
        elif score <= 1:
            return "IM"
        elif score == 2:
            return "NM"
        else:
            return "UM"

    # -----------------------------
    # CYP2C19
    # -----------------------------
    if gene == "CYP2C19":
        if score == 0:
            return "PM"
        elif score <= 1:
            return "IM"
        elif score == 2:
            return "NM"
        else:
            return "UM"

    # -----------------------------
    # CYP2C9
    # -----------------------------
    if gene == "CYP2C9":
        if score == 0:
            return "PM"
        elif score < 1.5:
            return "IM"
        else:
            return "NM"

    # -----------------------------
    # HLA GENES (risk marker, not enzyme)
    # -----------------------------
    if gene == "HLA-B":
        return "Positive" if stars else "Negative"
    
    if gene == "VKORC1":
        if "AA" in stars:
            return "High Sensitivity"
        elif "GA" in stars:
            return "Moderate Sensitivity"
        else:
            return "Normal"


    # -----------------------------
    # SLCO1B1
    # -----------------------------
    if gene == "SLCO1B1":
        if "*5" in stars or "*15" in stars:
            return "Low Function"
        return "Normal"

    return "Unknown"

    
# -----------------------------
# DIPLOTYPE
# -----------------------------
def get_diplotype(stars):
    if not stars:
        return "*1/*1"
    return "/".join(stars)