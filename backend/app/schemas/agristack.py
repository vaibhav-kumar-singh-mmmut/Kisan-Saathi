from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict


class AgriStackSyncRequest(BaseModel):
    jurisdiction_id: Optional[str] = None  # Village/Tehsil ID, or None for all in scope
    season: Optional[str] = "rabi"  # rabi, kharif, zaid


class AgriStackParcelRecord(BaseModel):
    farmer_name: str
    farmer_phone: str
    survey_number: str  # Khasra / Survey No
    crop_name: str
    acreage_ha: float
    growth_stage: str
    sowing_date: Optional[str] = None
    harvest_date: Optional[str] = None
    season: str
    village_name: str


class AgriStackSyncResponse(BaseModel):
    status: str
    synced_records_count: int
    village_count: int
    message: str
    synced_at: datetime


class CropCatalogueItem(BaseModel):
    id: str
    crop_name: str
    acreage_ha: float
    growth_stage: Optional[str]
    season: str
    farmer_name: Optional[str] = None
    farmer_phone: Optional[str] = None
    village_id: str
    village_name: str
    lat: Optional[str] = None
    lon: Optional[str] = None
    synced_from_agristack: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CropDiscrepancyCreate(BaseModel):
    crop_entry_id: Optional[str] = None
    jurisdiction_id: str
    survey_number: Optional[str] = None
    farmer_name: Optional[str] = None
    reported_crop: str
    actual_crop_observed: str
    reported_acreage_ha: Optional[float] = None
    actual_acreage_ha: Optional[float] = None
    discrepancy_type: str = "crop_mismatch"
    notes: Optional[str] = None


class CropDiscrepancyResponse(BaseModel):
    id: str
    crop_entry_id: Optional[str]
    jurisdiction_id: str
    village_name: Optional[str] = None
    official_id: Optional[str]
    official_name: Optional[str] = None
    official_role: Optional[str] = None
    farmer_name: Optional[str]
    survey_number: Optional[str]
    reported_crop: str
    actual_crop_observed: str
    reported_acreage_ha: Optional[float]
    actual_acreage_ha: Optional[float]
    discrepancy_type: str
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
