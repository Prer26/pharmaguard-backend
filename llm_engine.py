from groq import Groq
import os
from dotenv import load_dotenv
import json
import re
import logging
import hashlib
from functools import lru_cache

# -----------------------------
# LOAD ENV
# -----------------------------
load_dotenv()

logger = logging.getLogger(__name__)

# -----------------------------
# API SETUP
# -----------------------------
api_key = os.getenv("GROQ_API_KEY")

print("🔑 GROQ API KEY LOADED:", bool(api_key))

if not api_key:
    raise ValueError("❌ Missing GROQ_API_KEY")

client = Groq(api_key=api_key)


# -----------------------------
# JSON EXTRACTION
# -----------------------------
def _extract_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            logger.debug("JSON parse failed")

    return None


# -----------------------------
# HASH (FOR CACHE)
# -----------------------------
def _hash_input(data: dict):
    return hashlib.md5(
        json.dumps(data, sort_keys=True).encode()
    ).hexdigest()


# -----------------------------
# LLM CALL (ROBUST)
# -----------------------------
@lru_cache(maxsize=200)
def _call_llm_cached(data_hash: str, prompt: str):
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # ✅ stable model
            messages=[
                {"role": "system", "content": "You are a clinical pharmacogenomics expert."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=400,
        )

        print("\n🔍 FULL GROQ RESPONSE:\n", response)

        # -----------------------------
        # SAFE EXTRACTION
        # -----------------------------
        if not response:
            raise Exception("No response from Groq")

        if not hasattr(response, "choices") or not response.choices:
            raise Exception("No choices returned")

        message = response.choices[0].message

        if not message:
            raise Exception("No message in response")

        if not hasattr(message, "content") or not message.content:
            raise Exception("Empty content")

        text = message.content.strip()

        print("\n🔥 CLEAN TEXT:\n", text)

        return text

    except Exception as e:
        print("\n❌ GROQ ERROR:", e)
        logger.error(f"LLM CALL FAILED: {e}")
        return None


# -----------------------------
# MAIN FUNCTION
# -----------------------------
def generate_explanation(data, mode="clinical"):
    """
    mode = "clinical" OR "patient"
    """

    gene = data.get("gene")
    phenotype = data.get("phenotype")
    drug = data.get("drug")
    risk = data.get("risk")
    recommendation = data.get("recommendation")
    confidence = data.get("confidence", 0.9)
    variants = data.get("variants", [])

    # -----------------------------
    # PHENOTYPE MEANING
    # -----------------------------
    phenotype_map = {
        "PM": "Very low enzyme activity",
        "IM": "Reduced enzyme activity",
        "NM": "Normal enzyme activity",
        "UM": "Increased enzyme activity"
    }

    phenotype_meaning = phenotype_map.get(phenotype, phenotype)

    # -----------------------------
    # MODE
    # -----------------------------
    if mode == "patient":
        tone = "Explain in simple, non-medical language."
    else:
        tone = "Use precise clinical explanation."

    # -----------------------------
    # PROMPT
    # -----------------------------
    prompt = f"""
You are a clinical pharmacogenomics expert system.

Patient Genetic Data:
- Gene: {gene}
- Phenotype: {phenotype} ({phenotype_meaning})
- Drug: {drug}
- Risk Level: {risk}
- Confidence Score: {confidence}
- Detected Variants: {variants}
- Existing Recommendation: {recommendation}

Explain clearly:
1. Why gene affects drug
2. Biological mechanism
3. Clinical impact
4. Final recommendation

Rules:
- {tone}
- No hallucination
- Be concise
- RETURN STRICT JSON ONLY

Format:
{{
  "summary": "",
  "mechanism": "",
  "clinical_impact": "",
  "recommendation": "",
  "confidence_explanation": ""
}}
"""

    try:
        data_hash = _hash_input(data)
        raw_text = _call_llm_cached(data_hash, prompt)

        if not raw_text:
            raise Exception("Empty LLM response")

        parsed = _extract_json(raw_text)

        if isinstance(parsed, dict):
            return {
                "summary": parsed.get("summary", ""),
                "mechanism": parsed.get("mechanism", ""),
                "clinical_impact": parsed.get("clinical_impact", ""),
                "recommendation": parsed.get("recommendation", recommendation),
                "confidence_explanation": parsed.get(
                    "confidence_explanation",
                    f"Confidence based on detected variants affecting {gene}"
                )
            }

        # fallback if JSON fails
        return {
            "summary": raw_text,
            "mechanism": "",
            "clinical_impact": "",
            "recommendation": recommendation,
            "confidence_explanation": "Generated from AI model"
        }

    except Exception as e:
        print("\n❌ LLM ERROR:", e)
        logger.error(f"LLM ERROR: {e}")

        return {
            "summary": "AI explanation unavailable",
            "mechanism": "",
            "clinical_impact": "",
            "recommendation": recommendation,
            "confidence_explanation": "Fallback response"
        }