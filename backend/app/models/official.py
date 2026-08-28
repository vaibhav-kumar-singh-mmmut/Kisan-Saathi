"""
Official model — all 21 roles across Revenue, Development, Panchayat, Service wings.
Used for: auth (Phase 2), expert queue (M5), subsidy approval (Phase 11).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

WINGS = ("revenue", "development", "panchayat", "service")

# All roles per AI_AGENT_BUILD_PROMPT.md Phase 2
OFFICIAL_ROLES = (
    "Farmer",
    "Pradhan",
    "Lekhpal/Patwari",
    "Kanungo",
    "DM",
    "Adl. Commissioner",
    "Adl. DM",
    "Chief Revenue Officer",
    "SDM",
    "Tehsildar",
    "Naib Tehsildar",
    "CDO",
    "DDO",
    "PD (DRDA)",
    "DC (MGNREGA)",
    "DC (NRLM)",
    "BDO",
    "Agriculture/Horticulture Officer",
    "KVK Expert",
    "Drone Pilot",
    "Drone Assistant",
    "CHC Manager",
    "FPO Representative",
)


class Official(Base):
    __tablename__ = "officials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False, unique=True)
    role = Column(String(80), nullable=False)
    wing = Column(SAEnum(*WINGS, name="wing_enum"), nullable=False)
    jurisdiction_type = Column(String(40), nullable=False)
    jurisdiction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("jurisdictions.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="officials")
    expert_reviews = relationship(
        "DiseaseReport", back_populates="expert", foreign_keys="DiseaseReport.expert_id"
    )
    subsidy_flags = relationship(
        "SubsidyFlag", back_populates="flagged_by_official",
        foreign_keys="SubsidyFlag.flagged_by",
    )
    retraining_corrections = relationship(
        "RetrainingData", back_populates="corrected_by_official",
        foreign_keys="RetrainingData.corrected_by",
    )

    def __repr__(self) -> str:
        return f"<Official {self.role}:{self.name}>"
