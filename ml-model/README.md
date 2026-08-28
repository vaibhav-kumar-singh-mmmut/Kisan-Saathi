# ML Model — Phase 0 Stub

This directory will contain the inference service for crop-disease classification.

## Phase 5 Plan
- Fine-tune **MobileNetV3 / EfficientNet-B0** on PlantVillage + IP102 + PlantDoc
- ONNX export for lightweight hosting (Render free tier / Railway)
- Endpoint: `POST /predict` → `{disease_id, confidence, crop, pathogen_type}`
- Confidence < 0.70 → `needs_expert_review: true`, no advisory generated

## Running the stub (Phase 0)
```bash
pip install -r requirements.txt
uvicorn ml_service:app --port 8001 --reload
```

## Directory structure (final)
```
ml-model/
├── ml_service.py          # FastAPI inference server
├── train.py               # Training script
├── evaluate.py            # Evaluation & confusion matrix
├── models/                # Saved weights (.onnx / .pt)
├── data/                  # Dataset symlinks / download scripts
└── requirements.txt
```
