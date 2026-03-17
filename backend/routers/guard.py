"""HydroGuard proxy router — stations, alerts, dispatch."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from backend.deps import get_current_user
from backend.models import Alert, DispatchCommand, DispatchResult, Station

router = APIRouter(prefix="/api/guard", tags=["guard"])

# ---------------------------------------------------------------------------
# Demo in-memory data
# ---------------------------------------------------------------------------

_STATIONS: list[Station] = [
    Station(station_id="ST-001", name="南水北调中线渠首", lat=32.68, lon=111.49, status="online"),
    Station(station_id="ST-002", name="丹江口水库", lat=32.54, lon=111.51, status="online"),
    Station(station_id="ST-003", name="陶岔渠首", lat=32.62, lon=111.67, status="warning"),
    Station(station_id="ST-004", name="沙河渡槽", lat=33.72, lon=112.54, status="online"),
    Station(station_id="ST-005", name="穿黄工程", lat=34.91, lon=113.66, status="offline"),
]

_ALERTS: list[Alert] = [
    Alert(
        alert_id="ALT-001",
        station_id="ST-003",
        level="warning",
        message="水位超过预警值 0.3m",
        timestamp=datetime.now(timezone.utc),
    ),
    Alert(
        alert_id="ALT-002",
        station_id="ST-005",
        level="critical",
        message="通信中断超过 30 分钟",
        timestamp=datetime.now(timezone.utc),
    ),
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/stations", response_model=list[Station])
async def list_stations(user: dict = Depends(get_current_user)):
    """List all monitoring stations."""
    return _STATIONS


@router.get("/alerts", response_model=list[Alert])
async def get_alerts(user: dict = Depends(get_current_user)):
    """Get active alerts."""
    return [a for a in _ALERTS if not a.acknowledged]


@router.post("/alerts/{alert_id}/ack")
async def acknowledge_alert(alert_id: str, user: dict = Depends(get_current_user)):
    """Acknowledge an alert."""
    for a in _ALERTS:
        if a.alert_id == alert_id:
            a.acknowledged = True
            return {"status": "acknowledged", "alert_id": alert_id}
    return {"status": "not_found", "alert_id": alert_id}


@router.post("/dispatch", response_model=DispatchResult)
async def create_dispatch(cmd: DispatchCommand, user: dict = Depends(get_current_user)):
    """Create a dispatch command to a station."""
    dispatch_id = f"DSP-{uuid.uuid4().hex[:8].upper()}"
    return DispatchResult(
        dispatch_id=dispatch_id,
        status="submitted",
        message=f"Dispatch '{cmd.command}' sent to station {cmd.station_id}",
    )
