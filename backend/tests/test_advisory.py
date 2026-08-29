import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.disease_lookup import DiseaseLookup
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
        session.add_all(
            [
                DiseaseLookup(
                    id="wheat_yellow_rust",
                    name="Yellow Rust",
                    crops=["Wheat"],
                    severity="high",
                    pathogen_type="fungal",
                    ipm_steps=[
                        "Use resistant/tolerant wheat varieties where available",
                        "Avoid excess nitrogenous fertilizer",
                        "Spray recommended fungicide (e.g. Propiconazole) at first sign",
                    ],
                ),
                DiseaseLookup(
                    id="rice_tungro",
                    name="Rice Tungro",
                    crops=["Rice"],
                    severity="high",
                    pathogen_type="viral",
                    ipm_steps=["This shouldn't be returned"],
                ),
                DiseaseLookup(
                    id="pomegranate_nematode_wilt",
                    name="Pomegranate Nematode Wilt",
                    crops=["Pomegranate"],
                    severity="high",
                    pathogen_type="nematode",
                    ipm_steps=["Check soil"],
                ),
            ]
        )
        session.commit()
    yield
    Base.metadata.drop_all(_TEST_ENGINE)


@pytest.fixture
def app_with_test_db():
    from app.core.database import get_db

    def override_get_db():
        with Session(_TEST_ENGINE) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_advisory_low_confidence(app_with_test_db):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_test_db), base_url="http://test"
    ) as ac:
        response = await ac.get(
            "/api/v1/advisory",
            params={"disease_id": "wheat_yellow_rust", "confidence": 0.65},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "expert_queue"
    assert "no advisory generated" in data["message"].lower()
    assert data.get("advisory_steps") is None


@pytest.mark.asyncio
async def test_advisory_fungal(app_with_test_db):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_test_db), base_url="http://test"
    ) as ac:
        response = await ac.get(
            "/api/v1/advisory",
            params={"disease_id": "wheat_yellow_rust", "confidence": 0.85},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "treatable"
    assert data["pathogen_type"] == "fungal"
    assert data["disease_name"] == "Yellow Rust"
    assert "advisory_steps" in data
    assert len(data["advisory_steps"]) > 0
    assert "Propiconazole" in str(data["advisory_steps"])
    assert data.get("dosage") is not None
    assert data.get("pre_harvest_interval") is not None


@pytest.mark.asyncio
async def test_advisory_viral(app_with_test_db):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_test_db), base_url="http://test"
    ) as ac:
        response = await ac.get(
            "/api/v1/advisory", params={"disease_id": "rice_tungro", "confidence": 0.90}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "viral_isolate"
    assert data["pathogen_type"] == "viral"
    assert "advisory_steps" in data
    steps_str = str(data["advisory_steps"]).lower()
    assert "isolate" in steps_str
    assert "resistant variety" in steps_str
    # MUST NEVER return a cure/treatment step from DB
    assert "spray" not in steps_str
    assert "fungicide" not in steps_str


@pytest.mark.asyncio
async def test_advisory_nematode(app_with_test_db):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_test_db), base_url="http://test"
    ) as ac:
        response = await ac.get(
            "/api/v1/advisory",
            params={"disease_id": "pomegranate_nematode_wilt", "confidence": 0.95},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "nematode_treatment"
    assert data["pathogen_type"] == "nematode"
    assert "advisory_steps" in data
    steps_str = str(data["advisory_steps"]).lower()
    assert "soil treatment" in steps_str
    assert "crop rotation" in steps_str


@pytest.mark.asyncio
async def test_advisory_not_found(app_with_test_db):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_test_db), base_url="http://test"
    ) as ac:
        response = await ac.get(
            "/api/v1/advisory",
            params={"disease_id": "unknown_disease", "confidence": 0.90},
        )

    assert response.status_code == 404
