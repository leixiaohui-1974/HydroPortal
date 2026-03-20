"""Capability introspection API tests."""

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
async def test_capabilities_snapshot_returns_registry_backed_apps(auth_client: AsyncClient):
    resp = await auth_client.get("/api/apps/capabilities")
    assert resp.status_code == 200
    data = resp.json()
    assert data["app_count"] >= 5
    assert data["tool_count"] > 0
    assert isinstance(data["apps"], list)
    app_ids = {item["app_id"] for item in data["apps"]}
    assert {"guard", "design", "lab", "edu", "arena"}.issubset(app_ids)


@pytest.mark.asyncio
async def test_capabilities_snapshot_includes_roles_hints_and_tools(auth_client: AsyncClient):
    resp = await auth_client.get("/api/apps/capabilities")
    assert resp.status_code == 200
    data = resp.json()
    design = next(item for item in data["apps"] if item["app_id"] == "design")
    assert "designer" in design["role_names"]
    assert any("check_compliance" in hint for hint in design["routing_hints"])
    assert any(tool["tool_name"] == "check_compliance" for tool in design["tools"])


@pytest.mark.asyncio
async def test_capabilities_snapshot_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.get("/api/apps/capabilities")
        assert resp.status_code == 401
