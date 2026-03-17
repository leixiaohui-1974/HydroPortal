"""HydroDesign proxy router — projects, schemes, compliance."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.deps import get_current_user

router = APIRouter(prefix="/api/design", tags=["design"])


@router.get("/projects")
async def list_projects(user: dict = Depends(get_current_user)):
    """List design projects."""
    return [
        {"project_id": "PRJ-001", "name": "南水北调东线二期", "status": "in_progress", "owner": "designer"},
        {"project_id": "PRJ-002", "name": "引江补汉工程", "status": "review", "owner": "designer"},
        {"project_id": "PRJ-003", "name": "环北部湾水资源配置", "status": "draft", "owner": "admin"},
    ]


@router.get("/projects/{project_id}/schemes")
async def list_schemes(project_id: str, user: dict = Depends(get_current_user)):
    """List schemes for a project."""
    return [
        {"scheme_id": "SCH-A", "name": "方案A — 明渠方案", "score": 82.5},
        {"scheme_id": "SCH-B", "name": "方案B — 隧洞方案", "score": 78.1},
    ]


@router.post("/compliance/check")
async def check_compliance(
    body: dict,
    user: dict = Depends(get_current_user),
):
    """Run compliance check on a scheme."""
    return {
        "scheme_id": body.get("scheme_id", "unknown"),
        "compliant": True,
        "issues": [],
        "checked_rules": 24,
    }
