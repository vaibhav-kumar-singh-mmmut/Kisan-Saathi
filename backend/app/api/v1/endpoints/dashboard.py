"""
Dashboard endpoint — the single jurisdiction-scoped village view.

GET /api/v1/dashboard/villages
  → returns villages the caller is allowed to see (server-side filtered)
  → optional query params: crop, zone, disease (for Phase 9 map filters)

Design: ONE route for ALL roles. The jurisdiction_service resolves the
village ID scope from the caller's JWT; the DB query is then filtered
to only those IDs. No per-role branching in this file.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import datetime, timedelta
import json

from app.core.database import get_db
from app.models.jurisdiction import Jurisdiction
from app.models.zone_status import ZoneStatus
from app.schemas.jurisdiction import VillageSummary
from app.services.jurisdiction_service import get_village_ids_in_scope
from app.utils.jurisdiction_scope import CurrentUser

router = APIRouter()


@router.get(
    "/villages",
    response_model=list[VillageSummary],
    summary="List villages in caller's jurisdiction scope",
    description=(
        "Returns all villages the authenticated caller is permitted to see. "
        "Scope is derived server-side from the JWT — a Tehsildar sees only their tehsil's "
        "villages; a DM sees all villages in the district. "
        "Optional filters: `zone` (red/orange/green/incoming_risk), `crop` (crop name)."
    ),
)
def get_villages(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    zone: Optional[str] = Query(
        None, description="Filter by zone color: red/orange/green/incoming_risk"
    ),
    crop: Optional[str] = Query(
        None, description="Filter by crop name (partial match)"
    ),
):
    role = current_user["role"]
    jurisdiction_id = current_user.get("jurisdiction_id", "")
    stored_jurisdiction_type = current_user["jurisdiction_type"]

    # Resolve which village IDs this caller can see
    allowed_ids = get_village_ids_in_scope(
        db=db,
        jurisdiction_id=jurisdiction_id,
        role=role,
        stored_jurisdiction_type=stored_jurisdiction_type,
    )

    if not allowed_ids:
        return []

    # Build the village query scoped to allowed_ids
    stmt = select(Jurisdiction).where(
        Jurisdiction.jurisdiction_type == "village",
        Jurisdiction.id.in_(allowed_ids),
    )

    villages = db.execute(stmt).scalars().all()

    # Apply optional zone filter (join zone_status)
    if zone:
        # Get village IDs with the requested zone color
        zone_rows = (
            db.execute(
                select(ZoneStatus.jurisdiction_id).where(
                    ZoneStatus.color == zone,
                    ZoneStatus.jurisdiction_id.in_(allowed_ids),
                )
            )
            .scalars()
            .all()
        )
        zone_set = set(zone_rows)
        villages = [v for v in villages if v.id in zone_set]

    # Apply optional crop filter (via crop_entries — simplified for Phase 2)
    # Full crop catalogue layer is Phase 9; here we do a basic name filter via
    # the CropEntry table if crop param is provided.
    if crop:
        from app.models.crop_entry import CropEntry

        crop_village_ids = (
            db.execute(
                select(CropEntry.farmer_id).where(
                    CropEntry.crop_name.ilike(f"%{crop}%")
                )
            )
            .scalars()
            .all()
        )
        # Get the jurisdiction_id for farmers matching those IDs
        from app.models.farmer import Farmer

        farmer_juris = (
            db.execute(
                select(Farmer.jurisdiction_id).where(Farmer.id.in_(crop_village_ids))
            )
            .scalars()
            .all()
        )
        crop_village_set = set(farmer_juris)
        villages = [v for v in villages if v.id in crop_village_set]

    return [VillageSummary.model_validate(v) for v in villages]

@router.get(
    "/analytics",
    summary="Get unified analytics for the officer dashboard charts",
)
def get_analytics(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    zone: Optional[str] = Query(None),
    crop: Optional[str] = Query(None),
):
    role = current_user["role"]
    jurisdiction_id = current_user.get("jurisdiction_id", "")
    stored_jurisdiction_type = current_user["jurisdiction_type"]

    allowed_ids = get_village_ids_in_scope(
        db=db,
        jurisdiction_id=jurisdiction_id,
        role=role,
        stored_jurisdiction_type=stored_jurisdiction_type,
    )

    if not allowed_ids:
        return {"trend": [], "zone_distribution": [], "disease_frequency": []}
    
    # Optional filters logic (same as /villages to keep scope exact)
    filtered_ids = set(allowed_ids)
    if zone:
        zone_rows = db.execute(select(ZoneStatus.jurisdiction_id).where(ZoneStatus.color == zone, ZoneStatus.jurisdiction_id.in_(allowed_ids))).scalars().all()
        filtered_ids.intersection_update(zone_rows)
    
    if crop:
        from app.models.crop_entry import CropEntry
        from app.models.farmer import Farmer
        crop_village_ids = db.execute(select(CropEntry.farmer_id).where(CropEntry.crop_name.ilike(f"%{crop}%"))).scalars().all()
        farmer_juris = db.execute(select(Farmer.jurisdiction_id).where(Farmer.id.in_(crop_village_ids))).scalars().all()
        filtered_ids.intersection_update(farmer_juris)

    if not filtered_ids:
        return {"trend": [], "zone_distribution": [], "disease_frequency": []}
    
    filtered_list = list(filtered_ids)

    # 1. Zone Distribution (latest per village)
    subq = (
        select(
            ZoneStatus.jurisdiction_id,
            func.max(ZoneStatus.computed_at).label("max_computed_at"),
        )
        .where(ZoneStatus.jurisdiction_id.in_(filtered_list))
        .group_by(ZoneStatus.jurisdiction_id)
        .subquery()
    )

    latest_zones = (
        db.query(ZoneStatus.color, func.count(ZoneStatus.id).label("count"))
        .join(
            subq,
            (ZoneStatus.jurisdiction_id == subq.c.jurisdiction_id)
            & (ZoneStatus.computed_at == subq.c.max_computed_at),
        )
        .group_by(ZoneStatus.color)
        .all()
    )
    zone_distribution = [{"zone": z.color, "count": z.count} for z in latest_zones]

    # 2. Disease Frequency
    from app.models.disease_report import DiseaseReport
    from app.models.disease_lookup import DiseaseLookup
    disease_freq = (
        db.query(DiseaseReport.disease_id, func.count(DiseaseReport.id).label("count"))
        .where(DiseaseReport.jurisdiction_id.in_(filtered_list))
        .group_by(DiseaseReport.disease_id)
        .order_by(func.count(DiseaseReport.id).desc())
        .limit(5)
        .all()
    )
    disease_frequency = [{"disease": d.disease_id.replace('_', ' ').title(), "count": d.count} for d in disease_freq]

    # 3. Report Trend (last 14 days)
    # Using SQLite date function for string dates
    fourteen_days_ago = datetime.utcnow() - timedelta(days=14)
    trend_rows = (
        db.query(
            func.date(DiseaseReport.created_at).label("report_date"),
            func.count(DiseaseReport.id).label("count")
        )
        .where(DiseaseReport.jurisdiction_id.in_(filtered_list))
        .where(DiseaseReport.created_at >= fourteen_days_ago)
        .group_by(func.date(DiseaseReport.created_at))
        .order_by(func.date(DiseaseReport.created_at))
        .all()
    )
    trend = [{"date": t.report_date, "count": t.count} for t in trend_rows]

    return {
        "trend": trend,
        "zone_distribution": zone_distribution,
        "disease_frequency": disease_frequency
    }
