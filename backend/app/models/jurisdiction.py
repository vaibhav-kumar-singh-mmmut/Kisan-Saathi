"""
Jurisdiction model — self-referencing tree.
Hierarchy: District -> Tehsil -> Block -> Village / Panchayat

All modules: shared infrastructure for jurisdiction-scoped filtering (Phase 2+).

Uses String PKs (UUID stored as text) for SQLite compatibility in dev.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey

from app.core.database import Base

JURISDICTION_TYPES = ("district", "tehsil", "block", "village", "panchayat")


def _new_id() -> str:
    return str(uuid.uuid4())


class Jurisdiction(Base):
    __tablename__ = "jurisdictions"

    id = Column(String(36), primary_key=True, default=_new_id)
    name = Column(String(200), nullable=False)
    jurisdiction_type = Column(
        String(20), nullable=False
    )  # district/tehsil/block/village/panchayat
    parent_id = Column(
        String(36),
        ForeignKey("jurisdictions.id", ondelete="SET NULL"),
        nullable=True,
    )
    state = Column(String(100), nullable=False, default="Uttar Pradesh")
    district_name = Column(String(100), nullable=True)
    lat = Column(String(20), nullable=True)
    lon = Column(String(20), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Jurisdiction {self.jurisdiction_type}:{self.name}>"
