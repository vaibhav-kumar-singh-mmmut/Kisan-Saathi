"""
Pydantic v2 schemas for jurisdiction / dashboard endpoints.
"""
from typing import Optional
from pydantic import BaseModel


class VillageSummary(BaseModel):
    """Village row returned by GET /dashboard/villages."""
    id: str
    name: str
    jurisdiction_type: str
    parent_id: Optional[str] = None
    lat: Optional[str] = None
    lon: Optional[str] = None
    state: str
    district_name: Optional[str] = None

    model_config = {"from_attributes": True}
