"""Portal configuration — ports, enabled apps, auth settings."""

from __future__ import annotations

from pydantic import BaseModel


class AppEndpoint(BaseModel):
    """Descriptor for a downstream Hydro application."""

    app_id: str
    name: str
    base_url: str
    enabled: bool = True


# ---------------------------------------------------------------------------
# Default configuration values
# ---------------------------------------------------------------------------

PORTAL_HOST: str = "0.0.0.0"
PORTAL_PORT: int = 8000

JWT_SECRET: str = "hydroportal-dev-secret-change-in-production"
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

RATE_LIMIT_REQUESTS: int = 60
RATE_LIMIT_WINDOW_SECONDS: int = 60

# Downstream Hydro application endpoints (defaults for local dev)
HYDRO_APPS: list[AppEndpoint] = [
    AppEndpoint(app_id="guard", name="HydroGuard", base_url="http://localhost:8001"),
    AppEndpoint(app_id="design", name="HydroDesign", base_url="http://localhost:8002"),
    AppEndpoint(app_id="lab", name="HydroLab", base_url="http://localhost:8003"),
    AppEndpoint(app_id="edu", name="HydroEdu", base_url="http://localhost:8004"),
    AppEndpoint(app_id="arena", name="HydroArena", base_url="http://localhost:8005"),
]

CORS_ORIGINS: list[str] = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]
