"""
SubsidyFlag model — PMFBY subsidy claim lifecycle (Phase 11).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON

from app.core.database import Base


def _new_id() -> str:
    return str(uuid.uuid4())


class SubsidyFlag(Base):
    __tablename__ = "subsidy_flags"

    id = Column(String(36), primary_key=True, default=_new_id)
    jurisdiction_id = Column(
        String(36),
        ForeignKey("jurisdictions.id", ondelete="SET NULL"),
        nullable=True,
    )
    disease_id = Column(
        String(80),
        ForeignKey("disease_lookup.id", ondelete="SET NULL"),
        nullable=True,
    )
    flagged_by = Column(
        String(36),
        ForeignKey("officials.id", ondelete="SET NULL"),
        nullable=True,
    )
    report_ids = Column(JSON, nullable=True)          # list[str] of UUIDs
    status = Column(String(20), nullable=False, default="pending")
    pmfby_window_expires_at = Column(DateTime(timezone=True), nullable=True)
    audit_trail = Column(JSON, nullable=True, default=list)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<SubsidyFlag {self.status} disease={self.disease_id}>"
