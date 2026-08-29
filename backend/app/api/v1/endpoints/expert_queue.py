from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid

from app.core.database import get_db
from app.models.disease_report import DiseaseReport
from app.models.retraining_data import RetrainingData
from app.schemas.expert_queue import ExpertReviewRequest, ExpertQueueItem
from app.utils.jurisdiction_scope import CurrentUser

router = APIRouter()


@router.get("", response_model=List[ExpertQueueItem])
def get_queue(db: Session = Depends(get_db)):
    """
    Get all pending disease reports that require expert validation.
    """
    reports = (
        db.query(DiseaseReport)
        .filter(DiseaseReport.status == "pending")
        .order_by(
            DiseaseReport.confidence_score.asc().nulls_first(),
            DiseaseReport.reported_at.asc(),
        )
        .all()
    )
    return reports


@router.post("/{report_id}/validate")
def validate_report(
    report_id: str,
    review: ExpertReviewRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    """
    Validate a pending report.
    Updates the report status and writes a retraining record without altering the original disease_id.
    """
    report = db.query(DiseaseReport).filter(DiseaseReport.id == report_id).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.status != "pending":
        raise HTTPException(status_code=400, detail="Report is not pending validation")

    expert_id = current_user.get("sub")
    if not expert_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Write the correction to retraining_data
    if review.corrected_disease_id:
        retraining = RetrainingData(
            id=str(uuid.uuid4()),
            disease_report_id=report.id,
            original_disease_id=report.disease_id,
            corrected_disease_id=review.corrected_disease_id,
            corrected_by=expert_id,
            correction_notes=review.notes,
            created_at=datetime.now(timezone.utc),
        )
        db.add(retraining)

    # Update the report status, leaving original disease_id untouched
    report.status = "reviewed"
    report.expert_id = expert_id
    report.confirmed_at = datetime.now(timezone.utc)

    db.commit()
    return {"status": "reviewed", "message": "Report validated successfully"}
