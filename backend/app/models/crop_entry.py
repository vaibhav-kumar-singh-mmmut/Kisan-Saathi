"""
CropEntry model — what a farmer is currently growing.
M1/M2: drives zone scoring's affected_area_pct calculation (Phase 8).
Phase 12: synced from AgriStack Crop Sown Registry via UFSI.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Float, Boolean, Date, DateTime,
    ForeignKey, Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

SEASONS = ("rabi", "kharif", "zaid")
GROWTH_STAGES = (
    "nursery", "seedling", "vegetative", "flowering",
    "grain_fill", "maturity", "post_harvest",
)


class CropEntry(Base):
    __tablename__ = "crop_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("farmers.id", ondelete="CASCADE"),
        nullable=False,
    )
    crop_name = Column(String(100), nullable=False)
    acreage_ha = Column(Float, nullable=False)
    growth_stage = Column(
        SAEnum(*GROWTH_STAGES, name="growth_stage_enum"), nullable=True
    )
    sowing_date = Column(Date, nullable=True)
    harvest_date = Column(Date, nullable=True)
    season = Column(SAEnum(*SEASONS, name="season_enum"), nullable=False)
    # Phase 12: True once synced from AgriStack via UFSI
    synced_from_agristack = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    farmer = relationship("Farmer", back_populates="crop_entries")

    def __repr__(self) -> str:
        return f"<CropEntry {self.crop_name} {self.acreage_ha}ha>"
