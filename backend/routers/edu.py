"""HydroEdu proxy router — courses, quizzes, progress."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.deps import get_current_user

router = APIRouter(prefix="/api/edu", tags=["edu"])


@router.get("/courses")
async def list_courses(user: dict = Depends(get_current_user)):
    """List available courses."""
    return [
        {"course_id": "CRS-001", "name": "水力学基础", "modules": 12, "difficulty": "beginner"},
        {"course_id": "CRS-002", "name": "水工建筑物设计", "modules": 8, "difficulty": "intermediate"},
        {"course_id": "CRS-003", "name": "水利工程调度运行", "modules": 10, "difficulty": "advanced"},
    ]


@router.get("/courses/{course_id}/progress")
async def course_progress(course_id: str, user: dict = Depends(get_current_user)):
    """Get user's progress in a course."""
    return {
        "course_id": course_id,
        "username": user["username"],
        "completed_modules": 4,
        "total_modules": 12,
        "score": 85.0,
    }


@router.post("/quizzes/submit")
async def submit_quiz(body: dict, user: dict = Depends(get_current_user)):
    """Submit quiz answers and get score."""
    return {
        "quiz_id": body.get("quiz_id", "Q-001"),
        "score": 90,
        "total": 100,
        "passed": True,
    }
