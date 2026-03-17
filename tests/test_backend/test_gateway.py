"""Gateway API tests."""

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
async def test_gateway_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.get("/api/gateway/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["portal"] == "ok"
        assert "apps" in data


@pytest.mark.asyncio
async def test_gateway_chat(auth_client: AsyncClient):
    resp = await auth_client.post(
        "/api/gateway/chat",
        json={"message": "Show me station alerts"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "app_id" in data
    assert data["app_id"] == "guard"  # "alert" keyword -> guard


@pytest.mark.asyncio
async def test_gateway_chat_with_explicit_app(auth_client: AsyncClient):
    resp = await auth_client.post(
        "/api/gateway/chat",
        json={"message": "hello", "app_id": "design"},
    )
    assert resp.status_code == 200
    assert resp.json()["app_id"] == "design"


@pytest.mark.asyncio
async def test_gateway_skill(auth_client: AsyncClient):
    resp = await auth_client.post(
        "/api/gateway/skill",
        json={"skill_name": "test_skill", "params": {"a": 1}},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_gateway_tools(auth_client: AsyncClient):
    resp = await auth_client.get("/api/gateway/tools")
    assert resp.status_code == 200
    tools = resp.json()
    assert isinstance(tools, list)
    assert len(tools) > 0
    assert "tool_name" in tools[0]
