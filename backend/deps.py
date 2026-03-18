"""Dependency injection — app registry, auth helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend import config

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------------
# In-memory user store (demo) — passwords are bcrypt hashes
# ---------------------------------------------------------------------------

DEMO_USERS: dict[str, dict[str, str]] = {
    "admin": {
        "password": _pwd_context.hash("admin123"),
        "role": "admin",
        "display_name": "系统管理员",
    },
    "designer": {
        "password": _pwd_context.hash("design123"),
        "role": "designer",
        "display_name": "设计工程师",
    },
    "operator": {
        "password": _pwd_context.hash("oper123"),
        "role": "operator",
        "display_name": "调度员",
    },
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return _pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT helpers (python-jose)
# ---------------------------------------------------------------------------


def create_jwt(payload: dict[str, Any], secret: str = config.JWT_SECRET) -> str:
    """Create a signed JWT using python-jose."""
    return jwt.encode(payload, secret, algorithm=config.JWT_ALGORITHM)


def decode_jwt(token: str, secret: str = config.JWT_SECRET) -> dict[str, Any]:
    """Decode and verify a JWT. Raises on invalid / expired tokens."""
    try:
        payload = jwt.decode(token, secret, algorithms=[config.JWT_ALGORITHM])
    except JWTError as exc:
        raise ValueError(str(exc)) from exc
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
