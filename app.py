from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
# 🧠 DRUG INTELLIGENCE (PATIENT → MODEL)
# =====================================
drug_map = {
    # model-known drugs
    "warfarin": "warfarin",
    "clopidogrel": "clopidogrel",
    "aspirin": "aspirin",
    "omeprazole": "omeprazole",

    # 🔥 common patient drugs
    "dolo": "paracetamol",
    "crocin": "paracetamol",
    "calpol": "paracetamol",
    "paracetamol": "paracetamol",

    "vicks": "menthol",
    "benadryl": "diphenhydramine",

    "pantoprazole": "omeprazole",
    "pan": "omeprazole"
}


@app.get("/")
def home():
    return {"message": "PharmaGuard AI running 🚀"}


# =====================================
# ⚡ QUICK RISK (ML + GROQ HYBRID)
# =====================================
@app.post("/predict")
def predict(data: dict):
    try:
        # 🔥 Normalize inputs
        data["drug"] = data.get("drug", "").strip().lower()
        data["condition"] = data.get("condition", "").strip().lower()
        data["past_reaction"] = data.get("past_reaction", "").strip().lower()
        data["gender"] = data.get("gender", "").strip()
        data["ethnicity"] = data.get("ethnicity", "").strip()

        # 🔥 Map patient drug → model drug
        input_drug = data["drug"]

        if input_drug in drug_map:
            mapped_drug = drug_map[input_drug]
        elif input_drug in encoders["drug"].classes_:
            mapped_drug = input_drug
        else:
            mapped_drug = encoders["drug"].classes_[0]  # safe fallback

        data["drug"] = mapped_drug

        # 🔥 Safe condition handling
        if data["condition"] not in encoders["condition"].classes_:
            data["condition"] = encoders["condition"].classes_[0]

        df = pd.DataFrame([data])

        # Encode
        for col in ['gender', 'ethnicity', 'condition', 'drug', 'past_reaction']:
            df[col] = encoders[col].transform(df[col])

        # Prediction
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
        # 🧠 GROQ EXPLANATION (NO HARDCODING)
        # =====================================
        prompt = f"""
You are a clinical AI assistant.

Patient:
- Age: {data['age']}
- Condition: {data['condition']}
- Drug taken: {input_drug} (mapped to {mapped_drug})
- Past reaction: {data['past_reaction']}

Model prediction:
- Risk level: {risk}
- Confidence: {round(confidence,2)}

Explain clearly for a patient:
1. Why this risk occurred
2. Key contributing factors
3. What the patient should do

Return ONLY JSON (no extra text, no markdown):

{{
  "risk_summary": "1–2 line simple explanation",
  "key_factors": ["reason1", "reason2"],
  "what_it_means": "what this means for the patient",
  "next_steps": "clear advice"
}}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )

        content = response.choices[0].message.content
        print("🔥 GROQ RESPONSE:", content)

        # Parse JSON safely
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
        print("ERROR:", str(e))
        return {"error": str(e)}


# =====================================
# 🧠 AI INTELLIGENCE (FULL GROQ MODE)
# =====================================
@app.post("/ai-insights")
def ai_insights(data: dict):
    try:
        drug = data.get("drug", "unknown")
        condition = data.get("condition", "unknown")
        age = data.get("age", "unknown")

        prompt = f"""
You are a friendly medical assistant explaining results to a patient.

Patient:
- Age: {data['age']}
- Condition: {data['condition']}
- Medicine: {input_drug} (interpreted as {mapped_drug})
- Past reaction: {data['past_reaction']}

Prediction:
- Risk: {risk}
- Confidence: {round(confidence,2)}

Explain in simple, reassuring language.

Return JSON:
{{
  "risk_summary": "...",
  "key_factors": ["...", "..."],
  "what_it_means": "...",
  "next_steps": "..."
}}
"""
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )

        content = response.choices[0].message.content

        try:
            parsed = json.loads(content)
        except:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
            else:
                parsed = {
                    "summary": content,
                    "mechanism": "",
                    "clinical_impact": "",
                    "recommendation": ""
                }

        return parsed

    except Exception as e:
        print("AI ERROR:", str(e))
        return {"error": str(e)}
    
    