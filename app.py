from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
import os
from groq import Groq
from dotenv import load_dotenv
import json, re

# 🔐 Load env
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = FastAPI()

# 🌐 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📦 Load model
model = joblib.load("models/pharmaguard_model.pkl")
encoders = joblib.load("models/encoders.pkl")
target_encoder = joblib.load("models/target_encoder.pkl")

# =====================================
# 🧾 REQUEST MODEL (FIXES SWAGGER)
# =====================================
class RiskRequest(BaseModel):
    age: int
    gender: str
    ethnicity: str
    condition: str
    drug: str
    past_reaction: str


# =====================================
# 🧠 DRUG MAP (ONLY TRAINED DRUGS)
# =====================================
drug_map = {
    "warfarin": "warfarin",
    "clopidogrel": "clopidogrel",
    "codeine": "codeine",
    "omeprazole": "omeprazole",
    "tamoxifen": "tamoxifen",
    "phenytoin": "phenytoin",
    "simvastatin": "simvastatin",
    "abacavir": "abacavir",
    "carbamazepine": "carbamazepine",
    "allopurinol": "allopurinol"
}


@app.get("/")
def home():
    return {"message": "PharmaGuard AI running 🚀"}


# =====================================
# ⚡ QUICK RISK (ML + GROQ)
# =====================================
@app.post("/predict")
def predict(data: RiskRequest):
    try:
        # Normalize
        input_data = data.dict()
        input_data["drug"] = input_data["drug"].strip().lower()
        input_data["condition"] = input_data["condition"].strip().lower()
        input_data["past_reaction"] = input_data["past_reaction"].strip().lower()

        # Map drug
        input_drug = input_data["drug"]

        if input_drug in drug_map:
            mapped_drug = drug_map[input_drug]
        elif input_drug in encoders["drug"].classes_:
            mapped_drug = input_drug
        else:
            mapped_drug = encoders["drug"].classes_[0]

        input_data["drug"] = mapped_drug

        # Safe condition
        if input_data["condition"] not in encoders["condition"].classes_:
            input_data["condition"] = encoders["condition"].classes_[0]

        df = pd.DataFrame([input_data])

        # Encode
        for col in ['gender', 'ethnicity', 'condition', 'drug', 'past_reaction']:
            df[col] = encoders[col].transform(df[col])

        # Predict
        pred = model.predict(df)
        proba = model.predict_proba(df)

        risk = target_encoder.inverse_transform(pred)[0]
        confidence = float(max(proba[0]))

        if confidence < 0.4:
            confidence_label = "Low confidence"
        elif confidence < 0.7:
            confidence_label = "Moderate confidence"
        else:
            confidence_label = "High confidence"

        # =====================================
        # 🧠 GROQ EXPLANATION
        # =====================================
        prompt = f"""
You are a clinical AI assistant.

Patient:
- Age: {input_data['age']}
- Condition: {input_data['condition']}
- Drug: {input_drug}
- Past reaction: {input_data['past_reaction']}

Prediction:
- Risk: {risk}
- Confidence: {round(confidence,2)}

Explain clearly for patient.

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
            ai_data = json.loads(content)
        except:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                ai_data = json.loads(match.group())
            else:
                ai_data = {
                    "risk_summary": content,
                    "key_factors": [],
                    "what_it_means": "",
                    "next_steps": "Consult a doctor."
                }

        return {
            "risk": risk,
            "confidence": round(confidence, 2),
            "confidence_label": confidence_label,
            "risk_summary": ai_data.get("risk_summary", ""),
            "key_factors": ai_data.get("key_factors", []),
            "what_it_means": ai_data.get("what_it_means", ""),
            "next_steps": ai_data.get("next_steps", ""),
            "mapped_drug": mapped_drug
        }

    except Exception as e:
        return {"error": str(e)}


# =====================================
# 🧠 AI INSIGHTS (FIXED)
# =====================================
@app.post("/ai-insights")
def ai_insights(data: dict):
    try:
        prompt = f"""
You are a friendly medical assistant.

Patient:
- Age: {data.get('age')}
- Condition: {data.get('condition')}
- Medicine: {data.get('drug')}
- Past reaction: {data.get('past_reaction')}

Explain clearly.

Return JSON:

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
            temperature=0.5,
        )

        content = response.choices[0].message.content

        try:
            return json.loads(content)
        except:
            return {"risk_summary": content}

    except Exception as e:
        return {"error": str(e)}