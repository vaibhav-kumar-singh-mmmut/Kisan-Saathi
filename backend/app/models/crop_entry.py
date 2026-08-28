"""
CropEntry model — what a farmer is currently growing.
M1/M2: drives zone scoring's affected_area_pct calculation (Phase 8).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Boolean, Date, DateTime, ForeignKey

from app.core.database import Base


def _new_id() -> str:
    return str(uuid.uuid4())


class CropEntry(Base):
    __tablename__ = "crop_entries"

    id = Column(String(36), primary_key=True, default=_new_id)
    farmer_id = Column(
        String(36),
        ForeignKey("farmers.id", ondelete="CASCADE"),
        nullable=False,
    )
    crop_name = Column(String(100), nullable=False)
    acreage_ha = Column(Float, nullable=False)
    growth_stage = Column(String(40), nullable=True)
    sowing_date = Column(Date, nullable=True)
    harvest_date = Column(Date, nullable=True)
    season = Column(String(10), nullable=False)     # rabi/kharif/zaid
    synced_from_agristack = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<CropEntry {self.crop_name} {self.acreage_ha}ha>"
