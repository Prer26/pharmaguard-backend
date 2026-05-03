from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
import os
from dotenv import load_dotenv
from groq import Groq
import json, re

# ============================
# 🔐 ENV SETUP
# ============================
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=groq_api_key) if groq_api_key else None

app = FastAPI()

# ============================
# 🌐 CORS
# ============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================
# 🧪 LOAD ML MODEL (SAFE)
# ============================
try:
    model = joblib.load("models/pharmaguard_model.pkl")
    encoders = joblib.load("models/encoders.pkl")
    target_encoder = joblib.load("models/target_encoder.pkl")
    print("✅ ML model loaded")
except Exception as e:
    print("❌ Model load failed:", e)
    model = None
    encoders = None
    target_encoder = None

# ============================
# 🏠 ROOT
# ============================
@app.get("/")
def home():
    return {"message": "PharmaGuard backend running 🚀"}

# ============================
# 🔬 CLINICAL ANALYSIS
# ============================
@app.post("/analyze")
async def analyze(
    file: UploadFile = File(None),
    drug: str = Form(...),
    gene: str = Form(None),
    variant: str = Form(None)
):
    try:
        drugs = [d.strip().upper() for d in drug.split(",")]

        detected_gene = "N/A"
        detected_variant = "N/A"

        # 📂 FILE MODE
        if file:
            content = await file.read()

            # (Mock parsing for now)
            detected_gene = "CYP2C9"
            detected_variant = "*3"

        # ✍️ MANUAL MODE
        elif gene and variant:
            detected_gene = gene.upper()
            detected_variant = variant

        else:
            return {"error": "Provide VCF file OR gene+variant"}

        # 🧠 BASIC LOGIC
        risk_label = "Safe"
        confidence = 0.85

        if "WARFARIN" in drugs and detected_gene == "CYP2C9":
            risk_label = "Adjust Dosage"
            confidence = 0.78

        return {
            "risk_assessment": {
                "risk_label": risk_label,
                "confidence_score": confidence
            },
            "pharmacogenomic_profile": {
                "primary_gene": detected_gene,
                "phenotype": "Intermediate Metabolizer",
                "diplotype": f"{detected_variant}/{detected_variant}",
                "variants": [detected_variant],
                "metabolism_status": "Reduced"
            },
            "clinical_recommendation": {
                "guideline": "CPIC Guideline available",
                "action": "Reduce dosage and monitor"
            },
            "llm_generated_explanation": {
                "summary": "Genetic variation affects drug metabolism.",
                "mechanism": "Enzyme activity reduced due to variant.",
                "clinical_impact": "Higher drug levels may increase toxicity risk.",
                "recommendation": "Adjust dose and monitor closely."
            }
        }

    except Exception as e:
        print("❌ ERROR in /analyze:", e)
        return {"error": str(e)}

# ============================
# ⚡ QUICK RISK (ML)
# ============================
class RiskRequest(BaseModel):
    age: int
    gender: str
    ethnicity: str
    condition: str
    drug: str
    past_reaction: str

@app.post("/predict")
def predict(data: RiskRequest):
    try:
        if model is None or encoders is None or target_encoder is None:
            return {"error": "ML model not loaded"}

        input_data = data.dict()

        # 🔧 NORMALIZE
        input_data["gender"] = input_data["gender"].upper()
        input_data["ethnicity"] = input_data["ethnicity"].capitalize()
        input_data["condition"] = input_data["condition"].lower()
        input_data["drug"] = input_data["drug"].lower()
        input_data["past_reaction"] = input_data["past_reaction"].lower()

        # 🛡️ SAFE ENCODING
        for col in ['gender', 'ethnicity', 'condition', 'drug', 'past_reaction']:
            if input_data[col] not in encoders[col].classes_:
                input_data[col] = encoders[col].classes_[0]

        df = pd.DataFrame([input_data])

        for col in ['gender', 'ethnicity', 'condition', 'drug', 'past_reaction']:
            df[col] = encoders[col].transform(df[col])

        # 🤖 PREDICT
        pred = model.predict(df)
        proba = model.predict_proba(df)

        risk = target_encoder.inverse_transform(pred)[0].lower()
        confidence = float(max(proba[0]))

        # 🎯 CONFIDENCE LABEL
        if confidence < 0.4:
            confidence_label = "Low confidence"
        elif confidence < 0.7:
            confidence_label = "Moderate confidence"
        else:
            confidence_label = "High confidence"

        return {
            "risk": risk,
            "confidence": round(confidence, 2),
            "confidence_label": confidence_label,

            "risk_summary": f"The model predicts a {risk} risk level for this drug.",
            
            "key_factors": [
                f"Age: {input_data['age']}",
                f"Condition: {input_data['condition']}",
                f"Drug: {input_data['drug']}",
                f"Past reaction: {input_data['past_reaction']}"
            ],

            "what_it_means": (
                "This risk level indicates likelihood of adverse effects "
                "or reduced drug effectiveness."
            ),

            "next_steps": (
                "Consult a healthcare professional before taking this medication."
            )
        }

    except Exception as e:
        print("❌ ERROR in /predict:", e)
        return {"error": str(e)}

# ============================
# 🧠 AI INTELLIGENCE
# ============================
@app.post("/ai-insights")
def ai_insights(data: dict):
    try:
        drug = data.get("drug", "Unknown")
        gene = data.get("gene", "Unknown")
        variant = data.get("variant", "Unknown")

        if not client:
            return {
                "risk_summary": "AI not configured",
                "key_factors": [],
                "what_it_means": "",
                "next_steps": "Set GROQ_API_KEY"
            }

        prompt = f"""
You are a pharmacogenomics expert.

Drug: {drug}
Gene: {gene}
Variant: {variant}

Explain clearly.

Return ONLY JSON:

{{
  "risk_summary": "...",
  "key_factors": ["...", "..."],
  "what_it_means": "...",
  "next_steps": "..."
}}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )

        content = response.choices[0].message.content

        try:
            return json.loads(content)
        except:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                return json.loads(match.group())
            else:
                return {
                    "risk_summary": content,
                    "key_factors": [],
                    "what_it_means": "",
                    "next_steps": "Consult a clinician"
                }

    except Exception as e:
        print("❌ ERROR in /ai-insights:", e)
        return {"error": str(e)}