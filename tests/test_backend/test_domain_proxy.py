"""Domain proxy regression tests for downstream error handling."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
from httpx import ASGITransport, AsyncClient, Response
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
async def test_guard_dispatch_propagates_downstream_http_error(auth_client: AsyncClient):
    with patch("backend.routers._proxy.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.post.return_value = Response(
            503,
            json={"detail": "guard unavailable"},
            headers={"content-type": "application/json"},
        )
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        resp = await auth_client.post(
            "/api/guard/dispatch",
            json={"station_id": "ST-001", "command": "close_gate", "params": {}},
        )

    assert resp.status_code == 503
    assert resp.json()["detail"]["detail"] == "guard unavailable"


@pytest.mark.asyncio
async def test_design_compliance_propagates_downstream_validation_error(auth_client: AsyncClient):
    with patch("backend.routers._proxy.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.post.return_value = Response(
            400,
            json={"detail": "invalid scheme"},
            headers={"content-type": "application/json"},
        )
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        resp = await auth_client.post(
            "/api/design/compliance/check",
            json={"scheme_id": "SCH-A"},
        )

    assert resp.status_code == 400
    assert resp.json()["detail"]["detail"] == "invalid scheme"


@pytest.mark.asyncio
async def test_guard_stations_still_falls_back_on_transport_error(auth_client: AsyncClient):
    request = httpx.Request("GET", "http://localhost:8001/api/stations")

    with patch("backend.routers._proxy.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.get.side_effect = httpx.ConnectError("offline", request=request)
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        resp = await auth_client.get("/api/guard/stations")

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["station_id"] == "ST-001"
