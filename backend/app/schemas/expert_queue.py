from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class ExpertReviewRequest(BaseModel):
    corrected_disease_id: Optional[str] = None
    notes: Optional[str] = None

class ExpertQueueItem(BaseModel):
    id: str
    disease_id: Optional[str]
    confidence_score: Optional[float]
    reported_at: datetime
    status: str
    image_url: Optional[str]

    class Config:
        from_attributes = True
