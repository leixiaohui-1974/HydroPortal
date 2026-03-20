"""Gateway API tests — routing, skill execution, tools."""

from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient, ASGITransport, Response
import pytest
import pytest_asyncio

from backend.app import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def auth_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        login = await c.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        token = login.json()["access_token"]
        c.headers["Authorization"] = f"Bearer {token}"
        yield c


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gateway_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.get("/api/gateway/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["portal"] == "ok"
        assert "apps" in data


# ---------------------------------------------------------------------------
# Chat routing
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gateway_chat(auth_client: AsyncClient):
    with patch("backend.routers.gateway.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.post.return_value = Response(200, json={"reply": "ok", "tool_calls": []})
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

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
    with patch("backend.routers.gateway.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.post.return_value = Response(200, json={"reply": "ok", "tool_calls": []})
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        resp = await auth_client.post(
            "/api/gateway/chat",
            json={"message": "hello", "app_id": "design"},
        )
        assert resp.status_code == 200
        assert resp.json()["app_id"] == "design"


@pytest.mark.asyncio
async def test_gateway_chat_routes_design_keyword(auth_client: AsyncClient):
    with patch("backend.routers.gateway.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.post.return_value = Response(200, json={"reply": "ok", "tool_calls": []})
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        resp = await auth_client.post(
            "/api/gateway/chat",
            json={"message": "Check compliance for scheme A"},
        )
        assert resp.status_code == 200
        assert resp.json()["app_id"] == "design"


@pytest.mark.asyncio
async def test_gateway_chat_routes_by_discovered_tool_name(auth_client: AsyncClient):
    with patch("backend.routers.gateway.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.post.return_value = Response(200, json={"reply": "ok", "tool_calls": []})
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        resp = await auth_client.post(
            "/api/gateway/chat",
            json={"message": "Please run check_compliance for scheme A"},
        )
        assert resp.status_code == 200
        assert resp.json()["app_id"] == "design"


@pytest.mark.asyncio
async def test_gateway_chat_unknown_app(auth_client: AsyncClient):
    resp = await auth_client.post(
        "/api/gateway/chat",
        json={"message": "hello", "app_id": "nonexistent"},
    )
    assert resp.status_code == 200
    assert "not registered" in resp.json()["reply"]


@pytest.mark.asyncio
async def test_gateway_chat_normalizes_downstream_http_error(auth_client: AsyncClient):
    with patch("backend.routers.gateway.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.post.return_value = Response(
            422,
            json={"detail": "invalid chat payload"},
            headers={"content-type": "application/json"},
        )
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        resp = await auth_client.post(
            "/api/gateway/chat",
            json={"message": "Show me station alerts"},
        )

    assert resp.status_code == 502
    detail = resp.json()["detail"]
    assert detail["app_id"] == "guard"
    assert detail["downstream_status"] == 422
    assert detail["detail"]["detail"] == "invalid chat payload"


# ---------------------------------------------------------------------------
# Skill execution
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gateway_skill_no_route(auth_client: AsyncClient):
    """Skill with unknown prefix should return 404."""
    resp = await auth_client.post(
        "/api/gateway/skill",
        json={"skill_name": "unknown_domain.do_something", "params": {}},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_gateway_skill_downstream_unreachable(auth_client: AsyncClient):
    """Skill with valid prefix but unreachable downstream returns 502."""
    resp = await auth_client.post(
        "/api/gateway/skill",
        json={"skill_name": "guard.get_alerts", "params": {}},
    )
    # Downstream is not actually running in tests -> 502
    assert resp.status_code == 502


@pytest.mark.asyncio
async def test_gateway_skill_success_mocked(auth_client: AsyncClient):
    """Mock a successful downstream skill response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": {"data": [1, 2, 3]}, "status": "ok"}
    mock_response.headers = {"content-type": "application/json"}

    with patch("backend.routers.gateway.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.post.return_value = mock_response
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        resp = await auth_client.post(
            "/api/gateway/skill",
            json={"skill_name": "guard.get_alerts", "params": {"level": "critical"}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["result"]["data"] == [1, 2, 3]


@pytest.mark.asyncio
async def test_gateway_skill_prefers_discovered_tool_catalog(auth_client: AsyncClient):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": {"ok": True}, "status": "ok"}
    mock_response.headers = {"content-type": "application/json"}

    with patch("backend.routers.gateway.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.post.return_value = mock_response
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        resp = await auth_client.post(
            "/api/gateway/skill",
            json={"skill_name": "check_compliance", "params": {"scheme": "A"}},
        )
        assert resp.status_code == 200
        called_url = instance.post.await_args.args[0]
        assert called_url.endswith("/api/skill")
        assert "8002" in called_url


@pytest.mark.asyncio
async def test_gateway_skill_handles_malformed_success_payload(auth_client: AsyncClient):
    with patch("backend.routers.gateway.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.post.return_value = Response(
            200,
            content=b"not-json",
            headers={"content-type": "application/json"},
        )
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        resp = await auth_client.post(
            "/api/gateway/skill",
            json={"skill_name": "guard.get_alerts", "params": {}},
        )

    assert resp.status_code == 502
    assert "invalid JSON payload" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_gateway_skill_handles_malformed_error_payload(auth_client: AsyncClient):
    with patch("backend.routers.gateway.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.post.return_value = Response(
            400,
            content=b"upstream validation failed",
            headers={"content-type": "application/json"},
        )
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        resp = await auth_client.post(
            "/api/gateway/skill",
            json={"skill_name": "guard.get_alerts", "params": {}},
        )

    assert resp.status_code == 400
    assert resp.json()["detail"] == "upstream validation failed"


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gateway_tools(auth_client: AsyncClient):
    resp = await auth_client.get("/api/gateway/tools")
    assert resp.status_code == 200
    tools = resp.json()
    assert isinstance(tools, list)
    assert len(tools) > 0
    assert "tool_name" in tools[0]


@pytest.mark.asyncio
async def test_gateway_tools_unauthenticated():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.get("/api/gateway/tools")
        assert resp.status_code == 401
