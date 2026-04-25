from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging

from vcf_parser import parse_vcf
from rule_engine import analyze_variants
from llm_engine import generate_explanation
from gene_mapper import get_genes_for_drug

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PharmaGuard API")

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# DRUG ALIASES
# -----------------------------
DRUG_ALIASES = {
    "CODEINE": "CODEINE",
    "CLOPIDOGREL": "CLOPIDOGREL",
    "WARFARIN": "WARFARIN",
    "OMEPRAZOLE": "OMEPRAZOLE",
    "TAMOXIFEN": "TAMOXIFEN",
    "PHENYTOIN": "PHENYTOIN",
    "SIMVASTATIN": "SIMVASTATIN",
    "ABACAVIR": "ABACAVIR",
    "CARBAMAZEPINE": "CARBAMAZEPINE",
    "AZATHIOPRINE": "AZATHIOPRINE",
    "ALLOPURINOL": "ALLOPURINOL",
}

# -----------------------------
# HEALTH CHECK
# -----------------------------
@app.get("/")
def home():
    return {"message": "PharmaGuard API running 🚀"}

# -----------------------------
# UTILS
# -----------------------------
def calculate_confidence(num_variants: int) -> float:
    if num_variants == 0:
        return 0.75
    if num_variants == 1:
        return 0.88
    return 0.95


def normalize_risk_level(risk_label: str, severity: str) -> str:
    risk_lower = (risk_label or "").lower()

    if "safe" in risk_lower:
        return "low"
    if "toxic" in risk_lower:
        return "high"
    if "ineffective" in risk_lower:
        return "high"
    if "adjust" in risk_lower:
        return "medium"

    return severity if severity else "low"


# -----------------------------
# MAIN API
# -----------------------------
@app.post("/analyze")
async def analyze(request: Request):
    try:
        form = await request.form()

        # 🔥 MULTI DRUG SUPPORT
        drug_list = form.getlist("drug")

        # fallback (comma separated)
        if not drug_list:
            raw = form.get("drug")
            if raw:
                drug_list = raw.split(",")

        gene = form.get("gene")
        variant = form.get("variant")
        file = form.get("file")
        mode = form.get("mode", "clinical")

        logger.info(f"Request: drugs={drug_list}, gene={gene}, variant={variant}")

        # -----------------------------
        # VALIDATION
        # -----------------------------
        if not drug_list:
            return {"error": "Drug is required"}

        drugs = [
            DRUG_ALIASES.get(d.strip().upper(), d.strip().upper())
            for d in drug_list
            if d.strip()
        ]

        # -----------------------------
        # GET VARIANTS
        # -----------------------------
        variants = []

        # 📂 FILE MODE
        if file and hasattr(file, "file"):
            content = await file.read()

            if len(content) == 0:
                return {"error": "Empty file uploaded"}

            text = content.decode("utf-8", errors="ignore")
            variants = parse_vcf(text.split("\n"))

        # ✍️ MANUAL MODE
        else:
            if not variant:
                return {"error": "Provide VCF file OR variant input"}

            # 🔥 AUTO GENE MAP
            if not gene:
                auto_genes = []

                for d in drugs:
                    mapped = get_genes_for_drug(d)
                    auto_genes.extend(mapped)

                auto_genes = list(set(auto_genes))

                if not auto_genes:
                    return {"error": "No gene mapping found"}

                variants = [
                    {"gene": g, "star": variant, "rsid": "auto"}
                    for g in auto_genes
                ]

            else:
                variants = [
                    {"gene": gene.upper(), "star": variant, "rsid": "manual"}
                ]

        # -----------------------------
        # PROCESS DRUGS
        # -----------------------------
        results = []

        for d in drugs:
            analysis = analyze_variants(variants, d)

            # 🔥 LLM
            try:
                explanation = generate_explanation(analysis, mode=mode)
            except Exception as e:
                logger.error(f"LLM error: {e}")
                explanation = {
                    "summary": "",
                    "mechanism": "",
                    "clinical_impact": "",
                    "recommendation": analysis.get("recommendation", "")
                }

            # 🔥 CONFIDENCE
            relevant_variants = [
                v for v in variants if v.get("gene") == analysis.get("gene")
            ]
            confidence = calculate_confidence(len(relevant_variants))

            # 🔥 NORMALIZE RISK
            severity = normalize_risk_level(
                analysis.get("risk", ""),
                analysis.get("severity", "low")
            )

            result = {
                "patient_id": "PATIENT_001",
                "drug": d,
                "timestamp": datetime.utcnow().isoformat(),

                "risk_assessment": {
                    "risk_label": analysis.get("risk", "Unknown"),
                    "confidence_score": confidence,
                    "severity": severity
                },

                "pharmacogenomic_profile": {
                    "primary_gene": analysis.get("gene", "N/A"),
                    "diplotype": analysis.get("diplotype", "N/A"),
                    "phenotype": analysis.get("phenotype", "Unknown"),
                },

                "clinical_recommendation": {
                    "action": analysis.get("recommendation", ""),
                    "guideline": "CPIC"
                },

                "llm_generated_explanation": explanation,
            }

            results.append(result)

        # -----------------------------
        # RETURN
        # -----------------------------
        if len(results) == 1:
            return results[0]

        return {"results": results}

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return {"error": str(e)}