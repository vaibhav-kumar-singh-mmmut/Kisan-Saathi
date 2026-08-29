from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class WDRAWarehouse(BaseModel):
    name: str
    code: str
    location: str
    distance_km: float
    capacity_mt: int
    available_mt: int
    contact: str


class StorageAdvice(BaseModel):
    crop_name: str
    crop_category: str  # pulse, oilseed, cereal
    zone_color: str
    recommendation: str  # "STORE_WDRA", "MONITOR", "STANDARD_SELL"
    post_harvest_dip_pct: float  # e.g., 18.5%
    current_mandi_price_inr_qtl: float
    expected_peak_price_inr_qtl: float
    holding_period_days: int
    enwr_pledge_loan_eligible: bool
    max_pledge_loan_pct: float  # 70%
    effective_interest_rate_pct: float  # 4.0%
    rationale: str
    nearest_warehouses: List[WDRAWarehouse] = []
    deficit_market_routing: Optional[str] = None


class FarmerPostHarvestResponse(BaseModel):
    farmer_id: Optional[str] = None
    village_id: str
    village_name: str
    zone_color: str
    advisories: List[StorageAdvice] = []

    model_config = ConfigDict(from_attributes=True)
