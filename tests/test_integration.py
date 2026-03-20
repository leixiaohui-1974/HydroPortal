"""Integration tests for HydroPortal gateway.

Tests that the portal can route to all downstream services, handles auth
flows correctly, and enforces role-based access control.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

# ---------------------------------------------------------------------------
# Conditional imports -- skip entire module if FastAPI deps are missing
# ---------------------------------------------------------------------------

try:
    from fastapi.testclient import TestClient
    from backend.app import app
    from backend.deps import (
        create_jwt,
        decode_jwt,
        init_app_registry,
        get_app_registry,
        issue_token,
        verify_password,
    )
    from backend.config import AppEndpoint
    from backend import config
    _DEPS_OK = True
except ImportError as _import_err:
    _DEPS_OK = False
    _import_reason = str(_import_err)

pytestmark = pytest.mark.skipif(
    not _DEPS_OK,
    reason=f"Backend dependencies not installed: {_import_reason if not _DEPS_OK else ''}",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client():
    """Create a test client with the app registry initialized."""
    init_app_registry()
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def admin_token() -> str:
    """Issue a valid admin JWT."""
    return issue_token("admin", "admin")


@pytest.fixture()
def operator_token() -> str:
    """Issue a valid operator JWT."""
    return issue_token("operator", "operator")


@pytest.fixture()
def designer_token() -> str:
    """Issue a valid designer JWT."""
    return issue_token("designer", "designer")


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# 1. Route Table Completeness
# ============================================================================


class TestRouteTableCompleteness:
    """All downstream project endpoints must be registered."""

    EXPECTED_APP_IDS = {"guard", "design", "lab", "edu", "arena"}

    def test_all_apps_registered(self, client):
        """The app registry should contain all expected downstream apps."""
        registry = get_app_registry()
        registered = set(registry.keys())
        missing = self.EXPECTED_APP_IDS - registered
        assert len(missing) == 0, (
            f"Missing app registrations: {missing}. "
            f"Registered: {registered}"
        )

    def test_each_app_has_base_url(self, client):
        """Every registered app must have a non-empty base_url."""
        registry = get_app_registry()
        for app_id, endpoint in registry.items():
            assert endpoint.base_url, (
                f"App '{app_id}' has empty base_url"
            )
            assert endpoint.base_url.startswith("http"), (
                f"App '{app_id}' base_url '{endpoint.base_url}' is not a valid URL"
            )

    def test_each_app_has_name(self, client):
        """Every registered app must have a human-readable name."""
        registry = get_app_registry()
        for app_id, endpoint in registry.items():
            assert endpoint.name, (
                f"App '{app_id}' has empty name"
            )

    def test_keyword_routing_covers_all_apps(self, client):
        """The keyword routing map should route to all registered apps."""
        from backend.routers.gateway import _KEYWORD_MAP, _route_message

        routed_apps = set(_KEYWORD_MAP.values())
        # The default route is "guard", so guard is always covered
        routed_apps.add("guard")

        for app_id in self.EXPECTED_APP_IDS:
            assert app_id in routed_apps, (
                f"No keyword routes to app '{app_id}'. "
                f"Add keywords to _KEYWORD_MAP in gateway.py"
            )

    def test_portal_routers_exist_for_each_app(self, client):
        """Each app should have a corresponding proxy router mounted."""
        routes = [route.path for route in app.routes]
        expected_prefixes = [
            "/api/guard",
            "/api/design",
            "/api/lab",
            "/api/edu",
            "/api/arena",
        ]
        for prefix in expected_prefixes:
            has_route = any(prefix in r for r in routes)
            assert has_route, (
                f"No router found for prefix '{prefix}'. "
                f"Ensure a router is included in app.py"
            )


# ============================================================================
# 2. Gateway Health Endpoint
# ============================================================================


class TestGatewayHealth:
    """Test the gateway health reporting."""

    def test_root_health_returns_ok(self, client):
        """GET /health should return ok status."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "hydroportal"

    def test_root_endpoint_returns_service_info(self, client):
        """GET / should return service metadata."""
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "service" in data
        assert "version" in data

    def test_gateway_health_endpoint(self, client, admin_token):
        """GET /api/gateway/health should report all app statuses.

        In test mode, downstream services are unreachable, so all apps
        should report 'unreachable'.
        """
        resp = client.get(
            "/api/gateway/health",
        )
        # Gateway health does not require auth
        assert resp.status_code == 200
        data = resp.json()
        assert data["portal"] == "ok"
        assert "apps" in data
        # All apps should be in the response
        for app_id in TestRouteTableCompleteness.EXPECTED_APP_IDS:
            assert app_id in data["apps"], (
                f"App '{app_id}' missing from health report"
            )


# ============================================================================
# 3. Auth Flow End-to-End
# ============================================================================


class TestAuthFlow:
    """Test login -> token -> protected endpoint flow."""

    def test_login_success(self, client):
        """POST /api/auth/login with valid credentials returns a token."""
        resp = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        """POST /api/auth/login with wrong password returns 401."""
        resp = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong"},
        )
        assert resp.status_code == 401

    def test_login_unknown_user(self, client):
        """POST /api/auth/login with unknown user returns 401."""
        resp = client.post(
            "/api/auth/login",
            json={"username": "nobody", "password": "pass"},
        )
        assert resp.status_code == 401

    def test_token_grants_access_to_me(self, client):
        """A valid token should allow access to GET /api/auth/me."""
        # Login first
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "operator", "password": "oper123"},
        )
        token = login_resp.json()["access_token"]

        # Use token to access protected endpoint
        me_resp = client.get(
            "/api/auth/me",
            headers=_auth_header(token),
        )
        assert me_resp.status_code == 200
        data = me_resp.json()
        assert data["username"] == "operator"
        assert data["role"] == "operator"

    def test_expired_token_rejected(self, client):
        """An expired token should be rejected with 401."""
        import time
        # Create a token that expired 1 second ago
        expired_payload = {
            "sub": "admin",
            "role": "admin",
            "exp": (datetime.now(timezone.utc).timestamp() - 1),
        }
        expired_token = create_jwt(expired_payload)

        resp = client.get(
            "/api/auth/me",
            headers=_auth_header(expired_token),
        )
        assert resp.status_code == 401

    def test_no_token_returns_401(self, client):
        """Protected endpoints without Authorization header return 401."""
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, client):
        """A garbage token should return 401."""
        resp = client.get(
            "/api/auth/me",
            headers=_auth_header("not.a.valid.jwt.token"),
        )
        assert resp.status_code == 401

    def test_jwt_roundtrip(self):
        """JWT encode -> decode should preserve payload."""
        token = issue_token("designer", "designer")
        payload = decode_jwt(token)
        assert payload["sub"] == "designer"
        assert payload["role"] == "designer"
        assert "exp" in payload


# ============================================================================
# 4. Role-Based Access Control Matrix
# ============================================================================


class TestRoleBasedAccessControl:
    """Test that different roles have appropriate access patterns."""

    ALL_DEMO_USERS = [
        ("admin", "admin123", "admin"),
        ("designer", "design123", "designer"),
        ("operator", "oper123", "operator"),
    ]

    def test_all_demo_users_can_login(self, client):
        """Every demo user should be able to log in successfully."""
        for username, password, expected_role in self.ALL_DEMO_USERS:
            resp = client.post(
                "/api/auth/login",
                json={"username": username, "password": password},
            )
            assert resp.status_code == 200, (
                f"User '{username}' failed to login"
            )
            token = resp.json()["access_token"]
            payload = decode_jwt(token)
            assert payload["role"] == expected_role

    def test_all_roles_can_access_gateway_chat(self, client):
        """All authenticated users should be able to use the chat endpoint."""
        for username, password, _ in self.ALL_DEMO_USERS:
            login_resp = client.post(
                "/api/auth/login",
                json={"username": username, "password": password},
            )
            token = login_resp.json()["access_token"]

            chat_resp = client.post(
                "/api/gateway/chat",
                json={"message": "hello"},
                headers=_auth_header(token),
            )
            # Should not be 401 or 403
            assert chat_resp.status_code in (200, 422, 500), (
                f"User '{username}' got unexpected status {chat_resp.status_code} "
                f"on gateway/chat"
            )

    def test_all_roles_can_access_gateway_tools(self, client):
        """All authenticated users can list available tools."""
        for username, password, _ in self.ALL_DEMO_USERS:
            login_resp = client.post(
                "/api/auth/login",
                json={"username": username, "password": password},
            )
            token = login_resp.json()["access_token"]

            tools_resp = client.get(
                "/api/gateway/tools",
                headers=_auth_header(token),
            )
            assert tools_resp.status_code == 200
            tools = tools_resp.json()
            assert isinstance(tools, list)
            assert len(tools) > 0, "Tool catalog should not be empty"

    def test_gateway_tools_cover_all_apps(self, client, admin_token):
        """The tool catalog should have tools from all registered apps."""
        resp = client.get(
            "/api/gateway/tools",
            headers=_auth_header(admin_token),
        )
        assert resp.status_code == 200
        tools = resp.json()

        apps_with_tools = {t["app_id"] for t in tools}
        expected = set(get_app_registry().keys())
        missing = expected - apps_with_tools
        assert len(missing) == 0, (
            f"No tools registered for apps: {missing}"
        )

    def test_unauthenticated_chat_rejected(self, client):
        """Gateway chat should reject unauthenticated requests."""
        resp = client.post(
            "/api/gateway/chat",
            json={"message": "test"},
        )
        assert resp.status_code == 401


# ============================================================================
# 5. Gateway Routing Logic
# ============================================================================


class TestGatewayRouting:
    """Test the keyword-based message routing logic."""

    def test_station_routes_to_guard(self):
        from backend.routers.gateway import _route_message
        assert _route_message("Check station STN_001 status") == "guard"

    def test_scada_routes_to_guard(self):
        from backend.routers.gateway import _route_message
        assert _route_message("Query SCADA data for pump 3") == "guard"

    def test_design_routes_to_design(self):
        from backend.routers.gateway import _route_message
        assert _route_message("Create a new design scheme") == "design"

    def test_experiment_routes_to_lab(self):
        from backend.routers.gateway import _route_message
        assert _route_message("Run an experiment with SWMM") == "lab"

    def test_course_routes_to_edu(self):
        from backend.routers.gateway import _route_message
        assert _route_message("List all available courses") == "edu"

    def test_contest_routes_to_arena(self):
        from backend.routers.gateway import _route_message
        assert _route_message("Join the latest contest") == "arena"

    def test_default_routes_to_guard(self):
        from backend.routers.gateway import _route_message
        assert _route_message("Hello, what can you do?") == "guard"

    def test_explicit_app_id_overrides_routing(self, client, admin_token):
        """When app_id is explicit in the request, routing is bypassed."""
        resp = client.post(
            "/api/gateway/chat",
            json={"message": "hello", "app_id": "design"},
            headers=_auth_header(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["app_id"] == "design"


class TestRegistryConsistency:
    """Ensure discovery snapshot is reflected consistently across endpoints."""

    def test_end_to_end_registry_consistency_for_health_chat_skill(self, client, admin_token, monkeypatch):
        discovered = {
            "design": AppEndpoint(
                app_id="design",
                name="HydroDesign",
                base_url="http://localhost:8102",
                available_tools=["check_compliance"],
                tool_catalog=[{"name": "check_compliance", "description": "Run compliance check"}],
                role_names=["designer"],
                routing_hints=["designer", "check_compliance", "optimization_design"],
                source="workspace",
            ),
            "guard": AppEndpoint(
                app_id="guard",
                name="HydroGuard",
                base_url="http://localhost:8101",
                available_tools=["station.collect_data"],
                tool_catalog=[{"name": "station.collect_data", "description": "Collect station data"}],
                role_names=["operator"],
                routing_hints=["operator", "station.collect_data"],
                source="workspace",
            ),
        }

        monkeypatch.setattr("backend.deps.discover_hydromind_apps", lambda: discovered)
        init_app_registry()

        class FakeResponse:
            def __init__(self, status_code, payload=None, headers=None):
                self.status_code = status_code
                self._payload = payload if payload is not None else {}
                self.headers = headers or {"content-type": "application/json"}

            def json(self):
                return self._payload

            @property
            def text(self):
                return str(self._payload)

        class FakeAsyncClient:
            def __init__(self, *args, **kwargs):
                self.calls = []

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def get(self, url, *args, **kwargs):
                self.calls.append(("GET", url, None))
                return FakeResponse(200, {"status": "ok"})

            async def post(self, url, *args, **kwargs):
                self.calls.append(("POST", url, kwargs.get("json")))
                if url.endswith("/api/chat"):
                    return FakeResponse(200, {"reply": "ok", "tool_calls": []})
                return FakeResponse(200, {"status": "ok", "result": {"accepted": True}})

        fake_client = FakeAsyncClient()

        class ClientFactory:
            def __call__(self, *args, **kwargs):
                return fake_client

        monkeypatch.setattr("backend.routers.gateway.httpx.AsyncClient", ClientFactory())

        apps_resp = client.get("/api/apps/list", headers=_auth_header(admin_token))
        assert apps_resp.status_code == 200
        app_ids = {item["app_id"] for item in apps_resp.json()}
        assert app_ids == {"design", "guard"}

        health_resp = client.get("/api/gateway/health")
        assert health_resp.status_code == 200
        assert set(health_resp.json()["apps"].keys()) == {"design", "guard"}

        chat_resp = client.post(
            "/api/gateway/chat",
            json={"message": "please run check_compliance"},
            headers=_auth_header(admin_token),
        )
        assert chat_resp.status_code == 200
        assert chat_resp.json()["app_id"] == "design"

        skill_resp = client.post(
            "/api/gateway/skill",
            json={"skill_name": "check_compliance", "params": {"scheme": "A"}},
            headers=_auth_header(admin_token),
        )
        assert skill_resp.status_code == 200

        urls = [call[1] for call in fake_client.calls]
        assert "http://localhost:8102/api/chat" in urls
        assert "http://localhost:8102/api/skill" in urls

    def test_unknown_app_id_returns_message(self, client, admin_token):
        """An unknown app_id should return an informative message."""
        resp = client.post(
            "/api/gateway/chat",
            json={"message": "hello", "app_id": "nonexistent"},
            headers=_auth_header(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "not registered" in data["reply"].lower() or "nonexistent" in data["reply"].lower()


# ============================================================================
# 6. Gateway Skill Execution
# ============================================================================


class TestGatewaySkill:
    """Test the skill execution endpoint."""

    def test_skill_endpoint_downstream_unreachable(self, client, admin_token):
        """POST /api/gateway/skill should return 502 when downstream is unreachable."""
        resp = client.post(
            "/api/gateway/skill",
            json={"skill_name": "guard.collect_data", "params": {"station_id": "STN_001"}},
            headers=_auth_header(admin_token),
        )
        # Downstream service is not running in tests, so expect 502
        assert resp.status_code == 502

    def test_skill_without_auth_rejected(self, client):
        """Skill endpoint should reject unauthenticated requests."""
        resp = client.post(
            "/api/gateway/skill",
            json={"skill_name": "test", "params": {}},
        )
        assert resp.status_code == 401
