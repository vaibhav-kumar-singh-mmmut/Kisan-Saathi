from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.disease_lookup import DiseaseLookup
from app.schemas.advisory import AdvisoryResponse

router = APIRouter()


@router.get("", response_model=AdvisoryResponse)
def get_advisory(disease_id: str, confidence: float, db: Session = Depends(get_db)):
    """
    Get Pathogen-Branched Advisory for a disease prediction.
    """
    if confidence < 0.70:
        return AdvisoryResponse(
            status="expert_queue",
            message="Low confidence prediction. Routes to expert queue, no advisory generated yet.",
        )

    disease = db.execute(
        select(DiseaseLookup).where(DiseaseLookup.id == disease_id)
    ).scalar_one_or_none()

    if not disease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Disease not found."
        )

    base_response = {
        "disease_name": disease.name,
        "pathogen_type": disease.pathogen_type,
        "dosage": "Follow local agricultural department guidelines.",
        "pre_harvest_interval": "Check pesticide label for PHI.",
    }

    if disease.pathogen_type == "viral":
        # Viral match MUST NEVER return a cure/treatment step.
        return AdvisoryResponse(
            status="viral_isolate",
            advisory_steps=[
                "Isolate affected plants to prevent spread",
                "Use resistant variety next season",
            ],
            advisory_steps_hi=[
                "संक्रमित पौधों को अलग करें ताकि फैलाव रुक सके",
                "अगले मौसम में रोग प्रतिरोधी किस्म का उपयोग करें",
            ],
            message="Viral infections cannot be cured with chemical treatments.",
            **base_response
        )
    elif disease.pathogen_type == "nematode":
        return AdvisoryResponse(
            status="nematode_treatment",
            advisory_steps=["Soil treatment required", "Implement crop rotation"]
            + (disease.ipm_steps or []),
            advisory_steps_hi=["मिट्टी के उपचार की आवश्यकता है", "फसल चक्र अपनाएं"]
            + (disease.ipm_steps_hi or []),
            **base_response
        )
    else:
        # Fungal, Bacterial, Insect
        return AdvisoryResponse(
            status="treatable",
            advisory_steps=disease.ipm_steps or [],
            advisory_steps_hi=disease.ipm_steps_hi or [],
            **base_response
        )
