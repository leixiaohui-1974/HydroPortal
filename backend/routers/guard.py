"""HydroGuard proxy router — stations, alerts, dispatch."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from backend import config
from backend.deps import get_current_user
from backend.models import Alert, DispatchCommand, DispatchResult, Station
from backend.routers._proxy import proxy_or_mock

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/guard", tags=["guard"])

# ---------------------------------------------------------------------------
# Demo in-memory data (fallback when upstream is unavailable)
# ---------------------------------------------------------------------------

_STATIONS: list[dict] = [
    {"station_id": "ST-001", "name": "南水北调中线渠首", "lat": 32.68, "lon": 111.49, "status": "online"},
    {"station_id": "ST-002", "name": "丹江口水库", "lat": 32.54, "lon": 111.51, "status": "online"},
    {"station_id": "ST-003", "name": "陶岔渠首", "lat": 32.62, "lon": 111.67, "status": "warning"},
    {"station_id": "ST-004", "name": "沙河渡槽", "lat": 33.72, "lon": 112.54, "status": "online"},
    {"station_id": "ST-005", "name": "穿黄工程", "lat": 34.91, "lon": 113.66, "status": "offline"},
]

_ALERTS: list[dict] = [
    {
        "alert_id": "ALT-001",
        "station_id": "ST-003",
        "level": "warning",
        "message": "水位超过预警值 0.3m",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "acknowledged": False,
    },
    {
        "alert_id": "ALT-002",
        "station_id": "ST-005",
        "level": "critical",
        "message": "通信中断超过 30 分钟",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "acknowledged": False,
    },
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/stations")
async def list_stations(user: dict = Depends(get_current_user)):
    """List all monitoring stations."""
    data = await proxy_or_mock(
        upstream_url=config.GUARD_UPSTREAM_URL,
        method="GET",
        path="/api/stations",
        mock_data=_STATIONS,
    )
    return data


@router.get("/alerts")
async def get_alerts(user: dict = Depends(get_current_user)):
    """Get active alerts."""
    mock = [a for a in _ALERTS if not a.get("acknowledged")]
    data = await proxy_or_mock(
        upstream_url=config.GUARD_UPSTREAM_URL,
        method="GET",
        path="/api/alerts",
        mock_data=mock,
    )
    return data


@router.post("/alerts/{alert_id}/ack")
async def acknowledge_alert(alert_id: str, user: dict = Depends(get_current_user)):
    """Acknowledge an alert."""
    mock_result = {"status": "not_found", "alert_id": alert_id}
    for a in _ALERTS:
        if a["alert_id"] == alert_id:
            a["acknowledged"] = True
            mock_result = {"status": "acknowledged", "alert_id": alert_id}
            break

    data = await proxy_or_mock(
        upstream_url=config.GUARD_UPSTREAM_URL,
        method="POST",
        path=f"/api/alerts/{alert_id}/ack",
        mock_data=mock_result,
        fallback_on_http_error=False,
    )
    return data


@router.post("/dispatch")
async def create_dispatch(cmd: DispatchCommand, user: dict = Depends(get_current_user)):
    """Create a dispatch command to a station."""
    dispatch_id = f"DSP-{uuid.uuid4().hex[:8].upper()}"
    mock_result = {
        "dispatch_id": dispatch_id,
        "status": "submitted",
        "message": f"Dispatch '{cmd.command}' sent to station {cmd.station_id}",
    }

    data = await proxy_or_mock(
        upstream_url=config.GUARD_UPSTREAM_URL,
        method="POST",
        path="/api/dispatch",
        json_body={"station_id": cmd.station_id, "command": cmd.command, "params": cmd.params},
        mock_data=mock_result,
        fallback_on_http_error=False,
    )
    return data
