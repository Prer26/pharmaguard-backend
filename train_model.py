import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

# =====================================
# 🎯 YOUR FINAL DRUG LIST (FIXED)
# =====================================
drugs = [
    "warfarin",
    "clopidogrel",
    "codeine",
    "omeprazole",
    "tamoxifen",
    "phenytoin",
    "simvastatin",
    "abacavir",
    "carbamazepine",
    "allopurinol"
]

conditions = ["cardiac", "infection", "neurology"]
genders = ["M", "F"]
ethnicities = ["Caucasian", "African", "Asian"]
past_reactions = ["yes", "no"]

np.random.seed(42)

# =====================================
# 📊 DATA GENERATION
# =====================================
def generate_data(n=4000):
    data = []

    for _ in range(n):
        age = np.random.randint(18, 85)
        gender = np.random.choice(genders)
        ethnicity = np.random.choice(ethnicities)
        condition = np.random.choice(conditions)
        drug = np.random.choice(drugs)
        past_reaction = np.random.choice(past_reactions)

        # -------------------------
        # 🧠 RISK LOGIC (CLINICAL STYLE)
        # -------------------------
        risk_score = 0.2

        if age > 60:
            risk_score += 0.2

        # High-risk drugs
        if drug in ["warfarin", "carbamazepine", "phenytoin"]:
            risk_score += 0.25

        # Moderate risk
        if drug in ["simvastatin", "allopurinol"]:
            risk_score += 0.15

        # Genetic sensitive drugs
        if drug in ["abacavir", "carbamazepine"]:
            risk_score += 0.2

        if condition == "cardiac":
            risk_score += 0.15

        if past_reaction == "yes":
            risk_score += 0.3

        # Clamp
        risk_score = max(0, min(1, risk_score))

        if risk_score < 0.33:
            risk = "low"
        elif risk_score < 0.66:
            risk = "moderate"
        else:
            risk = "high"

        data.append({
            "age": age,
            "gender": gender,
            "ethnicity": ethnicity,
            "condition": condition,
            "drug": drug,
            "past_reaction": past_reaction,
            "risk": risk
        })

    return pd.DataFrame(data)


# =====================================
# 🚀 TRAIN MODEL
# =====================================
print("🚀 Generating dataset...")
df = generate_data(4000)

print("📊 Dataset:", df.shape)
print("💊 Drugs:", df["drug"].unique())

# Encode
encoders = {}
for col in ['gender', 'ethnicity', 'condition', 'drug', 'past_reaction']:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col])
    encoders[col] = le

# Target
target_encoder = LabelEncoder()
y = target_encoder.fit_transform(df["risk"])

# Features
X = df[['age', 'gender', 'ethnicity', 'condition', 'drug', 'past_reaction']]

# Model
print("🧠 Training model...")
model = RandomForestClassifier(
    n_estimators=150,
    max_depth=12,
    random_state=42
)
model.fit(X, y)

# Save
os.makedirs("models", exist_ok=True)

joblib.dump(model, "models/pharmaguard_model.pkl")
joblib.dump(encoders, "models/encoders.pkl")
joblib.dump(target_encoder, "models/target_encoder.pkl")

print("✅ DONE — FINAL MVP MODEL READY")
print("Supported drugs:", drugs)