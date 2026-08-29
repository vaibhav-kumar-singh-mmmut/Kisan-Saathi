"""
Phase 11 — Subsidy/PMFBY + Drone Booking: DB model for DroneBooking.
Maps farmer spray request to nearest CHC/SHG by proximity.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, DateTime, ForeignKey

from app.core.database import Base


def _new_id() -> str:
    return str(uuid.uuid4())


class DroneBooking(Base):
    __tablename__ = "drone_bookings"

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
    disease_report_id = Column(
        String(36),
        ForeignKey("disease_reports.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Nearest CHC/SHG resolved at booking time
    chc_id = Column(String(80), nullable=True)
    chc_name = Column(String(200), nullable=True)
    chc_lat = Column(Float, nullable=True)
    chc_lon = Column(Float, nullable=True)
    chc_distance_km = Column(Float, nullable=True)

    # Farmer-provided details
    acreage_ha = Column(Float, nullable=True)
    crop_name = Column(String(100), nullable=True)
    notes = Column(String(500), nullable=True)

    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending/confirmed/completed/cancelled

    booked_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<DroneBooking farmer={self.farmer_id} chc={self.chc_name} status={self.status}>"
