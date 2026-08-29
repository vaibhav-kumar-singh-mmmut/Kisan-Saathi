"""
Post-Harvest WDRA Storage Advisory Endpoints (Phase 12).
Surfaces WDRA warehouse holding recommendations and e-NWR pledge loan details for Green Zone farmers.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.jurisdiction_scope import CurrentUser
from app.schemas.post_harvest import FarmerPostHarvestResponse
from app.services import post_harvest_service
from app.models.farmer import Farmer

router = APIRouter()


@router.get(
    "/storage-suggestions",
    response_model=FarmerPostHarvestResponse,
    summary="Get WDRA post-harvest warehouse & e-NWR pledge advice",
    description="Returns price-dip protection recommendations, WDRA warehouse allocations, and e-NWR pledge loan eligibility.",
)
def get_storage_suggestions(
    village_id: Optional[str] = Query(
        None, description="Village ID to evaluate (defaults to user village)"
    ),
    farmer_id: Optional[str] = Query(
        None, description="Specific farmer ID (optional)"
    ),
    current_user: CurrentUser = None,
    db: Session = Depends(get_db),
):
    target_village_id = village_id

    # If village_id not provided, try resolving from current user's profile
    if not target_village_id:
        if current_user.get("role") == "Farmer" and current_user.get("user_id"):
            farmer = (
                db.query(Farmer).filter(Farmer.id == current_user["user_id"]).first()
            )
            if farmer:
                target_village_id = farmer.jurisdiction_id
                farmer_id = farmer_id or farmer.id
        elif current_user.get("jurisdiction_id"):
            target_village_id = current_user["jurisdiction_id"]

    if not target_village_id:
        raise HTTPException(
            status_code=400,
            detail="village_id is required to evaluate post-harvest storage suggestions.",
        )

    return post_harvest_service.evaluate_post_harvest_advice(
        db=db,
        village_id=target_village_id,
        farmer_id=farmer_id,
    )
