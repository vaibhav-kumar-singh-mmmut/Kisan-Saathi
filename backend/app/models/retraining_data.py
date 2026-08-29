"""
RetrainingData model — expert corrections feeding ML retraining pipeline.
M5 (Expert Validation Loop).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, ForeignKey

from app.core.database import Base


def _new_id() -> str:
    return str(uuid.uuid4())


class RetrainingData(Base):
    __tablename__ = "retraining_data"

    id = Column(String(36), primary_key=True, default=_new_id)
    disease_report_id = Column(
        String(36),
        ForeignKey("disease_reports.id", ondelete="CASCADE"),
        nullable=False,
    )
    original_disease_id = Column(
        String(80),
        ForeignKey("disease_lookup.id", ondelete="SET NULL"),
        nullable=True,
    )
    corrected_disease_id = Column(
        String(80),
        ForeignKey("disease_lookup.id", ondelete="SET NULL"),
        nullable=True,
    )
    corrected_by = Column(
        String(36),
        ForeignKey("officials.id", ondelete="SET NULL"),
        nullable=True,
    )
    correction_notes = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<RetrainingData {self.original_disease_id}->{self.corrected_disease_id}>"
        )
