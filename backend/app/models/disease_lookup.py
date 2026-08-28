"""
DiseaseLookup model — seeded from disease_lookup.json (38 entries).
M1/M3: drives ML inference label mapping + Phase 6 pathogen-branched advisory.
M2: weather_triggers feed zone-scoring risk amplifiers.

pathogen_type enum: fungal | bacterial | viral | nematode | insect
  - "insect" added for pure pest entries (wheat_pests, cotton_whitefly, etc.)
  - mustard_pests_diseases stored as "insect" with secondary_pathogen_notes JSON (Option A)

Uses portable column types (JSON instead of ARRAY/JSONB) for SQLite dev compatibility.
In production (PostgreSQL), these serialize/deserialize identically.
"""
from sqlalchemy import Column, String, Boolean, Integer, JSON

from app.core.database import Base


class DiseaseLookup(Base):
    __tablename__ = "disease_lookup"

    # Use the string id from disease_lookup.json (e.g. "wheat_yellow_rust")
    id = Column(String(80), primary_key=True)
    name = Column(String(200), nullable=False)
    crops = Column(JSON, nullable=False)                     # list[str]
    severity = Column(String(20), nullable=False)            # low/medium/high
    pathogen_type = Column(String(20), nullable=False)       # fungal/bacterial/viral/nematode/insect
    spread_medium = Column(JSON, nullable=True)              # list[str]
    spread_radius_km = Column(Integer, nullable=True)
    seasonal_window = Column(String(100), nullable=True)
    weather_triggers = Column(JSON, nullable=True)           # dict
    risk_factors = Column(JSON, nullable=True)               # list[str] or list[dict]
    irreversible = Column(Boolean, nullable=False, default=False)
    ipm_steps = Column(JSON, nullable=True)                  # list[str]
    growth_stage = Column(String(80), nullable=True)
    compound_risk_with = Column(JSON, nullable=True)         # list[str]
    regional_note = Column(String(500), nullable=True)
    regional_source = Column(String(500), nullable=True)
    # Option A: secondary pathogen notes for mixed entries like mustard_pests_diseases
    secondary_pathogen_notes = Column(JSON, nullable=True)   # dict

    def __repr__(self) -> str:
        return f"<DiseaseLookup {self.id} ({self.pathogen_type}/{self.severity})>"
