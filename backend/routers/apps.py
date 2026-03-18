"""App discovery router — list installed Hydro applications and their status."""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Depends

from backend.deps import get_app_registry, get_current_user
from backend.models import AppInfo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/apps", tags=["apps"])


@router.get("/list", response_model=list[AppInfo])
async def list_apps(user: dict = Depends(get_current_user)):
    """Discover installed Hydro applications."""
    registry = get_app_registry()
    results: list[AppInfo] = []
    for app_id, endpoint in registry.items():
        results.append(
            AppInfo(
                app_id=app_id,
                name=endpoint.name,
                base_url=endpoint.base_url,
                status="registered",
            )
        )
    return results


@router.get("/{app_id}/status", response_model=AppInfo)
async def app_status(app_id: str, user: dict = Depends(get_current_user)):
    """Check whether a specific app service is running."""
    registry = get_app_registry()
    endpoint = registry.get(app_id)
    if endpoint is None:
        logger.warning("Status check for unknown app: %s", app_id)
        return AppInfo(app_id=app_id, name=app_id, status="not_found")

    status_str = "unreachable"
    version = "unknown"
    tools: list[str] = []

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{endpoint.base_url}/health")
            if resp.status_code == 200:
                data = resp.json()
                status_str = "online"
                version = data.get("version", version)
                tools = data.get("tools", tools)
            else:
                status_str = f"http-{resp.status_code}"
    except Exception:
        logger.info("App %s is unreachable at %s", app_id, endpoint.base_url)

    return AppInfo(
        app_id=app_id,
        name=endpoint.name,
        version=version,
        status=status_str,
        base_url=endpoint.base_url,
        available_tools=tools,
    )
