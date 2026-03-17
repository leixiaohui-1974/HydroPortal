"""Dependency injection — app registry, auth helpers."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend import config

# ---------------------------------------------------------------------------
# In-memory user store (demo)
# ---------------------------------------------------------------------------

DEMO_USERS: dict[str, dict[str, str]] = {
    "admin": {
        "password": "admin123",
        "role": "admin",
        "display_name": "系统管理员",
    },
    "designer": {
        "password": "design123",
        "role": "designer",
        "display_name": "设计工程师",
    },
    "operator": {
        "password": "oper123",
        "role": "operator",
        "display_name": "调度员",
    },
}

# ---------------------------------------------------------------------------
# JWT helpers (HMAC-SHA256, no dependency on python-jose at runtime)
# ---------------------------------------------------------------------------

def _b64url_encode(data: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    import base64
    s += "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)


def create_jwt(payload: dict[str, Any], secret: str = config.JWT_SECRET) -> str:
    """Create a simple HMAC-SHA256 JWT."""
    header = {"alg": "HS256", "typ": "JWT"}
    h = _b64url_encode(json.dumps(header).encode())
    p = _b64url_encode(json.dumps(payload, default=str).encode())
    sig = hmac.new(secret.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{_b64url_encode(sig)}"


def decode_jwt(token: str, secret: str = config.JWT_SECRET) -> dict[str, Any]:
    """Decode and verify a JWT. Raises on invalid / expired tokens."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format")
    h, p, s = parts
    expected_sig = hmac.new(secret.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    actual_sig = _b64url_decode(s)
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid signature")
    payload = json.loads(_b64url_decode(p))
    if "exp" in payload and float(payload["exp"]) < time.time():
        raise ValueError("Token expired")
    return payload


def issue_token(username: str, role: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=config.JWT_EXPIRE_MINUTES)
    return create_jwt({"sub": username, "role": role, "exp": exp.timestamp()})


# ---------------------------------------------------------------------------
# FastAPI dependency — get current user from Authorization header
# ---------------------------------------------------------------------------

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, str]:
    if cred is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_jwt(cred.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    username = payload.get("sub")
    if username not in DEMO_USERS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown user")
    return {"username": username, "role": payload["role"], "display_name": DEMO_USERS[username]["display_name"]}


# ---------------------------------------------------------------------------
# App registry helpers
# ---------------------------------------------------------------------------

_app_registry: dict[str, config.AppEndpoint] = {}


def init_app_registry() -> None:
    """Populate the app registry from config."""
    for app in config.HYDRO_APPS:
        _app_registry[app.app_id] = app


def get_app_registry() -> dict[str, config.AppEndpoint]:
    return _app_registry


def get_app_endpoint(app_id: str) -> config.AppEndpoint | None:
    return _app_registry.get(app_id)
