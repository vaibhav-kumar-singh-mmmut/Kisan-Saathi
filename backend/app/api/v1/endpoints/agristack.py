"""
AgriStack & Statutory Crop Discrepancy Endpoints (Phase 12).
Provides UFSI crop synchronization, live crop catalogue, and Lekhpal/Kanungo discrepancy workflows.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.jurisdiction_scope import CurrentUser
from app.services.jurisdiction_service import get_village_ids_in_scope
from app.schemas.agristack import (
    AgriStackSyncRequest,
    AgriStackSyncResponse,
    CropCatalogueItem,
    CropDiscrepancyCreate,
    CropDiscrepancyResponse,
)
from app.services import agristack_service

router = APIRouter()


@router.post(
    "/sync",
    response_model=AgriStackSyncResponse,
    summary="Synchronize crop registry from AgriStack UFSI",
    description="Fetches crop sown registry parcels from AgriStack UFSI for all villages in caller scope.",
)
def sync_agristack(
    request: AgriStackSyncRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    role = current_user["role"]
    stored_jurisdiction_type = current_user["jurisdiction_type"]
    jurisdiction_id = request.jurisdiction_id or current_user.get("jurisdiction_id", "")

    allowed_ids = get_village_ids_in_scope(
        db=db,
        jurisdiction_id=jurisdiction_id,
        role=role,
        stored_jurisdiction_type=stored_jurisdiction_type,
    )

    return agristack_service.sync_agristack_registry(
        db=db,
        allowed_village_ids=allowed_ids,
        season=request.season or "rabi",
    )


@router.get(
    "/catalogue",
    response_model=List[CropCatalogueItem],
    summary="List crop catalogue in caller's jurisdiction scope",
    description="Returns crop entries enriched with farmer and village data, filterable by crop and sync source.",
)
def get_catalogue(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    synced_only: bool = Query(
        False, description="Filter to only AgriStack-synced crops"
    ),
    crop: Optional[str] = Query(None, description="Filter by crop name"),
):
    role = current_user["role"]
    stored_jurisdiction_type = current_user["jurisdiction_type"]
    jurisdiction_id = current_user.get("jurisdiction_id", "")

    allowed_ids = get_village_ids_in_scope(
        db=db,
        jurisdiction_id=jurisdiction_id,
        role=role,
        stored_jurisdiction_type=stored_jurisdiction_type,
    )

    return agristack_service.get_crop_catalogue(
        db=db,
        allowed_village_ids=allowed_ids,
        synced_only=synced_only,
        crop=crop,
    )


@router.post(
    "/discrepancies",
    response_model=CropDiscrepancyResponse,
    summary="Report statutory crop record discrepancy",
    description="Lekhpal/Patwari/Kanungo/Tehsildar submits a ground verification mismatch against AgriStack registry.",
)
def create_discrepancy(
    data: CropDiscrepancyCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    return agristack_service.create_crop_discrepancy(
        db=db,
        discrepancy_data=data,
        current_user=current_user,
    )


@router.get(
    "/discrepancies",
    response_model=List[CropDiscrepancyResponse],
    summary="List crop discrepancies in jurisdiction scope",
    description="Returns statutory discrepancies reported for villages within the caller's jurisdiction.",
)
def list_discrepancies(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    role = current_user["role"]
    stored_jurisdiction_type = current_user["jurisdiction_type"]
    jurisdiction_id = current_user.get("jurisdiction_id", "")

    allowed_ids = get_village_ids_in_scope(
        db=db,
        jurisdiction_id=jurisdiction_id,
        role=role,
        stored_jurisdiction_type=stored_jurisdiction_type,
    )

    return agristack_service.list_crop_discrepancies(
        db=db,
        allowed_village_ids=allowed_ids,
    )
