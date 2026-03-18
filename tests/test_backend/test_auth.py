"""Auth flow tests — JWT, bcrypt verification, role-based access."""

from httpx import AsyncClient, ASGITransport
import pytest
import pytest_asyncio

from backend.app import app
from backend.deps import verify_password, create_jwt, decode_jwt, issue_token, _pwd_context


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _get_token(client: AsyncClient, username: str, password: str) -> str:
    resp = await client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    resp = await client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    resp = await client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_user(client: AsyncClient):
    resp = await client.post("/api/auth/login", json={"username": "nobody", "password": "x"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /me endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient):
    token = await _get_token(client, "operator", "oper123")
    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "operator"
    assert data["role"] == "operator"


# ---------------------------------------------------------------------------
# bcrypt password verification
# ---------------------------------------------------------------------------

def test_bcrypt_verify_correct():
    hashed = _pwd_context.hash("test_pass_123")
    assert verify_password("test_pass_123", hashed) is True


def test_bcrypt_verify_wrong():
    hashed = _pwd_context.hash("correct")
    assert verify_password("wrong", hashed) is False


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def test_create_and_decode_jwt():
    payload = {"sub": "testuser", "role": "admin"}
    token = create_jwt(payload)
    decoded = decode_jwt(token)
    assert decoded["sub"] == "testuser"
    assert decoded["role"] == "admin"


def test_decode_invalid_jwt():
    with pytest.raises(ValueError):
        decode_jwt("not.a.valid.token")


def test_issue_token_contains_sub_and_role():
    token = issue_token("admin", "admin")
    decoded = decode_jwt(token)
    assert decoded["sub"] == "admin"
    assert decoded["role"] == "admin"
    assert "exp" in decoded


# ---------------------------------------------------------------------------
# Role-based access
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_role_admin_can_access_guard(client: AsyncClient):
    token = await _get_token(client, "admin", "admin123")
    resp = await client.get("/api/guard/stations", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_expired_token_rejected(client: AsyncClient):
    # Create a token with exp in the past
    import time
    token = create_jwt({"sub": "admin", "role": "admin", "exp": time.time() - 100})
    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
