"""Dependency injection helpers for auth and app registry."""

from __future__ import annotations

import os
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend import config
from backend.plugin_discovery import discover_hydromind_apps

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def _ensure_bcrypt_version_shim() -> None:
    """Backfill bcrypt.__about__.__version__ for passlib 1.7.x compatibility."""
    if hasattr(bcrypt, "__about__"):
        return
    version = getattr(bcrypt, "__version__", None)
    if version:
        bcrypt.__about__ = SimpleNamespace(__version__=version)


_ensure_bcrypt_version_shim()

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _build_demo_users() -> dict[str, dict[str, str]]:
    """Build demo users from env vars (dev/demo mode only)."""
    return {
        "admin": {
            "password": _pwd_context.hash(
                os.environ.get("HYDROPORTAL_DEMO_ADMIN_PASSWORD", "admin123")
            ),
            "role": "admin",
            "display_name": "系统管理员",
        },
        "designer": {
            "password": _pwd_context.hash(
                os.environ.get("HYDROPORTAL_DEMO_DESIGNER_PASSWORD", "design123")
            ),
            "role": "designer",
            "display_name": "设计工程师",
        },
        "operator": {
            "password": _pwd_context.hash(
                os.environ.get("HYDROPORTAL_DEMO_OPERATOR_PASSWORD", "oper123")
            ),
            "role": "operator",
            "display_name": "调度员",
        },
    }


@lru_cache(maxsize=8)
def _cached_demo_users(password_snapshot: tuple[str, str, str]) -> dict[str, dict[str, str]]:
    """Cache hashed demo users until the configured demo passwords change."""
    return _build_demo_users()

def get_demo_users() -> dict[str, dict[str, str]]:
    """Return the current demo users for the active auth configuration."""
    if not config.DEMO_AUTH_ENABLED:
        return {}
    password_snapshot = (
        os.environ.get("HYDROPORTAL_DEMO_ADMIN_PASSWORD", "admin123"),
        os.environ.get("HYDROPORTAL_DEMO_DESIGNER_PASSWORD", "design123"),
        os.environ.get("HYDROPORTAL_DEMO_OPERATOR_PASSWORD", "oper123"),
    )
    return _cached_demo_users(password_snapshot)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return _pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT helpers (python-jose)
# ---------------------------------------------------------------------------


def create_jwt(payload: dict[str, Any], secret: str | None = None) -> str:
    """Create a signed JWT using python-jose."""
    return jwt.encode(payload, secret or config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def decode_jwt(token: str, secret: str | None = None) -> dict[str, Any]:
    """Decode and verify a JWT. Raises on invalid / expired tokens."""
    try:
        payload = jwt.decode(token, secret or config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    except JWTError as exc:
        raise ValueError(str(exc)) from exc
    return payload


def issue_token(username: str, role: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=config.JWT_EXPIRE_MINUTES)
    return create_jwt({"sub": username, "role": role, "exp": exp.timestamp()})


# ---------------------------------------------------------------------------
# FastAPI dependency -- get current user from Authorization header
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
    demo_users = get_demo_users()
    if username not in demo_users:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown user")
    expected_role = demo_users[username]["role"]
    token_role = payload.get("role")
    if token_role != expected_role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token role mismatch")

    return {
        "username": username,
        "role": expected_role,
        "display_name": demo_users[username]["display_name"],
    }


# ---------------------------------------------------------------------------
# App registry helpers
# ---------------------------------------------------------------------------

_app_registry: dict[str, config.AppEndpoint] = {}


def init_app_registry() -> None:
    """Populate the app registry from discovery first, then config fallback."""
    _app_registry.clear()
    discovered = discover_hydromind_apps()
    if discovered:
        _app_registry.update(discovered)
        return
    for app in config.HYDRO_APPS:
        _app_registry[app.app_id] = app


def get_app_registry() -> dict[str, config.AppEndpoint]:
    return _app_registry


def get_app_endpoint(app_id: str) -> config.AppEndpoint | None:
    return _app_registry.get(app_id)
