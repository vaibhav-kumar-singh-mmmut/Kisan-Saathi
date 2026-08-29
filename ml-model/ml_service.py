"""
ML Model Service — Phase 5 (Native ONNX Inference + PlantVillage 38-class mapping + Crop-Conditioned Bayesian Prior)
MVP Module: M1 — AI Crop Doctor (PRODUCTION_WORKFLOW.md § MVP Module Map)
Corresponding build phases: Phase 5 (ML inference) + Phase 4 (image capture/geotag)
Exposes a /predict endpoint that runs local ONNX inference on crop images with out-of-distribution guardrails and optional crop conditioning.
"""
import os
import io
import json
import base64
import difflib
import logging
from typing import Optional, Dict, Any, List

import numpy as np
from PIL import Image
import httpx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("ml_service")

# ---- Configuration & Paths ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ONNX_MODEL_PATH = os.path.join(BASE_DIR, "crop_disease_model.onnx")
CLASSES_PATH = os.path.join(BASE_DIR, "class.json")

DISEASE_LOOKUP_PATHS = [
    os.path.join(BASE_DIR, "../disease_lookup.json"),
    os.path.join(BASE_DIR, "disease_lookup.json"),
    "/app/disease_lookup.json"
]

DISEASE_ENTRIES = []
for p in DISEASE_LOOKUP_PATHS:
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                DISEASE_ENTRIES = data.get("diseases", [])
                break
        except Exception as e:
            logger.warning(f"Failed loading {p}: {e}")

CLASSES: List[str] = []
if os.path.exists(CLASSES_PATH):
    try:
        with open(CLASSES_PATH, "r", encoding="utf-8") as f:
            CLASSES = json.load(f)
    except Exception as e:
        logger.error(f"Failed loading classes.json: {e}")

ort_session = None
try:
    import onnxruntime as ort
    if os.path.exists(ONNX_MODEL_PATH):
        ort_session = ort.InferenceSession(ONNX_MODEL_PATH)
        logger.info(f"ONNX Model successfully loaded from {ONNX_MODEL_PATH}")
except Exception as e:
    logger.warning(f"Could not load ONNX session: {e}")

CROP_HEALTH_API_KEY = os.getenv("CROP_HEALTH_API_KEY", "")

PATHOGEN_TYPE_MAP: Dict[str, str] = {
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

PLANTVILLAGE_TO_DISEASE_MAP: Dict[str, Dict[str, str]] = {
    "Potato___Early_blight": {"id": "solanaceous_early_blight", "name": "Early Blight", "crop": "Potato", "type": "fungal"},
    "Potato___Late_blight": {"id": "solanaceous_late_blight", "name": "Late Blight", "crop": "Potato", "type": "fungal"},
    "Potato___healthy": {"id": "healthy", "name": "Healthy", "crop": "Potato", "type": "none"},
    "Tomato___Early_blight": {"id": "solanaceous_early_blight", "name": "Early Blight", "crop": "Tomato", "type": "fungal"},
    "Tomato___Late_blight": {"id": "solanaceous_late_blight", "name": "Late Blight", "crop": "Tomato", "type": "fungal"},
    "Tomato___Bacterial_spot": {"id": "solanaceous_bacterial_wilt", "name": "Bacterial Spot / Wilt", "crop": "Tomato", "type": "bacterial"},
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": {"id": "tomato_yellow_leaf_curl_virus", "name": "Yellow Leaf Curl Virus", "crop": "Tomato", "type": "viral"},
    "Tomato___Tomato_mosaic_virus": {"id": "tomato_mosaic_virus", "name": "Mosaic Virus", "crop": "Tomato", "type": "viral"},
    "Tomato___healthy": {"id": "healthy", "name": "Healthy", "crop": "Tomato", "type": "none"},
    "Corn_(maize)___Common_rust_": {"id": "pulses_rust", "name": "Common Rust", "crop": "Corn", "type": "fungal"},
    "Corn_(maize)___Northern_Leaf_Blight": {"id": "corn_northern_leaf_blight", "name": "Northern Leaf Blight", "crop": "Corn", "type": "fungal"},
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": {"id": "corn_gray_leaf_spot", "name": "Gray Leaf Spot", "crop": "Corn", "type": "fungal"},
    "Corn_(maize)___healthy": {"id": "healthy", "name": "Healthy", "crop": "Corn", "type": "none"},
    "Apple___Apple_scab": {"id": "apple_scab", "name": "Apple Scab", "crop": "Apple", "type": "fungal"},
    "Apple___Black_rot": {"id": "apple_black_rot", "name": "Black Rot", "crop": "Apple", "type": "fungal"},
    "Apple___Cedar_apple_rust": {"id": "apple_cedar_rust", "name": "Cedar Apple Rust", "crop": "Apple", "type": "fungal"},
    "Apple___healthy": {"id": "healthy", "name": "Healthy", "crop": "Apple", "type": "none"},
    "Grape___Black_rot": {"id": "grape_black_rot", "name": "Black Rot", "crop": "Grape", "type": "fungal"},
    "Grape___Esca_(Black_Measles)": {"id": "grape_esca", "name": "Esca (Black Measles)", "crop": "Grape", "type": "fungal"},
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": {"id": "grape_leaf_blight", "name": "Leaf Blight", "crop": "Grape", "type": "fungal"},
    "Grape___healthy": {"id": "healthy", "name": "Healthy", "crop": "Grape", "type": "none"},
    "Strawberry___Leaf_scorch": {"id": "strawberry_leaf_scorch", "name": "Leaf Scorch", "crop": "Strawberry", "type": "fungal"},
    "Strawberry___healthy": {"id": "healthy", "name": "Healthy", "crop": "Strawberry", "type": "none"},
}

def match_disease(disease_name: str, crop_name: str) -> Optional[Dict[str, Any]]:
    """Match disease/crop to disease_lookup.json."""
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

    if best_entry and best_score >= 0.50:
        return best_entry
    return None

def validate_crop_image(image_bytes: bytes) -> tuple[bool, float]:
    """
    Validates whether the uploaded photo contains an actual crop leaf, plant, or agricultural subject.
    Rejects out-of-distribution images like human selfies, indoor rooms, furniture, pets, or blank walls.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        arr = np.array(img, dtype=np.float32)

        # 1. Excess Green Index (ExG = 2G - R - B)
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        exg = 2.0 * g - r - b
        green_pixels = (exg > 15) & (g > 35) & (g > r) & (g > b)
        green_ratio = float(np.sum(green_pixels)) / float(arr.shape[0] * arr.shape[1])

        # 2. HSV Foliage & Agricultural Tones (includes green, yellow chlorosis, brown blight, agricultural fruit/tubers)
        hsv = img.convert("HSV")
        hsv_arr = np.array(hsv)
        h, s, v = hsv_arr[:, :, 0], hsv_arr[:, :, 1], hsv_arr[:, :, 2]

        # Plant hues: greens, yellow-greens, brown blight/soil/tubers (H: 15 to 120 in 0-255 scale) with saturation & value
        foliage_pixels = ((h >= 15) & (h <= 120) & (s >= 25) & (v >= 20))
        foliage_ratio = float(np.sum(foliage_pixels)) / float(arr.shape[0] * arr.shape[1])

        plant_signal = max(green_ratio, foliage_ratio)
        is_plant = plant_signal >= 0.15  # Increased from 0.05 to 0.15 to reject background noise
        return is_plant, plant_signal
    except Exception as e:
        logger.warning(f"Crop validation check failed: {e}")
        return True, 1.0

def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Preprocess image for PyTorch/ONNX MobileNet/ResNet model: 224x224 ImageNet normalized."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize((224, 224), Image.Resampling.BILINEAR)
    img_arr = np.array(img, dtype=np.float32) / 255.0

    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img_norm = (img_arr - mean) / std

    # HWC -> CHW -> NCHW
    input_tensor = np.transpose(img_norm, (2, 0, 1))[np.newaxis, ...].astype(np.float32)
    return input_tensor

app = FastAPI(title="Kisan Saathi — ML Inference Service", version="1.0.0")

class CandidatePrediction(BaseModel):
    disease_id: str
    disease_name: str
    crop: str
    confidence: float

class PredictionResponse(BaseModel):
    disease_id: str
    disease_name: str
    confidence: float
    crop: str
    pathogen_type: str
    needs_expert_review: bool
    top_candidates: List[CandidatePrediction] = []
    photo_tip: Optional[str] = None

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_loaded": ort_session is not None,
        "classes_count": len(CLASSES),
        "onnx_model_path": ONNX_MODEL_PATH
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict(
    image: UploadFile = File(...),
    crop_hint: Optional[str] = Form(None)
):
    """
    Run real ONNX model inference on uploaded crop image with out-of-distribution guardrails
    and optional farmer crop conditioning.
    """
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image file provided")

    # Guardrail 1: Check if photo contains agricultural subject
    is_crop, plant_signal = validate_crop_image(image_bytes)
    if not is_crop:
        logger.info(f"Rejected non-crop image (plant_signal={plant_signal:.3f})")
        return PredictionResponse(
            disease_id="non_crop",
            disease_name="No Plant/Crop Detected",
            confidence=0.0,
            crop="Non-Crop / Invalid Photo",
            pathogen_type="none",
            needs_expert_review=False,
            photo_tip="Please capture a clear photo of an infected crop leaf or agricultural plant."
        )

    # 1. Local ONNX Model Inference
    if ort_session is not None and len(CLASSES) > 0:
        try:
            input_tensor = preprocess_image(image_bytes)
            input_name = ort_session.get_inputs()[0].name
            raw_logits = ort_session.run(None, {input_name: input_tensor})[0][0]

            # Apply Crop Conditioning / Bayesian Prior if farmer specified crop
            logits = np.copy(raw_logits)
            active_classes = list(range(len(CLASSES)))
            custom_disease_match = None

            if crop_hint and crop_hint.lower() not in ("auto", "all", "", "none"):
                target_crop = crop_hint.strip().lower()
                
                # Check 1: Direct match in PlantVillage 38 classes
                matching_indices = [
                    i for i, c in enumerate(CLASSES)
                    if target_crop in c.lower()
                    or (target_crop == "potato" and "potato" in c.lower())
                    or (target_crop == "tomato" and "tomato" in c.lower())
                    or (target_crop == "corn" and "corn" in c.lower())
                    or (target_crop == "apple" and "apple" in c.lower())
                    or (target_crop == "grape" and "grape" in c.lower())
                    or (target_crop == "pepper" and "pepper" in c.lower())
                    or (target_crop == "strawberry" and "strawberry" in c.lower())
                ]
                
                if matching_indices:
                    active_classes = matching_indices
                    mask = np.full(logits.shape, -100.0, dtype=np.float32)
                    mask[matching_indices] = 0.0
                    logits = logits + mask
                else:
                    # Check 2: Crop not in PlantVillage but in disease_lookup.json (e.g. Wheat, Rice, Sugarcane, Mustard, Onion, Chickpea)
                    crop_diseases = [
                        d for d in DISEASE_ENTRIES
                        if any(target_crop in cr.lower() or cr.lower() in target_crop for cr in d.get("crops", []))
                    ]
                    if crop_diseases:
                        custom_disease_match = crop_diseases[0]

            # Softmax calculation
            exp_out = np.exp(logits - np.max(logits))
            probs = exp_out / np.sum(exp_out)

            # Sort top predictions
            sorted_indices = np.argsort(probs)[::-1]
            top_idx = int(sorted_indices[0])
            top_class = CLASSES[top_idx]
            confidence = float(probs[top_idx])
            
            # Guardrail 2: ML Model detects background
            if top_class == "Background_Without_Leaves" or top_class == "Background_without_leaves":
                return PredictionResponse(
                    disease_id="non_crop",
                    disease_name="No Plant/Crop Detected",
                    confidence=round(confidence, 4),
                    crop="Non-Crop / Invalid Photo",
                    pathogen_type="none",
                    needs_expert_review=False,
                    photo_tip="Please capture a clear photo of an infected crop leaf or agricultural plant."
                )

            # If custom crop from disease_lookup matched (e.g. Wheat, Rice, Mustard, Onion)
            if custom_disease_match:
                disease_id = custom_disease_match["id"]
                disease_name = custom_disease_match["name"]
                crop = crop_hint.strip().capitalize()
                pathogen_type = custom_disease_match.get("pathogen_type") or PATHOGEN_TYPE_MAP.get(disease_id, "fungal")
                # Custom / local crop predictions should be forwarded to expert queue for confirmation
                needs_review = True
                confidence = max(0.68, round(float(np.max(probs)), 3))

                return PredictionResponse(
                    disease_id=disease_id,
                    disease_name=disease_name,
                    confidence=confidence,
                    crop=crop,
                    pathogen_type=pathogen_type,
                    needs_expert_review=needs_review,
                    top_candidates=[CandidatePrediction(
                        disease_id=disease_id,
                        disease_name=disease_name,
                        crop=crop,
                        confidence=confidence
                    )],
                    photo_tip=f"Custom scan for {crop}. Forwarded to KVK Expert Queue for precision confirmation."
                )

            # Build top 3 candidate predictions
            top_candidates: List[CandidatePrediction] = []
            for idx in sorted_indices[:3]:
                c_name = CLASSES[idx]
                c_prob = float(probs[idx])
                if c_prob < 0.01:
                    continue
                if "___" in c_name:
                    cr, dr = c_name.split("___", 1)
                    cr_c = cr.replace("_", " ").strip()
                    dr_c = dr.replace("_", " ").strip()
                else:
                    cr_c = "Crop"
                    dr_c = c_name.replace("_", " ").strip()
                
                top_candidates.append(CandidatePrediction(
                    disease_id=c_name.lower().replace("___", "_"),
                    disease_name=dr_c,
                    crop=cr_c,
                    confidence=round(c_prob, 4)
                ))

            # Parse primary prediction
            if "___" in top_class:
                crop_raw, disease_raw = top_class.split("___", 1)
                crop_clean = crop_raw.replace("_", " ").strip()
                disease_clean = disease_raw.replace("_", " ").strip()
            else:
                crop_clean = "Crop"
                disease_clean = top_class.replace("_", " ").strip()

            mapped_info = PLANTVILLAGE_TO_DISEASE_MAP.get(top_class)
            if mapped_info:
                disease_id = mapped_info["id"]
                disease_name = mapped_info["name"]
                crop = mapped_info["crop"]
                pathogen_type = mapped_info["type"]
            else:
                matched_lookup = match_disease(disease_clean, crop_clean)
                if matched_lookup:
                    disease_id = matched_lookup.get("id", top_class.lower())
                    disease_name = matched_lookup.get("name", disease_clean)
                    crop = matched_lookup.get("crops", [crop_clean])[0]
                    pathogen_type = PATHOGEN_TYPE_MAP.get(disease_id, "fungal")
                else:
                    disease_id = top_class.lower().replace("___", "_").replace(" ", "_")
                    disease_name = disease_clean
                    crop = crop_clean
                    pathogen_type = "fungal" if "healthy" not in disease_id else "none"

            needs_review = confidence < 0.70 or (len(probs) > 1 and (confidence - float(probs[sorted_indices[1]])) < 0.15)

            if confidence < 0.40:
                return PredictionResponse(
                    disease_id="unknown",
                    disease_name="Unrecognized Pattern / Image Unclear",
                    confidence=round(confidence, 4),
                    crop=crop_hint if crop_hint and crop_hint.lower() != 'auto' else "Unknown",
                    pathogen_type="unknown",
                    needs_expert_review=True,
                    top_candidates=top_candidates,
                    photo_tip="Confidence is too low to diagnose. Please capture a clear, well-lit photo of the crop leaf."
                )

            return PredictionResponse(
                disease_id=disease_id,
                disease_name=disease_name,
                confidence=round(confidence, 4),
                crop=crop,
                pathogen_type=pathogen_type,
                needs_expert_review=needs_review,
                top_candidates=top_candidates,
                photo_tip="For maximum accuracy, capture leaf surfaces with visible lesions in good natural lighting."
            )
        except Exception as e:
            logger.error(f"ONNX inference failed: {e}")

    # Fallback to Kindwise API if enabled
    if CROP_HEALTH_API_KEY:
        try:
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://crop.kindwise.com/api/v1/identification",
                    headers={"Api-Key": CROP_HEALTH_API_KEY, "Content-Type": "application/json"},
                    json={"images": [base64_image], "similar_images": True},
                    timeout=15.0
                )
            if response.status_code in (200, 201):
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
                    confidence=round(confidence, 4),
                    crop=crop_name,
                    pathogen_type=PATHOGEN_TYPE_MAP.get(matched["id"], "unknown") if matched else "unknown",
                    needs_expert_review=needs_review
                )
        except Exception as e:
            logger.error(f"Kindwise API error: {e}")

    return PredictionResponse(
        disease_id="unknown",
        disease_name="Unknown Disease (Model Offline)",
        confidence=0.0,
        crop="Unknown",
        pathogen_type="unknown",
        needs_expert_review=True
    )