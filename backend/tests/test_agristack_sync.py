"""
Phase 12 — TDD tests for AgriStack UFSI Sync, Lekhpal/Kanungo Discrepancy Reporting,
and WDRA Post-Harvest Storage & e-NWR Loan Suggestions.
"""

import pytest
from datetime import datetime, timezone, timedelta, date
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi import HTTPException

from app.core.database import Base
from app.models.jurisdiction import Jurisdiction
from app.models.official import Official
from app.models.farmer import Farmer
from app.models.crop_entry import CropEntry
from app.models.zone_status import ZoneStatus
from app.models.crop_discrepancy import CropDiscrepancy
from app.schemas.agristack import CropDiscrepancyCreate
from app.services.agristack_service import (
    sync_agristack_registry,
    get_crop_catalogue,
    create_crop_discrepancy,
    list_crop_discrepancies,
)
from app.services.post_harvest_service import evaluate_post_harvest_advice

_TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(_TEST_ENGINE)

    with Session(_TEST_ENGINE) as session:
        # District & Tehsil
        dist = Jurisdiction(
            id="D-1",
            name="Lucknow",
            jurisdiction_type="district",
        )
        tehsil = Jurisdiction(
            id="T-1",
            name="Sarojini Nagar",
            jurisdiction_type="tehsil",
            parent_id="D-1",
        )
        # Green Village with Pulse
        v_green = Jurisdiction(
            id="V-GREEN",
            name="Naugaon",
            jurisdiction_type="village",
            parent_id="T-1",
            lat=26.80,
            lon=80.90,
        )
        # Red Village with Wheat
        v_red = Jurisdiction(
            id="V-RED",
            name="Rampur Khurd",
            jurisdiction_type="village",
            parent_id="T-1",
            lat=26.72,
            lon=80.87,
        )
        session.add_all([dist, tehsil, v_green, v_red])
        session.flush()

        # Zone Status
        zs_green = ZoneStatus(
            jurisdiction_id="V-GREEN",
            color="green",
            score=12.5,
            report_count=1,
            computed_at=datetime.now(timezone.utc),
        )
        zs_red = ZoneStatus(
            jurisdiction_id="V-RED",
            color="red",
            score=82.0,
            report_count=8,
            computed_at=datetime.now(timezone.utc),
        )
        session.add_all([zs_green, zs_red])

        # Revenue Officials
        lekhpal = Official(
            id="OFF-LEKHPAL",
            name="Sanjay Yadav",
            phone="+919001000004",
            role="Lekhpal/Patwari",
            wing="revenue",
            jurisdiction_type="village",
            jurisdiction_id="V-GREEN",
        )
        dm = Official(
            id="OFF-DM",
            name="Arvind Kumar Singh",
            phone="+919001000001",
            role="DM",
            wing="revenue",
            jurisdiction_type="district",
            jurisdiction_id="D-1",
        )
        kvk_expert = Official(
            id="OFF-KVK",
            name="Dr. Ashok Tiwari",
            phone="+919001000007",
            role="KVK Expert",
            wing="service",
            jurisdiction_type="district",
            jurisdiction_id="D-1",
        )
        session.add_all([lekhpal, dm, kvk_expert])
        session.commit()

    yield
    Base.metadata.drop_all(_TEST_ENGINE)


@pytest.fixture
def db():
    with Session(_TEST_ENGINE) as session:
        yield session


def test_agristack_sync_populates_crop_entries(db: Session):
    """Gate 1: AgriStack sync fetches parcels and writes crop_entries with synced_from_agristack=True."""
    res = sync_agristack_registry(
        db=db,
        allowed_village_ids=["V-GREEN", "V-RED"],
        season="rabi",
    )
    assert res.status == "success"
    assert res.synced_records_count > 0
    assert res.village_count == 2

    # Check synced crop entries
    entries = db.query(CropEntry).filter(CropEntry.synced_from_agristack.is_(True)).all()
    assert len(entries) >= 3

    crops = {e.crop_name for e in entries}
    assert "Chickpea" in crops or "Wheat" in crops


def test_get_crop_catalogue(db: Session):
    """Gate 2: Crop catalogue returns enriched farmer + village info and supports filtering."""
    catalogue = get_crop_catalogue(
        db=db,
        allowed_village_ids=["V-GREEN", "V-RED"],
        synced_only=True,
    )
    assert len(catalogue) > 0
    item = catalogue[0]
    assert item.synced_from_agristack is True
    assert item.village_name in ["Naugaon", "Rampur Khurd"]
    assert item.farmer_name is not None


def test_lekhpal_create_crop_discrepancy_authorized(db: Session):
    """Gate 3: Lekhpal (Revenue Official) can successfully file a statutory crop discrepancy."""
    user_context = {
        "user_id": "OFF-LEKHPAL",
        "name": "Sanjay Yadav",
        "role": "Lekhpal/Patwari",
        "jurisdiction_type": "revenue",
        "jurisdiction_id": "V-GREEN",
    }

    discrepancy_in = CropDiscrepancyCreate(
        jurisdiction_id="V-GREEN",
        farmer_name="Raghunath Maurya",
        survey_number="KH-14/6",
        reported_crop="Chickpea",
        actual_crop_observed="Mustard",
        reported_acreage_ha=3.2,
        actual_acreage_ha=2.8,
        discrepancy_type="crop_mismatch",
        notes="Farmer sowed Mustard instead of registered Chickpea crop.",
    )

    created = create_crop_discrepancy(
        db=db,
        discrepancy_data=discrepancy_in,
        current_user=user_context,
    )

    assert created.id is not None
    assert created.reported_crop == "Chickpea"
    assert created.actual_crop_observed == "Mustard"
    assert created.status == "pending"
    assert created.official_role == "Lekhpal/Patwari"

    # Verify listing
    items = list_crop_discrepancies(db=db, allowed_village_ids=["V-GREEN"])
    assert len(items) >= 1
    assert any(i.survey_number == "KH-14/6" for i in items)


def test_non_revenue_create_crop_discrepancy_forbidden(db: Session):
    """Gate 4: Non-revenue official (e.g. KVK Expert) is rejected with HTTP 403."""
    user_context = {
        "user_id": "OFF-KVK",
        "name": "Dr. Ashok Tiwari",
        "role": "KVK Expert",
        "jurisdiction_type": "service",
        "jurisdiction_id": "D-1",
    }

    discrepancy_in = CropDiscrepancyCreate(
        jurisdiction_id="V-GREEN",
        reported_crop="Wheat",
        actual_crop_observed="Barley",
    )

    with pytest.raises(HTTPException) as excinfo:
        create_crop_discrepancy(
            db=db,
            discrepancy_data=discrepancy_in,
            current_user=user_context,
        )

    assert excinfo.value.status_code == 403
    assert "not authorized" in excinfo.value.detail.lower()


def test_wdra_storage_suggestion_green_zone_pulse(db: Session):
    """Gate 5: Green Zone Pulse farmer receives WDRA storage recommendation & e-NWR pledge loan advice."""
    advice_response = evaluate_post_harvest_advice(
        db=db,
        village_id="V-GREEN",
    )
    assert advice_response.village_name == "Naugaon"
    assert advice_response.zone_color == "green"
    assert len(advice_response.advisories) > 0

    pulse_advisories = [a for a in advice_response.advisories if a.crop_category == "pulse"]
    assert len(pulse_advisories) > 0
    first_pulse = pulse_advisories[0]

    assert first_pulse.recommendation == "STORE_WDRA"
    assert first_pulse.enwr_pledge_loan_eligible is True
    assert first_pulse.effective_interest_rate_pct == 4.0
    assert first_pulse.max_pledge_loan_pct == 70.0
    assert first_pulse.post_harvest_dip_pct > 0
    assert len(first_pulse.nearest_warehouses) > 0
    assert "Deficit Demand Route" in (first_pulse.deficit_market_routing or "")


def test_wdra_storage_suggestion_red_zone_suppressed(db: Session):
    """Gate 6: Red Zone village suppresses long-term WDRA seed storage due to pathogen risk."""
    # Ensure there is a pulse/oilseed entry in Red village for testing
    farmer_red = Farmer(
        name="Red Zone Pulse Grower",
        phone="+919876599999",
        jurisdiction_id="V-RED",
        agristack_id="AGRI-RED-9999",
    )
    db.add(farmer_red)
    db.flush()
    crop_red = CropEntry(
        farmer_id=farmer_red.id,
        crop_name="Chickpea",
        acreage_ha=2.0,
        growth_stage="maturity",
        season="rabi",
    )
    db.add(crop_red)
    db.commit()

    advice_response = evaluate_post_harvest_advice(
        db=db,
        village_id="V-RED",
    )
    assert advice_response.zone_color == "red"
    assert len(advice_response.advisories) > 0
    adv = advice_response.advisories[0]
    assert adv.recommendation == "STANDARD_SELL"
    assert adv.enwr_pledge_loan_eligible is False
    assert len(adv.nearest_warehouses) == 0
