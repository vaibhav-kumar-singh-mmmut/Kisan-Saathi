"""
ZoneStatus model — per-village zone classification output.
M2 (Crop Risk Radar) / M4 (Geo Disease Hotspot Maps).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey

from app.core.database import Base


def _new_id() -> str:
    return str(uuid.uuid4())


class ZoneStatus(Base):
    __tablename__ = "zone_status"

    id = Column(String(36), primary_key=True, default=_new_id)
    jurisdiction_id = Column(
        String(36),
        ForeignKey("jurisdictions.id", ondelete="CASCADE"),
        nullable=False,
    )
    color = Column(String(20), nullable=False, default="green")
    score = Column(Float, nullable=True)
    report_count = Column(Integer, nullable=False, default=0)
    growth_rate = Column(Float, nullable=True)
    affected_area_pct = Column(Float, nullable=True)
    weather_trigger_fired = Column(Boolean, nullable=False, default=False)
    alert_fired = Column(Boolean, nullable=False, default=False)
    computed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<ZoneStatus {self.color} score={self.score}>"
