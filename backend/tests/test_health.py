"""
Phase 0 smoke-test — verifies all core imports and /health work without a DB.
Run: pytest tests/test_health.py -v
"""
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_health_endpoint():
    """GET /health must return 200 with status=ok — no DB needed."""
    from main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "env" in data


@pytest.mark.anyio
async def test_ping_endpoint():
    """GET /api/v1/ping must return {pong: true}."""
    from main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/ping")
    assert response.status_code == 200
    assert response.json() == {"pong": True}


@pytest.mark.anyio
async def test_docs_available():
    """GET /docs must return 200 (Swagger UI)."""
    from main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/docs")
    assert response.status_code == 200
