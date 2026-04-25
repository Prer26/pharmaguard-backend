TARGET_GENES = ["CYP2D6","CYP2C19","CYP2C9","SLCO1B1","TPMT","DPYD"]

def parse_vcf(lines):
    variants = []

    for line in lines:
        if line.startswith("#") or not line.strip():
            continue

        cols = line.split("\t")

        if len(cols) < 8:
            continue

        rsid = cols[2]
        info = cols[7]

        gene = None

        for item in info.split(";"):
            if item.startswith("GENE="):
                gene = item.split("=")[1]

        if gene in TARGET_GENES:
            variants.append({
                "gene": gene,
                "rsid": rsid
            })

    return variants