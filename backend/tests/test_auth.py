"""
Phase 2 auth tests — written FIRST per AI_AGENT_BUILD_PROMPT.md gate requirement.

Tests:
  1. OTP request for known official phone → 200, otp_sent=True
  2. OTP request for unknown phone → 404
  3. OTP verify with wrong code → 401
  4. OTP verify with correct code → 200, access_token present
  5. GET /auth/me with no token → 401
  6. GET /auth/me with valid token → 200, correct role/jurisdiction
  7. GET /dashboard/villages as Tehsildar → only tehsil-level villages
  8. GET /dashboard/villages as DM → all district villages

Uses an in-memory SQLite DB seeded with minimal data matching the Phase 1 scenarios.
No real network calls. OTP store is the module-level dict (reset between tests).
"""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models import (
    Jurisdiction,
    Official,
    Farmer,
)

from sqlalchemy.pool import StaticPool

# ── Shared test engine (module-scoped so tables are created once) ─────────────
# StaticPool: all connections reuse the SAME underlying connection,
# so the tables created in setup_test_db are visible in every Session.
_TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Create tables and seed minimal data once for the whole module."""
    Base.metadata.create_all(_TEST_ENGINE)

    with Session(_TEST_ENGINE) as session:
        # Jurisdiction tree: district -> tehsil -> block -> villages
        district = Jurisdiction(
            id="dist-001",
            name="Lucknow",
            jurisdiction_type="district",
            parent_id=None,
            state="Uttar Pradesh",
            district_name="Lucknow",
        )
        tehsil = Jurisdiction(
            id="teh-001",
            name="Sarojini Nagar",
            jurisdiction_type="tehsil",
            parent_id="dist-001",
            state="Uttar Pradesh",
            district_name="Lucknow",
        )
        block = Jurisdiction(
            id="blk-001",
            name="Mohanlalganj",
            jurisdiction_type="block",
            parent_id="teh-001",
            state="Uttar Pradesh",
            district_name="Lucknow",
        )
        village_a = Jurisdiction(
            id="vil-001",
            name="Rampur Khurd",
            jurisdiction_type="village",
            parent_id="blk-001",
            state="Uttar Pradesh",
            district_name="Lucknow",
        )
        village_b = Jurisdiction(
            id="vil-002",
            name="Sonbarsa",
            jurisdiction_type="village",
            parent_id="blk-001",
            state="Uttar Pradesh",
            district_name="Lucknow",
        )
        session.add_all([district, tehsil, block, village_a, village_b])

        # Officials
        dm = Official(
            id="off-001",
            name="Arvind Kumar Singh",
            phone="+919001000001",
            role="DM",
            wing="revenue",
            jurisdiction_type="district",
            jurisdiction_id="dist-001",
        )
        tehsildar = Official(
            id="off-002",
            name="Priya Sharma",
            phone="+919001000002",
            role="Tehsildar",
            wing="revenue",
            jurisdiction_type="tehsil",
            jurisdiction_id="teh-001",
        )
        session.add_all([dm, tehsildar])

        # Farmer
        farmer = Farmer(
            id="far-001",
            name="Farmer V1-1",
            phone="+9190100001",
            jurisdiction_id="vil-001",
        )
        session.add(farmer)
        session.commit()

    yield

    Base.metadata.drop_all(_TEST_ENGINE)


@pytest.fixture(autouse=True)
def clear_otp_store():
    """Reset the in-memory OTP store between tests to prevent leakage."""
    from app.utils import otp as otp_module

    otp_module._otp_store.clear()
    yield
    otp_module._otp_store.clear()


@pytest.fixture
def app_with_test_db():
    """Override the get_db dependency with test DB session."""
    from main import app
    from app.core.database import get_db
    from sqlalchemy.orm import Session

    def override_get_db():
        with Session(_TEST_ENGINE) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


# ── Helper: get a valid JWT for a seeded phone ────────────────────────────────


async def _get_token(client: AsyncClient, phone: str) -> str:
    """Request OTP, extract dev_code, verify it, return access_token."""
    r1 = await client.post("/api/v1/auth/otp/request", json={"phone": phone})
    assert r1.status_code == 200, f"OTP request failed: {r1.text}"
    code = r1.json()["dev_code"]
    r2 = await client.post(
        "/api/v1/auth/otp/verify", json={"phone": phone, "code": code}
    )
    assert r2.status_code == 200, f"OTP verify failed: {r2.text}"
    return r2.json()["access_token"]


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_otp_request_known_official(app_with_test_db):
    """1. Known official phone → 200, otp_sent=True, dev_code present."""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_test_db), base_url="http://test"
    ) as client:
        r = await client.post(
            "/api/v1/auth/otp/request", json={"phone": "+919001000001"}
        )
    assert r.status_code == 200
    data = r.json()
    assert data["otp_sent"] is True
    assert data["dev_code"] is not None
    assert len(data["dev_code"]) == 6


@pytest.mark.anyio
async def test_otp_request_unknown_phone(app_with_test_db):
    """2. Unknown phone → 404."""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_test_db), base_url="http://test"
    ) as client:
        r = await client.post(
            "/api/v1/auth/otp/request", json={"phone": "+910000000000"}
        )
    assert r.status_code == 404


@pytest.mark.anyio
async def test_otp_verify_wrong_code(app_with_test_db):
    """3. Wrong OTP code → 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_test_db), base_url="http://test"
    ) as client:
        await client.post("/api/v1/auth/otp/request", json={"phone": "+919001000001"})
        r = await client.post(
            "/api/v1/auth/otp/verify",
            json={"phone": "+919001000001", "code": "000000"},
        )
    assert r.status_code == 401


@pytest.mark.anyio
async def test_otp_verify_correct_code(app_with_test_db):
    """4. Correct OTP → 200, access_token present, role=DM."""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_test_db), base_url="http://test"
    ) as client:
        r1 = await client.post(
            "/api/v1/auth/otp/request", json={"phone": "+919001000001"}
        )
        code = r1.json()["dev_code"]
        r2 = await client.post(
            "/api/v1/auth/otp/verify",
            json={"phone": "+919001000001", "code": code},
        )
    assert r2.status_code == 200
    data = r2.json()
    assert "access_token" in data
    assert data["role"] == "DM"
    assert data["user_type"] == "official"
    assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_me_no_token(app_with_test_db):
    """5. GET /auth/me with no token → 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_test_db), base_url="http://test"
    ) as client:
        r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.anyio
async def test_me_valid_token(app_with_test_db):
    """6. GET /auth/me with valid DM token → 200, correct role + jurisdiction."""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_test_db), base_url="http://test"
    ) as client:
        token = await _get_token(client, "+919001000001")
        r = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
    assert r.status_code == 200
    data = r.json()
    assert data["role"] == "DM"
    assert data["jurisdiction_type"] == "district"
    assert data["user_type"] == "official"


@pytest.mark.anyio
async def test_dashboard_tehsildar_scope(app_with_test_db):
    """7. Tehsildar → only villages within their tehsil (teh-001)."""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_test_db), base_url="http://test"
    ) as client:
        token = await _get_token(client, "+919001000002")
        r = await client.get(
            "/api/v1/dashboard/villages",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 200
    villages = r.json()
    assert len(villages) == 2  # vil-001 and vil-002 are both in teh-001
    ids = {v["id"] for v in villages}
    assert "vil-001" in ids
    assert "vil-002" in ids


@pytest.mark.anyio
async def test_dashboard_dm_scope(app_with_test_db):
    """8. DM → all villages in district (same 2 in our test DB)."""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_test_db), base_url="http://test"
    ) as client:
        token = await _get_token(client, "+919001000001")
        r = await client.get(
            "/api/v1/dashboard/villages",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 200
    villages = r.json()
    # DM should see at least what Tehsildar sees (same district)
    assert len(villages) >= 2
