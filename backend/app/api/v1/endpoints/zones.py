from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.zone_scoring_service import calculate_zone_scores

router = APIRouter()

@router.post("/calculate", status_code=200)
def trigger_zone_calculation(db: Session = Depends(get_db)):
    """
    Manually triggers the zone scoring engine (Phase 8).
    In production (Phase 10), this would be handled by a scheduled Celery task.
    """
    calculate_zone_scores(db)
    return {"message": "Zone scoring calculation completed successfully."}
