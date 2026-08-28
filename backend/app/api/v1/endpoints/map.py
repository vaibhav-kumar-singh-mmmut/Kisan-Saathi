from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.core.database import get_db
from app.utils.jurisdiction_scope import CurrentUser
from app.services.jurisdiction_service import get_village_ids_in_scope
from app.models.jurisdiction import Jurisdiction
from app.models.zone_status import ZoneStatus

router = APIRouter()

@router.get("/hotspots", response_model=Dict[str, Any])
def get_map_hotspots(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Returns GeoJSON FeatureCollection for all villages in the user's jurisdiction scope,
    including their current ZoneStatus (color, score, report_count).
    Used by Phase 9 Officer Map.
    """
    jurisdiction_id = current_user.get("jurisdiction_id")
    role = current_user.get("role")
    jurisdiction_type = current_user.get("jurisdiction_type")
    
    if not jurisdiction_id:
        return {"type": "FeatureCollection", "features": []}

    # 1. Get scope (server-side filtering based on role)
    visible_village_ids = get_village_ids_in_scope(db, jurisdiction_id, role, jurisdiction_type)
    
    if not visible_village_ids:
        return {"type": "FeatureCollection", "features": []}

    # 2. Fetch all visible villages and their LATEST zone status
    # We use a subquery to get the latest zone status per village
    subq = (
        select(
            ZoneStatus.jurisdiction_id,
            func.max(ZoneStatus.computed_at).label("max_computed_at")
        )
        .where(ZoneStatus.jurisdiction_id.in_(visible_village_ids))
        .group_by(ZoneStatus.jurisdiction_id)
        .subquery()
    )

    latest_zones = (
        db.query(ZoneStatus)
        .join(
            subq,
            (ZoneStatus.jurisdiction_id == subq.c.jurisdiction_id) &
            (ZoneStatus.computed_at == subq.c.max_computed_at)
        )
        .all()
    )
    
    zone_map = {z.jurisdiction_id: z for z in latest_zones}
    
    # 3. Fetch village geo data
    villages = db.query(Jurisdiction).filter(Jurisdiction.id.in_(visible_village_ids)).all()

    # 4. Build GeoJSON
    features = []
    for village in villages:
        if village.lat is None or village.lon is None:
            continue
            
        z = zone_map.get(village.id)
        color = z.color if z else "green"
        score = z.score if z else 10.0
        report_count = z.report_count if z else 0
        
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [village.lon, village.lat] # GeoJSON is [lon, lat]
            },
            "properties": {
                "id": village.id,
                "name": village.name,
                "color": color,
                "score": score,
                "report_count": report_count
            }
        }
        features.append(feature)
        
    return {
        "type": "FeatureCollection",
        "features": features
    }
