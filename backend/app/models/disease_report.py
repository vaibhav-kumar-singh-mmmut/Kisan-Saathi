"""
DiseaseReport model — farmer-submitted crop scan result.
M1 (AI Crop Doctor): created when farmer submits image -> ML inference.
M5 (Expert Validation Loop): expert_id set when KVK/Lab expert reviews.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, DateTime, ForeignKey

from app.core.database import Base


def _new_id() -> str:
    return str(uuid.uuid4())


class DiseaseReport(Base):
    __tablename__ = "disease_reports"

    id = Column(String(36), primary_key=True, default=_new_id)
    farmer_id = Column(
        String(36),
        ForeignKey("farmers.id", ondelete="CASCADE"),
        nullable=False,
    )
    jurisdiction_id = Column(
        String(36),
        ForeignKey("jurisdictions.id", ondelete="SET NULL"),
        nullable=True,
    )
    disease_id = Column(
        String(80),
        ForeignKey("disease_lookup.id", ondelete="SET NULL"),
        nullable=True,
    )
    image_url = Column(String(500), nullable=True)
    confidence_score = Column(Float, nullable=True)
    pathogen_type = Column(String(20), nullable=True)
    gps_lat = Column(Float, nullable=True)
    gps_lon = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    reported_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    expert_id = Column(
        String(36),
        ForeignKey("officials.id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<DiseaseReport {self.disease_id} conf={self.confidence_score}>"
