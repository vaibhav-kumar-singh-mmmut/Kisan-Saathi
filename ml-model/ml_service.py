"""
ML Model Service — Phase 0 stub

MVP Module: M1 — AI Crop Doctor (PRODUCTION_WORKFLOW.md § MVP Module Map)
Corresponding build phases: Phase 5 (ML inference) + Phase 4 (image capture/geotag)

Exposes a /predict endpoint that returns a mock response.
Replace the stub body with a real model in Phase 5.

Run with: uvicorn ml_service:app --port 8001 --reload
"""
import os
import base64
import httpx
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import sys

# Get config
sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))
try:
    from app.core.config import settings
    CROP_HEALTH_API_KEY = settings.CROP_HEALTH_API_KEY
except ImportError:
    CROP_HEALTH_API_KEY = os.getenv("CROP_HEALTH_API_KEY", "")

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
                
                # Extract top disease suggestion
                disease_suggestions = disease_info.get("suggestions", [])
                top_disease = disease_suggestions[0] if disease_suggestions else {"name": "Healthy", "probability": 0.99, "id": "healthy"}
                
                # Extract top crop suggestion
                crop_suggestions = crop_info.get("suggestions", [])
                top_crop = crop_suggestions[0] if crop_suggestions else {"name": "Unknown Crop"}
                
                confidence = float(top_disease.get("probability", 0.0))
                needs_review = confidence < 0.70
                
                return PredictionResponse(
                    disease_id=top_disease.get("id", top_disease.get("name")),
                    disease_name=top_disease.get("name"),
                    confidence=confidence,
                    crop=top_crop.get("name"),
                    pathogen_type="unknown", # Kindwise provides details, could be extracted here
                    needs_expert_review=needs_review
                )
            else:
                print(f"Kindwise API Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Inference error calling Kindwise API: {e}")
            # Fall through to mock

    # Mock Response / Fallback (No model available)
    return PredictionResponse(
        disease_id="unknown",
        disease_name="Unknown (Model Unavailable)",
        confidence=0.0,
        crop="Unknown",
        pathogen_type="unknown",
        needs_expert_review=True
    )
