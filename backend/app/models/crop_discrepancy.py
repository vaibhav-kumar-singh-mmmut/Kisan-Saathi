"""
CropDiscrepancy model — statutory crop record discrepancy reports.
Filed by Lekhpal/Patwari, Kanungo, and revenue officers when ground inspection
differs from AgriStack's Crop Sown Registry.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text

from app.core.database import Base


def _new_id() -> str:
    return str(uuid.uuid4())


class CropDiscrepancy(Base):
    __tablename__ = "crop_discrepancies"

    id = Column(String(36), primary_key=True, default=_new_id)
    crop_entry_id = Column(
        String(36),
        ForeignKey("crop_entries.id", ondelete="SET NULL"),
        nullable=True,
    )
    jurisdiction_id = Column(
        String(36),
        ForeignKey("jurisdictions.id", ondelete="CASCADE"),
        nullable=False,
    )
    official_id = Column(
        String(36),
        ForeignKey("officials.id", ondelete="SET NULL"),
        nullable=True,
    )
    farmer_name = Column(String(150), nullable=True)
    survey_number = Column(String(50), nullable=True)  # Khasra / Survey No.
    reported_crop = Column(String(100), nullable=False)
    actual_crop_observed = Column(String(100), nullable=False)
    reported_acreage_ha = Column(Float, nullable=True)
    actual_acreage_ha = Column(Float, nullable=True)
    discrepancy_type = Column(
        String(50), nullable=False, default="crop_mismatch"
    )  # crop_mismatch, area_mismatch, stage_mismatch, unrecorded_plot
    status = Column(
        String(30), nullable=False, default="pending"
    )  # pending, verified, resolved
    notes = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<CropDiscrepancy {self.survey_number}: {self.reported_crop} vs {self.actual_crop_observed}>"
