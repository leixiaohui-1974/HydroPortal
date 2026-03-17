"""WebSocket endpoint for real-time SCADA data streaming.

Generates simulated SCADA telemetry — water level, flow rate and pressure —
using sinusoidal curves with Gaussian noise.  Sends one JSON frame per second.
"""

from __future__ import annotations

import asyncio
import json
import math
import random
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["websocket"])

# ---------------------------------------------------------------------------
# Simulated station metadata
# ---------------------------------------------------------------------------

_STATION_IDS = ["ST-001", "ST-002", "ST-003", "ST-004", "ST-005"]


def _simulate_reading(station_id: str, t: float) -> dict:
    """Generate a single SCADA frame for *station_id* at time *t*."""
    idx = _STATION_IDS.index(station_id) if station_id in _STATION_IDS else 0
    phase = idx * 0.7

    water_level = 45.0 + 2.0 * math.sin(t / 30.0 + phase) + random.gauss(0, 0.1)
    flow_rate = 120.0 + 15.0 * math.sin(t / 45.0 + phase) + random.gauss(0, 1.0)
    pressure = 2.5 + 0.3 * math.sin(t / 60.0 + phase) + random.gauss(0, 0.02)

    return {
        "station_id": station_id,
        "timestamp": time.time(),
        "water_level": round(water_level, 3),
        "flow_rate": round(flow_rate, 3),
        "pressure": round(pressure, 4),
    }


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@router.websocket("/ws/scada")
async def scada_stream(websocket: WebSocket):
    """Stream simulated SCADA data.

    Query params:
        stations — comma-separated list of station IDs to subscribe to.
                   If omitted, all stations are streamed.
    """
    await websocket.accept()

    raw = websocket.query_params.get("stations", "")
    if raw:
        stations = [s.strip() for s in raw.split(",") if s.strip() in _STATION_IDS]
    else:
        stations = list(_STATION_IDS)

    try:
        while True:
            t = time.time()
            frame = [_simulate_reading(sid, t) for sid in stations]
            await websocket.send_text(json.dumps(frame))
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close()
