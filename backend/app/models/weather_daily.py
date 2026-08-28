"""
WeatherDaily model — daily weather records per village.
M2 (Crop Risk Radar): checked against disease_lookup.weather_triggers.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Date, DateTime, ForeignKey

from app.core.database import Base


def _new_id() -> str:
    return str(uuid.uuid4())


class WeatherDaily(Base):
    __tablename__ = "weather_daily"

    id = Column(String(36), primary_key=True, default=_new_id)
    jurisdiction_id = Column(
        String(36),
        ForeignKey("jurisdictions.id", ondelete="CASCADE"),
        nullable=False,
    )
    date = Column(Date, nullable=False)
    temp_c_min = Column(Float, nullable=True)
    temp_c_max = Column(Float, nullable=True)
    humidity_pct = Column(Float, nullable=True)
    rainfall_mm = Column(Float, nullable=True)
    wind_direction = Column(String(20), nullable=True)
    wind_speed_kmh = Column(Float, nullable=True)
    source = Column(String(40), nullable=False, default="mock")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<WeatherDaily {self.date} temp={self.temp_c_min}-{self.temp_c_max}>"
