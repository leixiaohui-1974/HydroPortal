"""End-to-end smoke tests for HydroPortal gateway forwarding.

These tests mock downstream Hydro app responses through httpx and verify that
the gateway forwards health/chat/skill requests to the correct discovered app.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient, ASGITransport, Response
import pytest
import pytest_asyncio

from backend.app import app
from backend import config
from backend.deps import get_app_registry, init_app_registry


@pytest_asyncio.fixture
async def auth_client():
    init_app_registry()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        login = await c.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        token = login.json()["access_token"]
        c.headers["Authorization"] = f"Bearer {token}"
        yield c


@pytest.mark.asyncio
async def test_gateway_health_forwards_to_all_registered_apps(auth_client: AsyncClient):
    async def fake_get(url, *args, **kwargs):
        if url.endswith("/health"):
            return Response(200, json={"status": "ok", "version": "0.1.0"})
        return Response(404, json={"detail": "not found"})

    with patch("backend.routers.gateway.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.get.side_effect = fake_get
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        resp = await auth_client.get("/api/gateway/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["portal"] == "ok"
        assert all(status == "ok" for status in data["apps"].values())
        assert instance.get.await_count >= 5


@pytest.mark.asyncio
async def test_gateway_health_mixed_status_mapping(auth_client: AsyncClient):
    statuses = {
        "http://localhost:8001/health": Response(200, json={"status": "ok"}),
        "http://localhost:8002/health": Response(503, json={"status": "degraded"}),
        "http://localhost:8003/health": RuntimeError("offline"),
        "http://localhost:8004/health": Response(200, json={"status": "ok"}),
        "http://localhost:8005/health": Response(200, json={"status": "ok"}),
    }

    async def fake_get(url, *args, **kwargs):
        value = statuses[url]
        if isinstance(value, Exception):
            raise value
        return value

    with patch("backend.routers.gateway.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.get.side_effect = fake_get
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        resp = await auth_client.get("/api/gateway/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["apps"]["guard"] == "ok"
        assert data["apps"]["design"] == "http-503"
        assert data["apps"]["lab"] == "unreachable"


@pytest.mark.asyncio
async def test_gateway_chat_forwards_to_discovered_design_app(auth_client: AsyncClient):
    with patch("backend.routers.gateway.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.post.return_value = Response(
            200,
            json={
                "reply": "Design compliance check accepted",
                "tool_calls": [{"tool_name": "check_compliance"}],
            },
        )
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        resp = await auth_client.post(
            "/api/gateway/chat",
            json={"message": "Please run check_compliance for scheme A"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["app_id"] == "design"
        assert data["reply"] == "Design compliance check accepted"
        called_url = instance.post.await_args.args[0]
        assert called_url == "http://localhost:8002/api/chat"
        called_body = instance.post.await_args.kwargs["json"]
        assert called_body["message"] == "Please run check_compliance for scheme A"
        assert called_body["context"] == {}


@pytest.mark.asyncio
async def test_gateway_chat_preserves_downstream_tool_calls(auth_client: AsyncClient):
    with patch("backend.routers.gateway.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.post.return_value = Response(
            200,
            json={
                "reply": "ok",
                "tool_calls": [{"tool_name": "submit_solution", "app_id": "arena"}],
            },
        )
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        resp = await auth_client.post(
            "/api/gateway/chat",
            json={"message": "Submit solution to contest", "context": {"team": "alpha"}},
        )
        assert resp.status_code == 200
        assert resp.json()["tool_calls"] == [{"tool_name": "submit_solution", "app_id": "arena"}]


@pytest.mark.asyncio
async def test_gateway_chat_downstream_non_json_fallback(auth_client: AsyncClient):
    class BadJsonResponse:
        status_code = 200

        def json(self):
            raise ValueError("bad json")

    with patch("backend.routers.gateway.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.post.return_value = BadJsonResponse()
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        resp = await auth_client.post(
            "/api/gateway/chat",
            json={"message": "station status"},
        )
        assert resp.status_code == 200
        assert resp.json()["app_id"] == "guard"
        assert "暂不可达" in resp.json()["reply"]


@pytest.mark.asyncio
async def test_gateway_skill_forwards_exact_tool_to_discovered_app(auth_client: AsyncClient):
    with patch("backend.routers.gateway.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.post.return_value = Response(
            200,
            json={"status": "ok", "result": {"accepted": True}},
        )
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        resp = await auth_client.post(
            "/api/gateway/skill",
            json={"skill_name": "submit_solution", "params": {"problem_id": "p1"}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["result"]["accepted"] is True
        called_url = instance.post.await_args.args[0]
        assert called_url == "http://localhost:8005/api/skill"
        called_body = instance.post.await_args.kwargs["json"]
        assert called_body["skill_name"] == "submit_solution"
        assert called_body["params"] == {"problem_id": "p1"}
        assert called_body["role"] == "admin"


@pytest.mark.asyncio
async def test_gateway_skill_propagates_downstream_http_error(auth_client: AsyncClient):
    with patch("backend.routers.gateway.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.post.return_value = Response(
            400,
            json={"detail": "invalid parameters"},
            headers={"content-type": "application/json"},
        )
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        resp = await auth_client.post(
            "/api/gateway/skill",
            json={"skill_name": "check_compliance", "params": {}},
        )
        assert resp.status_code == 400
        assert "invalid parameters" in str(resp.json())


@pytest.mark.asyncio
async def test_gateway_skill_uses_registry_before_static_routes(auth_client: AsyncClient):
    old_routes = dict(config.SKILL_ROUTES)
    config.SKILL_ROUTES["check_compliance"] = "http://localhost:9999"
    try:
        with patch("backend.routers.gateway.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.post.return_value = Response(200, json={"status": "ok", "result": {"ok": True}})
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            resp = await auth_client.post(
                "/api/gateway/skill",
                json={"skill_name": "check_compliance", "params": {"scheme": "A"}},
            )
            assert resp.status_code == 200
            called_url = instance.post.await_args.args[0]
            assert called_url == "http://localhost:8002/api/skill"
    finally:
        config.SKILL_ROUTES.clear()
        config.SKILL_ROUTES.update(old_routes)


@pytest.mark.asyncio
async def test_gateway_skill_duplicate_tool_name_uses_first_registry_match(auth_client: AsyncClient):
    registry = get_app_registry()
    original_lab = registry["lab"]
    registry["lab"] = original_lab.model_copy(
        update={
            "tool_catalog": [*original_lab.tool_catalog, {"name": "check_compliance", "description": "duplicate"}],
            "available_tools": [*original_lab.available_tools, "check_compliance"],
        }
    )
    try:
        with patch("backend.routers.gateway.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.post.return_value = Response(200, json={"status": "ok", "result": {"ok": True}})
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            resp = await auth_client.post(
                "/api/gateway/skill",
                json={"skill_name": "check_compliance", "params": {}},
            )
            assert resp.status_code == 200
            called_url = instance.post.await_args.args[0]
            assert called_url == "http://localhost:8002/api/skill"
    finally:
        registry["lab"] = original_lab
