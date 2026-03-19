"""Portal configuration — ports, enabled apps, auth settings.

All configuration values are read from environment variables with sensible
defaults for local development.
"""

from __future__ import annotations

import json
import logging
import os

from pydantic import BaseModel

_logger = logging.getLogger(__name__)


def _as_bool(raw: str | None, default: bool = False) -> bool:
    """Parse common truthy values from env vars."""
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class AppEndpoint(BaseModel):
    """Descriptor for a downstream Hydro application."""

    app_id: str
    name: str
    base_url: str
    enabled: bool = True


# ---------------------------------------------------------------------------
# Environment-based configuration
# ---------------------------------------------------------------------------

PORTAL_HOST: str = os.environ.get("HYDROPORTAL_HOST", "0.0.0.0")
PORTAL_PORT: int = int(os.environ.get("HYDROPORTAL_PORT", "8000"))

# Runtime mode
APP_ENV: str = os.environ.get("HYDROPORTAL_ENV", "development").strip().lower()
IS_PRODUCTION: bool = APP_ENV in {"prod", "production"}

# Database
DATABASE_URL: str = os.environ.get(
    "HYDROPORTAL_DATABASE_URL",
    "sqlite+aiosqlite:///./hydroportal.db",
)

# JWT / Auth
DEFAULT_JWT_SECRET = "hydroportal-dev-secret-change-in-production"
JWT_SECRET: str = os.environ.get(
    "HYDROPORTAL_JWT_SECRET", DEFAULT_JWT_SECRET
)
if JWT_SECRET == DEFAULT_JWT_SECRET:
    _logger.warning(
        "SECURITY WARNING: Using default JWT secret. "
        "Set HYDROPORTAL_JWT_SECRET environment variable in production."
    )
JWT_ALGORITHM: str = os.environ.get("HYDROPORTAL_JWT_ALGORITHM", "HS256")
TOKEN_EXPIRE_MINUTES: int = int(
    os.environ.get("HYDROPORTAL_TOKEN_EXPIRE_MINUTES", str(60 * 24))
)
# Keep backward-compatible alias
JWT_EXPIRE_MINUTES: int = TOKEN_EXPIRE_MINUTES

# Rate limiting
RATE_LIMIT_REQUESTS: int = int(os.environ.get("HYDROPORTAL_RATE_LIMIT_REQUESTS", "60"))
RATE_LIMIT_WINDOW_SECONDS: int = int(
    os.environ.get("HYDROPORTAL_RATE_LIMIT_WINDOW_SECONDS", "60")
)

# CORS
CORS_ORIGINS: list[str] = json.loads(
    os.environ.get(
        "HYDROPORTAL_CORS_ORIGINS",
        json.dumps([
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]),
    )
)

# Logging
LOG_LEVEL: str = os.environ.get("HYDROPORTAL_LOG_LEVEL", "INFO").upper()

# SCADA WebSocket
SCADA_WS_INTERVAL: float = float(
    os.environ.get("HYDROPORTAL_SCADA_WS_INTERVAL", "1.0")
)

# Demo/dev auth mode
DEMO_AUTH_ENABLED: bool = _as_bool(
    os.environ.get("HYDROPORTAL_DEMO_AUTH_ENABLED"),
    default=not IS_PRODUCTION,
)
ALLOW_DEMO_AUTH_IN_PRODUCTION: bool = _as_bool(
    os.environ.get("HYDROPORTAL_ALLOW_DEMO_AUTH_IN_PRODUCTION"),
    default=False,
)

# ---------------------------------------------------------------------------
# Downstream Hydro application endpoints (defaults for local dev)
# ---------------------------------------------------------------------------

_DEFAULT_APPS = [
    {"app_id": "guard", "name": "HydroGuard", "base_url": "http://localhost:8001"},
    {"app_id": "design", "name": "HydroDesign", "base_url": "http://localhost:8002"},
    {"app_id": "lab", "name": "HydroLab", "base_url": "http://localhost:8003"},
    {"app_id": "edu", "name": "HydroEdu", "base_url": "http://localhost:8004"},
    {"app_id": "arena", "name": "HydroArena", "base_url": "http://localhost:8005"},
]

HYDRO_APPS: list[AppEndpoint] = [
    AppEndpoint(**app_def)
    for app_def in json.loads(
        os.environ.get("HYDROPORTAL_APPS", json.dumps(_DEFAULT_APPS))
    )
]

# Convenience: per-domain downstream URLs (overridable individually)
GUARD_UPSTREAM_URL: str = os.environ.get("HYDROPORTAL_GUARD_URL", "http://localhost:8001")
DESIGN_UPSTREAM_URL: str = os.environ.get("HYDROPORTAL_DESIGN_URL", "http://localhost:8002")
LAB_UPSTREAM_URL: str = os.environ.get("HYDROPORTAL_LAB_URL", "http://localhost:8003")
EDU_UPSTREAM_URL: str = os.environ.get("HYDROPORTAL_EDU_URL", "http://localhost:8004")
ARENA_UPSTREAM_URL: str = os.environ.get("HYDROPORTAL_ARENA_URL", "http://localhost:8005")

# ---------------------------------------------------------------------------
# Skill routing — maps skill name prefixes to downstream MCP service URLs
# ---------------------------------------------------------------------------

_DEFAULT_SKILL_ROUTES: dict[str, str] = {
    "guard": GUARD_UPSTREAM_URL,
    "design": DESIGN_UPSTREAM_URL,
    "lab": LAB_UPSTREAM_URL,
    "edu": EDU_UPSTREAM_URL,
    "arena": ARENA_UPSTREAM_URL,
}

SKILL_ROUTES: dict[str, str] = json.loads(
    os.environ.get("HYDROPORTAL_SKILL_ROUTES", json.dumps(_DEFAULT_SKILL_ROUTES))
)


def validate_security_settings() -> None:
    """Fail fast when unsafe defaults are used in production mode."""
    if IS_PRODUCTION and JWT_SECRET == DEFAULT_JWT_SECRET:
        raise RuntimeError(
            "HYDROPORTAL_JWT_SECRET must be set to a non-default value in production."
        )
    if IS_PRODUCTION and DEMO_AUTH_ENABLED and not ALLOW_DEMO_AUTH_IN_PRODUCTION:
        raise RuntimeError(
            "Demo auth is disabled in production by default. "
            "Set HYDROPORTAL_ALLOW_DEMO_AUTH_IN_PRODUCTION=true to override explicitly."
        )
