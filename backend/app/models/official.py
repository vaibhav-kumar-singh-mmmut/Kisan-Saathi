"""
Official model — all 21 roles across Revenue, Development, Panchayat, Service wings.
Used for: auth (Phase 2), expert queue (M5), subsidy approval (Phase 11).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey

from app.core.database import Base

WINGS = ("revenue", "development", "panchayat", "service")


def _new_id() -> str:
    return str(uuid.uuid4())


class Official(Base):
    __tablename__ = "officials"

    id = Column(String(36), primary_key=True, default=_new_id)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False, unique=True)
    role = Column(String(80), nullable=False)
    wing = Column(String(20), nullable=False)       # revenue/development/panchayat/service
    jurisdiction_type = Column(String(40), nullable=False)
    jurisdiction_id = Column(
        String(36),
        ForeignKey("jurisdictions.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Official {self.role}:{self.name}>"
