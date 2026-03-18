"""WebSocket authentication tests — accepted / rejected connections."""

from __future__ import annotations

import json

import pytest
from starlette.testclient import TestClient

from backend.app import app
from backend.deps import issue_token


@pytest.fixture
def sync_client():
    return TestClient(app)


def test_ws_rejected_without_token(sync_client: TestClient):
    """WebSocket connection without token should be closed with code 4001."""
    with pytest.raises(Exception):
        with sync_client.websocket_connect("/ws/scada"):
            pass  # should not reach here


def test_ws_rejected_with_invalid_token(sync_client: TestClient):
    """WebSocket connection with an invalid JWT should be closed with 4003."""
    with pytest.raises(Exception):
        with sync_client.websocket_connect("/ws/scada?token=invalid.jwt.token"):
            pass


def test_ws_accepted_with_valid_token(sync_client: TestClient):
    """WebSocket with a valid JWT should be accepted and send SCADA frames."""
    token = issue_token("admin", "admin")
    with sync_client.websocket_connect(f"/ws/scada?token={token}") as ws:
        data = ws.receive_text()
        frame = json.loads(data)
        assert isinstance(frame, list)
        assert len(frame) == 5  # all 5 stations by default
        assert "station_id" in frame[0]
        assert "water_level" in frame[0]
        assert "flow_rate" in frame[0]
        assert "pressure" in frame[0]


def test_ws_station_filter(sync_client: TestClient):
    """When stations param is specified, only those stations are streamed."""
    token = issue_token("operator", "operator")
    with sync_client.websocket_connect(f"/ws/scada?token={token}&stations=ST-001,ST-003") as ws:
        data = ws.receive_text()
        frame = json.loads(data)
        assert isinstance(frame, list)
        assert len(frame) == 2
        station_ids = {f["station_id"] for f in frame}
        assert station_ids == {"ST-001", "ST-003"}
