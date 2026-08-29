import pytest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.jurisdiction import Jurisdiction
from app.models.disease_report import DiseaseReport
from app.models.disease_lookup import DiseaseLookup
from app.models.weather_daily import WeatherDaily
from app.models.zone_status import ZoneStatus
from app.services.zone_scoring_service import calculate_zone_scores

_TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(_TEST_ENGINE)
    with Session(_TEST_ENGINE) as session:
        # V1: Rampur Khurd (Red)
        v1 = Jurisdiction(
            id="V1",
            name="Rampur Khurd",
            jurisdiction_type="village",
            lat=26.9,
            lon=80.9,
        )
        # V2: Sonbarsa (Red)
        v2 = Jurisdiction(
            id="V2", name="Sonbarsa", jurisdiction_type="village", lat=26.91, lon=80.91
        )
        # V5: Gajraula (Incoming Risk - within spread radius of V1)
        v5 = Jurisdiction(
            id="V5", name="Gajraula", jurisdiction_type="village", lat=26.95, lon=80.95
        )
        # V4: Mahmoodpur (Green)
        v4 = Jurisdiction(
            id="V4", name="Mahmoodpur", jurisdiction_type="village", lat=27.1, lon=81.1
        )

        dl_rust = DiseaseLookup(
            id="wheat_yellow_rust",
            name="Yellow Rust",
            crops=["Wheat"],
            severity="high",
            pathogen_type="fungal",
            spread_radius_km=10.0,
            weather_triggers={"humidity_min": 75},
        )
        dl_pest = DiseaseLookup(
            id="mustard_pests_diseases",
            name="Pests",
            crops=["Mustard"],
            severity="low",
            pathogen_type="pest",
            spread_radius_km=0.0,
        )

        session.add_all([v1, v2, v5, v4, dl_rust, dl_pest])
        session.commit()

    yield
    Base.metadata.drop_all(_TEST_ENGINE)


@pytest.fixture
def session():
    with Session(_TEST_ENGINE) as session:
        yield session


def test_score_red_village(session):
    # Setup reports for V1 (8 reports, high severity = RED)
    base_date = datetime.now(timezone.utc)
    for i in range(8):
        session.add(
            DiseaseReport(
                id=f"r-v1-{i}",
                farmer_id="test",
                jurisdiction_id="V1",
                disease_id="wheat_yellow_rust",
                status="confirmed",
                reported_at=base_date,
                confirmed_at=base_date,
            )
        )
    session.add(
        WeatherDaily(
            id="w-v1", jurisdiction_id="V1", date=base_date.date(), humidity_pct=80
        )
    )  # Weather trigger match
    session.commit()

    # Mock spatial query to return empty for simplicity in this test
    with patch(
        "app.services.zone_scoring_service._get_nearby_jurisdictions", return_value=[]
    ):
        calculate_zone_scores(session)

    zone = (
        session.query(ZoneStatus)
        .filter_by(jurisdiction_id="V1")
        .order_by(ZoneStatus.computed_at.desc())
        .first()
    )
    assert zone is not None
    assert zone.color == "red"
    assert zone.alert_fired is True
    assert zone.weather_trigger_fired is True


def test_alert_fatigue_prevention(session):
    # Score again without changing reports. Color remains Red. alert_fired should be False.
    with patch(
        "app.services.zone_scoring_service._get_nearby_jurisdictions", return_value=[]
    ):
        calculate_zone_scores(session)

    zones = (
        session.query(ZoneStatus)
        .filter_by(jurisdiction_id="V1")
        .order_by(ZoneStatus.computed_at.desc())
        .limit(2)
        .all()
    )
    assert len(zones) >= 2
    latest_zone = zones[0]
    assert latest_zone.color == "red"
    assert latest_zone.alert_fired is False  # Fatigue prevention!


def test_green_village(session):
    # Setup reports for V4 (2 reports, low severity = GREEN)
    base_date = datetime.now(timezone.utc)
    for i in range(2):
        session.add(
            DiseaseReport(
                id=f"r-v4-{i}",
                farmer_id="test",
                jurisdiction_id="V4",
                disease_id="mustard_pests_diseases",
                status="confirmed",
                reported_at=base_date,
                confirmed_at=base_date,
            )
        )
    session.commit()

    with patch(
        "app.services.zone_scoring_service._get_nearby_jurisdictions", return_value=[]
    ):
        calculate_zone_scores(session)

    zone = (
        session.query(ZoneStatus)
        .filter_by(jurisdiction_id="V4")
        .order_by(ZoneStatus.computed_at.desc())
        .first()
    )
    assert zone is not None
    assert zone.color == "green"


def test_incoming_risk_village(session):
    # V5 has no reports. But it's near V1 (which is Red).
    # We mock the spatial query to pretend V1 is within 10km of V5.
    with patch(
        "app.services.zone_scoring_service._get_nearby_jurisdictions",
        return_value=["V5"],
    ):
        calculate_zone_scores(session)

    zone = (
        session.query(ZoneStatus)
        .filter_by(jurisdiction_id="V5")
        .order_by(ZoneStatus.computed_at.desc())
        .first()
    )
    assert zone is not None
    assert zone.color == "incoming_risk"
    assert zone.alert_fired is True  # Should alert for new incoming risk
