from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.disease_report import DiseaseReport

router = APIRouter()

class DiseaseReportCreate(BaseModel):
    farmer_id: str
    jurisdiction_id: Optional[str] = None
    disease_id: Optional[str] = None
    image_url: Optional[str] = None
    confidence_score: Optional[float] = None
    pathogen_type: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None

@router.post("")
def create_disease_report(report: DiseaseReportCreate, db: Session = Depends(get_db)):
    """
    Save a disease prediction result from the farmer portal to the database.
    """
    db_report = DiseaseReport(
        farmer_id=report.farmer_id,
        jurisdiction_id=report.jurisdiction_id,
        disease_id=report.disease_id,
        image_url=report.image_url,
        confidence_score=report.confidence_score,
        pathogen_type=report.pathogen_type,
        gps_lat=report.gps_lat,
        gps_lon=report.gps_lon,
        status="pending"
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    return {
        "id": db_report.id,
        "message": "Disease report saved successfully and queued for expert review."
    }
