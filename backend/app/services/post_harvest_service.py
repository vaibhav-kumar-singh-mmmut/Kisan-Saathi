"""
Post-Harvest Storage & e-NWR Advisory Engine (Phase 12).
Evaluates Green Zone farmers harvesting pulses and oilseeds, generating WDRA-accredited
warehouse holding suggestions, e-NWR pledge loan eligibility (~4% rate), and surplus-deficit market routing.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.jurisdiction import Jurisdiction
from app.models.farmer import Farmer
from app.models.crop_entry import CropEntry
from app.models.zone_status import ZoneStatus
from app.schemas.post_harvest import (
    StorageAdvice,
    WDRAWarehouse,
    FarmerPostHarvestResponse,
)

# Crops eligible for WDRA pledge storage advisory
PULSE_CROPS = {
    "chickpea",
    "gram",
    "chana",
    "lentil",
    "masoor",
    "moong",
    "pea",
    "matar",
    "pigeon_pea",
    "arhar",
    "tur",
    "urad",
}
OILSEED_CROPS = {
    "mustard",
    "sarson",
    "soybean",
    "groundnut",
    "sunflower",
    "sesame",
    "til",
}

# Market baseline prices and expected peak dynamics (INR / Quintal)
COMMODITY_PRICES: Dict[str, Dict[str, Any]] = {
    "chickpea": {
        "current_mandi": 5350.0,
        "peak_price": 6450.0,
        "dip_pct": 20.5,
        "holding_days": 75,
    },
    "lentil": {
        "current_mandi": 5900.0,
        "peak_price": 6950.0,
        "dip_pct": 17.8,
        "holding_days": 60,
    },
    "mustard": {
        "current_mandi": 5400.0,
        "peak_price": 6350.0,
        "dip_pct": 17.6,
        "holding_days": 90,
    },
    "pea": {
        "current_mandi": 4800.0,
        "peak_price": 5700.0,
        "dip_pct": 18.75,
        "holding_days": 60,
    },
    "pigeon_pea": {
        "current_mandi": 6800.0,
        "peak_price": 8200.0,
        "dip_pct": 20.6,
        "holding_days": 90,
    },
    "moong": {
        "current_mandi": 7200.0,
        "peak_price": 8500.0,
        "dip_pct": 18.0,
        "holding_days": 60,
    },
}

# Accredited WDRA Warehouses in the region
REGIONAL_WDRA_WAREHOUSES: List[WDRAWarehouse] = [
    WDRAWarehouse(
        name="CWC Central Warehouse Sitapur",
        code="WDRA-UP-STP-01",
        location="Industrial Area, Sitapur, UP",
        distance_km=14.5,
        capacity_mt=15000,
        available_mt=4200,
        contact="+91-5862-245100",
    ),
    WDRAWarehouse(
        name="UP State Warehousing Corp Maholi",
        code="WDRA-UP-MHL-03",
        location="Near Mandi Samiti, Maholi",
        distance_km=8.2,
        capacity_mt=8000,
        available_mt=2100,
        contact="+91-5862-289412",
    ),
    WDRAWarehouse(
        name="NABARD Accredited Farmer Producer Warehouse",
        code="WDRA-UP-LKO-07",
        location="Bakshi Ka Talab, Lucknow",
        distance_km=19.0,
        capacity_mt=5000,
        available_mt=1850,
        contact="+91-522-298711",
    ),
]


def _normalize_crop(crop_name: str) -> str:
    return crop_name.lower().strip()


def get_village_latest_zone(db: Session, village_id: str) -> str:
    """Returns the latest zone color for a village, defaulting to green."""
    latest_status = (
        db.query(ZoneStatus)
        .filter(ZoneStatus.jurisdiction_id == village_id)
        .order_by(ZoneStatus.computed_at.desc())
        .first()
    )
    return latest_status.color.lower() if latest_status else "green"


def evaluate_post_harvest_advice(
    db: Session,
    village_id: str,
    farmer_id: Optional[str] = None,
) -> FarmerPostHarvestResponse:
    """
    Evaluates post-harvest storage and e-NWR pledge options for a village or specific farmer.
    """
    village = (
        db.query(Jurisdiction)
        .filter(
            Jurisdiction.id == village_id, Jurisdiction.jurisdiction_type == "village"
        )
        .first()
    )
    if not village:
        return FarmerPostHarvestResponse(
            village_id=village_id,
            village_name="Unknown",
            zone_color="green",
            advisories=[],
        )

    zone_color = get_village_latest_zone(db, village_id)

    # Query crop entries for the farmer or village
    crop_query = (
        db.query(CropEntry)
        .join(Farmer, CropEntry.farmer_id == Farmer.id)
        .filter(Farmer.jurisdiction_id == village_id)
    )

    if farmer_id:
        crop_query = crop_query.filter(Farmer.id == farmer_id)

    crop_entries = crop_query.all()
    advisories: List[StorageAdvice] = []

    # Find any deficit red zones nearby for market routing
    deficit_villages = (
        db.query(Jurisdiction.name)
        .join(ZoneStatus, ZoneStatus.jurisdiction_id == Jurisdiction.id)
        .filter(ZoneStatus.color == "red")
        .limit(3)
        .all()
    )
    deficit_names = ", ".join([d[0] for d in deficit_villages])
    deficit_route = (
        f"Deficit Demand Route: High shortfall identified in nearby outbreak zones ({deficit_names}). "
        "Hold in WDRA warehouse for 60-90 days for peak premium delivery to deficit markets."
        if deficit_villages
        else "Standard Mandi Integration: Sell on e-NAM platform during post-harvest price rebound."
    )

    for entry in crop_entries:
        norm_crop = _normalize_crop(entry.crop_name)
        is_pulse = norm_crop in PULSE_CROPS
        is_oilseed = norm_crop in OILSEED_CROPS

        if not (is_pulse or is_oilseed):
            continue

        crop_category = "pulse" if is_pulse else "oilseed"
        price_info = COMMODITY_PRICES.get(
            norm_crop,
            {
                "current_mandi": 5500.0,
                "peak_price": 6500.0,
                "dip_pct": 18.0,
                "holding_days": 60,
            },
        )

        if zone_color == "green":
            # High quality harvest without disease contamination -> WDRA storage recommended
            advice = StorageAdvice(
                crop_name=entry.crop_name,
                crop_category=crop_category,
                zone_color="green",
                recommendation="STORE_WDRA",
                post_harvest_dip_pct=price_info["dip_pct"],
                current_mandi_price_inr_qtl=price_info["current_mandi"],
                expected_peak_price_inr_qtl=price_info["peak_price"],
                holding_period_days=price_info["holding_days"],
                enwr_pledge_loan_eligible=True,
                max_pledge_loan_pct=70.0,
                effective_interest_rate_pct=4.0,
                rationale=(
                    f"Healthy {entry.crop_name} harvest in Green Zone '{village.name}'. "
                    f"Avoid the ~{price_info['dip_pct']}% post-harvest mandi price slump. "
                    "Deposit produce in a WDRA-accredited warehouse to generate an Electronic Negotiable "
                    "Warehouse Receipt (e-NWR) and avail a 70% pledge loan at subsidized 4% p.a. interest."
                ),
                nearest_warehouses=REGIONAL_WDRA_WAREHOUSES,
                deficit_market_routing=deficit_route,
            )
        else:
            # Red/Orange zone: Disease contamination risk
            advice = StorageAdvice(
                crop_name=entry.crop_name,
                crop_category=crop_category,
                zone_color=zone_color,
                recommendation="STANDARD_SELL",
                post_harvest_dip_pct=price_info["dip_pct"],
                current_mandi_price_inr_qtl=price_info["current_mandi"],
                expected_peak_price_inr_qtl=price_info["current_mandi"],
                holding_period_days=0,
                enwr_pledge_loan_eligible=False,
                max_pledge_loan_pct=0.0,
                effective_interest_rate_pct=0.0,
                rationale=(
                    f"Village is in {zone_color.upper()} Zone. Long-term warehouse storage is not recommended "
                    "for seeds/pulses exposed to active regional pathogen vectors. Sell promptly in local mandi "
                    "or file for PMFBY crop loss compensation if yield is compromised."
                ),
                nearest_warehouses=[],
                deficit_market_routing=None,
            )
        advisories.append(advice)

    return FarmerPostHarvestResponse(
        farmer_id=farmer_id,
        village_id=village_id,
        village_name=village.name,
        zone_color=zone_color,
        advisories=advisories,
    )
