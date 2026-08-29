import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone

from app.core.database import Base
from app.models.disease_lookup import DiseaseLookup
from app.models.disease_report import DiseaseReport
from app.models.retraining_data import RetrainingData
from app.models.jurisdiction import Jurisdiction
from app.models.farmer import Farmer
from app.models.official import Official
from app.utils.jurisdiction_scope import get_current_user
from main import app

_TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(_TEST_ENGINE)
    with Session(_TEST_ENGINE) as session:
        # Create minimal required records
        j = Jurisdiction(id="vil-01", name="Vil 01", jurisdiction_type="village")
        f = Farmer(
            id="far-01", name="Farmer", phone="+910000000000", jurisdiction_id="vil-01"
        )
        o = Official(
            id="off-01",
            name="Expert",
            phone="+910000000001",
            role="KVK Scientist",
            wing="agriculture",
            jurisdiction_type="district",
            jurisdiction_id="dist-01",
        )
        dl1 = DiseaseLookup(
            id="wheat_rust",
            name="Rust",
            crops=["Wheat"],
            severity="high",
            pathogen_type="fungal",
        )
        dl2 = DiseaseLookup(
            id="wheat_blight",
            name="Blight",
            crops=["Wheat"],
            severity="high",
            pathogen_type="fungal",
        )

        session.add_all([j, f, o, dl1, dl2])
        session.commit()

        # Add a pending disease report
        dr = DiseaseReport(
            id="report-1",
            farmer_id="far-01",
            disease_id="wheat_rust",
            confidence_score=0.65,
            status="pending",
            reported_at=datetime.now(timezone.utc),
        )
        session.add(dr)
        session.commit()
    yield
    Base.metadata.drop_all(_TEST_ENGINE)


@pytest.fixture
def app_with_test_db():
    from app.core.database import get_db

    def override_get_db():
        with Session(_TEST_ENGINE) as session:
            yield session

    def override_get_current_user():
        return {"sub": "off-01", "role": "KVK Scientist"}

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield app
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_expert_queue(app_with_test_db):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_test_db), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/expert-queue")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "report-1"
    assert data[0]["status"] == "pending"


@pytest.mark.asyncio
async def test_validate_expert_queue(app_with_test_db):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_test_db), base_url="http://test"
    ) as ac:
        response = await ac.post(
            "/api/v1/expert-queue/report-1/validate",
            json={
                "corrected_disease_id": "wheat_blight",
                "notes": "Looks more like blight.",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "reviewed"

    # Verify DB state directly
    with Session(_TEST_ENGINE) as session:
        report = session.query(DiseaseReport).filter_by(id="report-1").first()
        assert report.status == "reviewed"
        # CRITICAL: Original disease_id must not change
        assert report.disease_id == "wheat_rust"
        assert report.expert_id == "off-01"
        assert report.confirmed_at is not None

        retraining = (
            session.query(RetrainingData)
            .filter_by(disease_report_id="report-1")
            .first()
        )
        assert retraining is not None
        assert retraining.original_disease_id == "wheat_rust"
        assert retraining.corrected_disease_id == "wheat_blight"
        assert retraining.correction_notes == "Looks more like blight."
        assert retraining.corrected_by == "off-01"
