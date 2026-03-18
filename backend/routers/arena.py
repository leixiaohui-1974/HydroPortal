"""HydroArena proxy router — contests, leaderboard, submissions."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from backend import config
from backend.deps import get_current_user
from backend.routers._proxy import proxy_or_mock

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/arena", tags=["arena"])

# ---------------------------------------------------------------------------
# Demo data (fallback)
# ---------------------------------------------------------------------------

_CONTESTS = [
    {
        "contest_id": "CTX-001",
        "name": "2026 全国水利算法大赛",
        "status": "active",
        "participants": 128,
        "deadline": "2026-06-30",
    },
    {
        "contest_id": "CTX-002",
        "name": "水网调度优化挑战赛",
        "status": "upcoming",
        "participants": 0,
        "deadline": "2026-09-01",
    },
]

_LEADERBOARD = [
    {"rank": 1, "username": "hydro_master", "score": 98.7},
    {"rank": 2, "username": "water_wizard", "score": 95.2},
    {"rank": 3, "username": "canal_pro", "score": 93.1},
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/contests")
async def list_contests(user: dict = Depends(get_current_user)):
    """List active contests."""
    return await proxy_or_mock(
        upstream_url=config.ARENA_UPSTREAM_URL,
        method="GET",
        path="/api/contests",
        mock_data=_CONTESTS,
    )


@router.get("/leaderboard/{contest_id}")
async def leaderboard(contest_id: str, user: dict = Depends(get_current_user)):
    """Get leaderboard for a contest."""
    return await proxy_or_mock(
        upstream_url=config.ARENA_UPSTREAM_URL,
        method="GET",
        path=f"/api/leaderboard/{contest_id}",
        mock_data=_LEADERBOARD,
    )


@router.post("/submit")
async def submit_solution(body: dict, user: dict = Depends(get_current_user)):
    """Submit a solution to a contest."""
    mock_result = {
        "submission_id": "SUB-001",
        "contest_id": body.get("contest_id", "CTX-001"),
        "status": "accepted",
        "score": 87.5,
        "rank": 42,
    }
    return await proxy_or_mock(
        upstream_url=config.ARENA_UPSTREAM_URL,
        method="POST",
        path="/api/submit",
        json_body=body,
        mock_data=mock_result,
    )
