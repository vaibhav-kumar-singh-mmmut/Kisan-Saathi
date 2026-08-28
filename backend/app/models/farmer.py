"""
Farmer model — mobile app user, village-scoped.
M1 (AI Crop Doctor): farmers submit disease reports via the mobile app.
AgriStack sync populated in Phase 12 via UFSI.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False, unique=True)
    jurisdiction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("jurisdictions.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Phase 12: populated via AgriStack UFSI sync
    agristack_id = Column(String(100), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="farmers")
    crop_entries = relationship("CropEntry", back_populates="farmer")
    disease_reports = relationship("DiseaseReport", back_populates="farmer")

    def __repr__(self) -> str:
        return f"<Farmer {self.name} ({self.phone})>"
