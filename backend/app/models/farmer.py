"""
Farmer model — mobile app user, village-scoped.
M1 (AI Crop Doctor): farmers submit disease reports via the mobile app.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey

from app.core.database import Base


def _new_id() -> str:
    return str(uuid.uuid4())


class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(String(36), primary_key=True, default=_new_id)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False, unique=True)
    jurisdiction_id = Column(
        String(36),
        ForeignKey("jurisdictions.id", ondelete="SET NULL"),
        nullable=True,
    )
    agristack_id = Column(String(100), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Farmer {self.name} ({self.phone})>"
