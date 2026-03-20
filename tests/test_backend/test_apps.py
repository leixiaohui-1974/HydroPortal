"""App discovery tests."""

from httpx import AsyncClient, ASGITransport
import pytest
import pytest_asyncio

from backend.app import app


@pytest_asyncio.fixture
async def auth_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        login = await c.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        token = login.json()["access_token"]
        c.headers["Authorization"] = f"Bearer {token}"
        yield c


@pytest.mark.asyncio
async def test_list_apps(auth_client: AsyncClient):
    resp = await auth_client.get("/api/apps/list")
    assert resp.status_code == 200
    apps_list = resp.json()
    assert isinstance(apps_list, list)
    ids = {a["app_id"] for a in apps_list}
    assert {"guard", "design", "lab", "edu", "arena"}.issubset(ids)
    assert all(a["base_url"] for a in apps_list)


@pytest.mark.asyncio
async def test_app_status_known(auth_client: AsyncClient):
    resp = await auth_client.get("/api/apps/guard/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["app_id"] == "guard"
    assert data["name"] == "HydroGuard"


@pytest.mark.asyncio
async def test_app_status_unknown(auth_client: AsyncClient):
    resp = await auth_client.get("/api/apps/nonexistent/status")
    assert resp.status_code == 200
    assert resp.json()["status"] == "not_found"
