"""
ML Model Service — Phase 0 stub

MVP Module: M1 — AI Crop Doctor (PRODUCTION_WORKFLOW.md § MVP Module Map)
Corresponding build phases: Phase 5 (ML inference) + Phase 4 (image capture/geotag)

Exposes a /predict endpoint that returns a mock response.
Replace the stub body with a real model in Phase 5.

Run with: uvicorn ml_service:app --port 8001 --reload
"""
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

app = FastAPI(title="Kisan Saathi — ML Inference Service", version="0.1.0")


class PredictionResponse(BaseModel):
    disease_id: str
    disease_name: str
    confidence: float  # 0.0–1.0
    crop: str
    pathogen_type: str  # fungal | bacterial | viral | nematode | unknown
    needs_expert_review: bool


@app.get("/health")
async def health():
    return {"status": "ok", "model": "stub-v0"}


@app.post("/predict", response_model=PredictionResponse)
async def predict(image: UploadFile = File(...)):
    """
    Phase 0 stub — returns a fixed mock response.
    Phase 5 will load MobileNet/EfficientNet weights here.
    """
    # TODO Phase 5: load model, run inference, return real prediction
    return PredictionResponse(
        disease_id="mock_001",
        disease_name="Wheat Leaf Rust (stub)",
        confidence=0.85,
        crop="wheat",
        pathogen_type="fungal",
        needs_expert_review=False,
    )
