"""
Jurisdiction model — self-referencing tree.
Hierarchy: District → Tehsil → Block → Village / Panchayat

All modules: shared infrastructure for jurisdiction-scoped filtering (Phase 2+).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

try:
    from geoalchemy2 import Geometry
    _HAS_POSTGIS = True
except ImportError:
    _HAS_POSTGIS = False

from app.core.database import Base

JURISDICTION_TYPES = ("district", "tehsil", "block", "village", "panchayat")


class Jurisdiction(Base):
    __tablename__ = "jurisdictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    jurisdiction_type = Column(
        SAEnum(*JURISDICTION_TYPES, name="jurisdiction_type_enum"),
        nullable=False,
    )
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("jurisdictions.id", ondelete="SET NULL"),
        nullable=True,
    )
    state = Column(String(100), nullable=False, default="Uttar Pradesh")
    district_name = Column(String(100), nullable=True)

    # PostGIS point — nullable so the model loads without PostGIS extension in dev
    if _HAS_POSTGIS:
        geom = Column(Geometry("POINT", srid=4326), nullable=True)

    # Fallback lat/lon for dev without PostGIS
    lat = Column(String(20), nullable=True)
    lon = Column(String(20), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    parent = relationship(
        "Jurisdiction", remote_side="Jurisdiction.id", backref="children"
    )
    officials = relationship("Official", back_populates="jurisdiction")
    farmers = relationship("Farmer", back_populates="jurisdiction")
    disease_reports = relationship("DiseaseReport", back_populates="jurisdiction")
    weather_records = relationship("WeatherDaily", back_populates="jurisdiction")
    zone_statuses = relationship("ZoneStatus", back_populates="jurisdiction")

    def __repr__(self) -> str:
        return f"<Jurisdiction {self.jurisdiction_type}:{self.name}>"
