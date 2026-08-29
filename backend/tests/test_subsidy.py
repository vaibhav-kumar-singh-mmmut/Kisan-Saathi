"""
Phase 11 — TDD tests for PMFBY Subsidy Flag + Drone Booking.
All 5 spec gates:
  1. Flag rejected when report count < minimum
  2. Flag allowed once threshold met; 72-hr PMFBY window correct
  3. Claim packet includes geotagged images, disease history, acreage, farmer IDs
  4. Audit trail records flagged-by, evidence, approver, timestamp — immutable once approved
  5. Drone booking creates record routed to correct CHC by proximity
"""

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.jurisdiction import Jurisdiction
from app.models.official import Official
from app.models.farmer import Farmer
from app.models.disease_lookup import DiseaseLookup
from app.models.disease_report import DiseaseReport
from app.models.subsidy_flag import SubsidyFlag
from app.models.drone_booking import DroneBooking
from app.services.subsidy_service import (
    can_flag_subsidy,
    create_subsidy_flag,
    approve_subsidy_flag,
    create_drone_booking,
    PMFBY_MIN_REPORTS,
    PMFBY_MIN_UNIQUE_FARMERS,
    PMFBY_WINDOW_HOURS,
)

_TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(_TEST_ENGINE)

    with Session(_TEST_ENGINE) as session:
        # Village with GPS coordinates
        v1 = Jurisdiction(
            id="VIL-1",
            name="Rampur Khurd",
            jurisdiction_type="village",
            lat=26.755,
            lon=83.373,
        )
        # Village too far from any CHC (tests fallback)
        v2 = Jurisdiction(
            id="VIL-2",
            name="Remote Village",
            jurisdiction_type="village",
            lat=25.0,
            lon=80.0,
        )
        officer = Official(
            id="OFF-1",
            name="Rajiv Sharma",
            phone="9000000001",
            role="agri_officer",
            wing="development",
            jurisdiction_type="village",
            jurisdiction_id="VIL-1",
        )
        bdo = Official(
            id="BDO-1",
            name="DM Gupta",
            phone="9000000002",
            role="dm",
            wing="revenue",
            jurisdiction_type="block",
            jurisdiction_id="VIL-1",
        )
        f1 = Farmer(id="F-1", name="Ram Lal", phone="8000000001", jurisdiction_id="VIL-1")
        f2 = Farmer(id="F-2", name="Shyam Das", phone="8000000002", jurisdiction_id="VIL-1")
        f3 = Farmer(id="F-3", name="Mohan Singh", phone="8000000003", jurisdiction_id="VIL-1")
        f4 = Farmer(id="F-4", name="Geeta Devi", phone="8000000004", jurisdiction_id="VIL-1")
        dl = DiseaseLookup(
            id="potato_early_blight",
            name="Early Blight",
            crops=["Potato"],
            severity="high",
            pathogen_type="fungal",
            spread_radius_km=5.0,
        )
        session.add_all([v1, v2, officer, bdo, f1, f2, f3, f4, dl])
        session.commit()

    yield
    Base.metadata.drop_all(_TEST_ENGINE)


@pytest.fixture
def session():
    with Session(_TEST_ENGINE) as s:
        yield s


# ─── Helper ───────────────────────────────────────────────────────────────────

def _add_reports(session, count: int, farmer_cycle: list[str], disease_id="potato_early_blight", jurisdiction_id="VIL-1"):
    """Add `count` confirmed disease reports cycling across given farmer IDs."""
    for i in range(count):
        session.add(DiseaseReport(
            id=f"RPT-{disease_id}-{jurisdiction_id}-{i}",
            farmer_id=farmer_cycle[i % len(farmer_cycle)],
            jurisdiction_id=jurisdiction_id,
            disease_id=disease_id,
            status="confirmed",
            image_url=f"https://storage.example.com/scan_{i}.jpg",
            gps_lat=26.755,
            gps_lon=83.373,
            confidence_score=0.87,
        ))
    session.commit()


# ─── Test 1: Flag rejected when report count < minimum ────────────────────────

def test_flag_rejected_below_minimum_reports(session):
    """Gate 1: Flag is rejected when confirmed reports < PMFBY_MIN_REPORTS."""
    farmers = ["F-1", "F-2", "F-3"]
    _add_reports(session, count=PMFBY_MIN_REPORTS - 1, farmer_cycle=farmers,
                 disease_id="potato_early_blight", jurisdiction_id="VIL-2")

    allowed, reason = can_flag_subsidy(session, "VIL-2", "potato_early_blight")
    assert allowed is False
    assert "Minimum required" in reason or "confirmed report" in reason


# ─── Test 2: Flag allowed once threshold met; 72-hr PMFBY window correct ──────

def test_flag_allowed_at_threshold_and_window_correct(session):
    """Gate 2: Flag is raised once threshold is met and 72-hr window is correct."""
    farmers = ["F-1", "F-2", "F-3"]
    _add_reports(session, count=PMFBY_MIN_REPORTS, farmer_cycle=farmers,
                 disease_id="potato_early_blight", jurisdiction_id="VIL-1")

    before = datetime.now(timezone.utc)
    flag, message = create_subsidy_flag(
        session,
        officer_id="OFF-1",
        jurisdiction_id="VIL-1",
        disease_id="potato_early_blight",
        acreage_ha=3.5,
    )
    after = datetime.now(timezone.utc)

    assert flag is not None, f"Flag creation failed: {message}"
    assert flag.status == "pending"

    # 72-hr PMFBY window
    expected_min = before + timedelta(hours=PMFBY_WINDOW_HOURS)
    expected_max = after + timedelta(hours=PMFBY_WINDOW_HOURS)
    assert flag.pmfby_window_expires_at is not None
    # SQLite returns naive datetimes; strip tzinfo for comparison
    window = flag.pmfby_window_expires_at
    if window.tzinfo is not None:
        window = window.replace(tzinfo=None)
    before_naive = before.replace(tzinfo=None)
    after_naive = after.replace(tzinfo=None)
    expected_min = before_naive + timedelta(hours=PMFBY_WINDOW_HOURS)
    expected_max = after_naive + timedelta(hours=PMFBY_WINDOW_HOURS, seconds=5)
    assert expected_min <= window <= expected_max, (
        f"PMFBY window {window} not in expected range [{expected_min}, {expected_max}]"
    )


# ─── Test 3: Claim packet completeness ────────────────────────────────────────

def test_claim_packet_completeness(session):
    """Gate 3: Claim packet includes geotagged images, disease history, acreage, farmer IDs."""
    # Re-fetch the flag created in test 2
    flag = (
        session.query(SubsidyFlag)
        .filter_by(jurisdiction_id="VIL-1", disease_id="potato_early_blight")
        .order_by(SubsidyFlag.created_at.desc())
        .first()
    )
    assert flag is not None

    # Acreage
    assert flag.acreage_ha == 3.5

    # Farmer IDs — must include at least PMFBY_MIN_UNIQUE_FARMERS distinct farmers
    assert flag.farmer_ids is not None
    assert len(flag.farmer_ids) >= PMFBY_MIN_UNIQUE_FARMERS

    # Report IDs — disease history
    assert flag.report_ids is not None
    assert len(flag.report_ids) >= PMFBY_MIN_REPORTS

    # Geotagged images
    assert flag.geotagged_image_urls is not None
    assert len(flag.geotagged_image_urls) > 0
    assert all(url.startswith("http") for url in flag.geotagged_image_urls)

    # Officer who flagged it
    assert flag.flagged_by == "OFF-1"


# ─── Test 4: Audit trail immutability ─────────────────────────────────────────

def test_audit_trail_immutable_after_approval(session):
    """Gate 4: Audit trail records flagged-by, evidence, approver, timestamp.
    Second approval attempt is rejected (immutable once approved).
    """
    flag = (
        session.query(SubsidyFlag)
        .filter_by(jurisdiction_id="VIL-1", disease_id="potato_early_blight")
        .order_by(SubsidyFlag.created_at.desc())
        .first()
    )
    assert flag is not None

    # Initial audit trail has the 'flagged' entry
    assert flag.audit_trail is not None
    assert any(entry["action"] == "flagged" for entry in flag.audit_trail)

    # BDO approves
    approved_flag, msg = approve_subsidy_flag(session, flag.id, "BDO-1")
    assert approved_flag is not None, f"Approval failed: {msg}"
    assert approved_flag.status == "approved"
    assert approved_flag.approved_by == "BDO-1"
    assert approved_flag.approved_at is not None

    # Audit trail now contains both 'flagged' and 'approved' entries
    actions = [e["action"] for e in approved_flag.audit_trail]
    assert "flagged" in actions
    assert "approved" in actions

    # Second approval attempt must be rejected — immutable
    second_attempt, err_msg = approve_subsidy_flag(session, flag.id, "BDO-1")
    assert second_attempt is None
    assert "immutable" in err_msg.lower() or "already" in err_msg.lower()


# ─── Test 5: Drone booking routed to correct CHC by proximity ─────────────────

def test_drone_booking_routes_to_nearest_chc(session):
    """Gate 5: Drone booking is created and routed to the nearest CHC by GPS proximity."""
    booking = create_drone_booking(
        session,
        farmer_id="F-1",
        jurisdiction_id="VIL-1",
        disease_report_id=None,
        acreage_ha=2.0,
        crop_name="Potato",
        notes="Early blight detected on plot 3",
    )

    assert booking is not None
    assert booking.farmer_id == "F-1"
    assert booking.status == "pending"

    # CHC must be assigned
    assert booking.chc_id is not None
    assert booking.chc_name is not None
    assert booking.chc_lat is not None
    assert booking.chc_lon is not None

    # VIL-1 is at lat=26.755 lon=83.373 — nearest CHC should be CHC-001 (Gorakhpur)
    assert booking.chc_id == "CHC-001"
    assert "Gorakhpur" in booking.chc_name
    assert booking.chc_distance_km is not None
    assert booking.chc_distance_km < 10.0  # Must be very close
