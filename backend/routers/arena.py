"""HydroArena proxy router — contests, leaderboard, submissions."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.deps import get_current_user

router = APIRouter(prefix="/api/arena", tags=["arena"])


@router.get("/contests")
async def list_contests(user: dict = Depends(get_current_user)):
    """List active contests."""
    return [
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


@router.get("/leaderboard/{contest_id}")
async def leaderboard(contest_id: str, user: dict = Depends(get_current_user)):
    """Get leaderboard for a contest."""
    return [
        {"rank": 1, "username": "hydro_master", "score": 98.7},
        {"rank": 2, "username": "water_wizard", "score": 95.2},
        {"rank": 3, "username": "canal_pro", "score": 93.1},
    ]


@router.post("/submit")
async def submit_solution(body: dict, user: dict = Depends(get_current_user)):
    """Submit a solution to a contest."""
    return {
        "submission_id": "SUB-001",
        "contest_id": body.get("contest_id", "CTX-001"),
        "status": "accepted",
        "score": 87.5,
        "rank": 42,
    }
