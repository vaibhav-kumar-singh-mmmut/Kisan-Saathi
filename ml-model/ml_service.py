"""
ML Model Service — Phase 5+ (real Kindwise integration + disease_lookup matching)
MVP Module: M1 — AI Crop Doctor (PRODUCTION_WORKFLOW.md § MVP Module Map)
Corresponding build phases: Phase 5 (ML inference) + Phase 4 (image capture/geotag)
Exposes a /predict endpoint that calls crop.health and matches results to disease_lookup.json.
Run with: uvicorn ml_service:app --port 8001 --reload
"""
import os
import json
import base64
import difflib
import httpx
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))
try:
    from app.core.config import settings
    CROP_HEALTH_API_KEY = settings.CROP_HEALTH_API_KEY
except ImportError:
    CROP_HEALTH_API_KEY = os.getenv("CROP_HEALTH_API_KEY", "")

# ---- Load disease_lookup.json once at startup ----
DISEASE_LOOKUP_PATH = os.path.join(os.path.dirname(__file__), "../disease_lookup.json")
with open(DISEASE_LOOKUP_PATH, "r", encoding="utf-8") as f:
    _lookup_data = json.load(f)
DISEASE_ENTRIES = _lookup_data.get("diseases", [])

# Same approved pathogen_type map as backend/app/db/seed_disease_lookup.py
PATHOGEN_TYPE_MAP = {
    "wheat_yellow_rust": "fungal",
    "wheat_brown_leaf_rust": "fungal",
    "wheat_stem_black_rust": "fungal",
    "wheat_pests": "insect",
    "rice_bakanae": "fungal",
    "rice_false_smut": "fungal",
    "rice_blast": "fungal",
    "rice_tungro": "viral",
    "sugarcane_red_rot": "fungal",
    "cotton_whitefly": "insect",
    "cotton_pink_bollworm": "insect",
    "mustard_pests_diseases": "insect",
    "onion_purple_blotch": "fungal",
    "onion_stemphylium_blight": "fungal",
    "onion_thrips": "insect",
    "onion_fusarium_basal_rot": "fungal",
    "solanaceous_early_blight": "fungal",
    "solanaceous_late_blight": "fungal",
    "solanaceous_bacterial_wilt": "bacterial",
    "potato_pink_rot": "fungal",
    "potato_powdery_scab": "fungal",
    "brinjal_fruit_shoot_borer": "insect",
    "nursery_damping_off": "fungal",
    "anthracnose_multi": "fungal",
    "mango_powdery_mildew": "fungal",
    "mango_bacterial_canker": "bacterial",
    "litchi_blight": "fungal",
    "litchi_sudden_death": "fungal",
    "litchi_fruit_shoot_borer": "insect",
    "pomegranate_bacterial_blight": "bacterial",
    "pomegranate_nematode_wilt": "nematode",
    "chickpea_wilt": "fungal",
    "chickpea_ascochyta_blight": "fungal",
    "pulses_rust": "fungal",
    "pulses_powdery_mildew": "fungal",
    "lentil_collar_rot": "fungal",
    "pigeonpea_wilt": "fungal",
    "strawberry_powdery_mildew": "fungal",
}

def match_disease(disease_name: str, crop_name: str):
    """
    Match a crop.health disease_name/crop_name to the closest disease_lookup.json entry.
    Returns the matched entry dict, or None if nothing matches well enough.
    """
    if not disease_name:
        return None
    target = disease_name.strip().lower()
    crop_target = (crop_name or "").strip().lower()

    best_entry = None
    best_score = 0.0

    for entry in DISEASE_ENTRIES:
        entry_name = entry.get("name", "").strip().lower()
        entry_crops = [c.strip().lower() for c in entry.get("crops", [])]

        name_score = difflib.SequenceMatcher(None, target, entry_name).ratio()
        crop_bonus = 0.15 if crop_target and any(crop_target in c or c in crop_target for c in entry_crops) else 0.0
        substring_bonus = 0.1 if (target in entry_name or entry_name in target) else 0.0

        score = name_score + crop_bonus + substring_bonus

        if score > best_score:
            best_score = score
            best_entry = entry

    if best_entry and best_score >= 0.55:
        return best_entry
    return None

app = FastAPI(title="Kisan Saathi — ML Inference Service", version="0.1.0")

class PredictionResponse(BaseModel):
    disease_id: str
    disease_name: str
    confidence: float
    crop: str
    pathogen_type: str
    needs_expert_review: bool

@app.get("/health")
async def health():
    return {"status": "ok", "model": "crop-health-api" if CROP_HEALTH_API_KEY else "mock-v0"}

@app.post("/predict", response_model=PredictionResponse)
async def predict(image: UploadFile = File(...)):
    if CROP_HEALTH_API_KEY:
        try:
            image_data = await image.read()
            base64_image = base64.b64encode(image_data).decode("utf-8")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://crop.kindwise.com/api/v1/identification",
                    headers={
                        "Api-Key": CROP_HEALTH_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json={
                        "images": [base64_image],
                        "similar_images": True
                    },
                    timeout=15.0
                )
            if response.status_code == 201 or response.status_code == 200:
                data = response.json()
                result = data.get("result", {})
                disease_info = result.get("disease", {})
                crop_info = result.get("crop", {})

                disease_suggestions = disease_info.get("suggestions", [])
                top_disease = disease_suggestions[0] if disease_suggestions else {"name": "Healthy", "probability": 0.99, "id": "healthy"}

                crop_suggestions = crop_info.get("suggestions", [])
                top_crop = crop_suggestions[0] if crop_suggestions else {"name": "Unknown Crop"}

                confidence = float(top_disease.get("probability", 0.0))
                disease_name = top_disease.get("name", "")
                crop_name = top_crop.get("name", "")

                matched = match_disease(disease_name, crop_name)
                needs_review = confidence < 0.70 or matched is None

                return PredictionResponse(
                    disease_id=matched.get("id", disease_name) if matched else top_disease.get("id", disease_name),
                    disease_name=disease_name,
                    confidence=confidence,
                    crop=crop_name,
                    pathogen_type=PATHOGEN_TYPE_MAP.get(matched["id"], "unknown") if matched else "unknown",
                    needs_expert_review=needs_review
                )
            else:
                print(f"Kindwise API Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Inference error calling Kindwise API: {e}")

    return PredictionResponse(
        disease_id="unknown",
        disease_name="Unknown (Model Unavailable)",
        confidence=0.0,
        crop="Unknown",
        pathogen_type="unknown",
        needs_expert_review=True
    )