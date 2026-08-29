from typing import List, Optional
from pydantic import BaseModel


class AdvisoryResponse(BaseModel):
    status: str
    disease_name: Optional[str] = None
    pathogen_type: Optional[str] = None
    advisory_steps: Optional[List[str]] = None
    advisory_steps_hi: Optional[List[str]] = None
    dosage: Optional[str] = None
    pre_harvest_interval: Optional[str] = None
    message: Optional[str] = None
