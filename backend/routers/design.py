"""HydroDesign proxy router — projects, schemes, compliance."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from backend import config
from backend.deps import get_current_user
from backend.routers._proxy import proxy_or_mock

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/design", tags=["design"])

# ---------------------------------------------------------------------------
# Demo data (fallback)
# ---------------------------------------------------------------------------

_PROJECTS = [
    {"project_id": "PRJ-001", "name": "南水北调东线二期", "status": "in_progress", "owner": "designer"},
    {"project_id": "PRJ-002", "name": "引江补汉工程", "status": "review", "owner": "designer"},
    {"project_id": "PRJ-003", "name": "环北部湾水资源配置", "status": "draft", "owner": "admin"},
]

_SCHEMES = [
    {"scheme_id": "SCH-A", "name": "方案A — 明渠方案", "score": 82.5},
    {"scheme_id": "SCH-B", "name": "方案B — 隧洞方案", "score": 78.1},
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/projects")
async def list_projects(user: dict = Depends(get_current_user)):
    """List design projects."""
    return await proxy_or_mock(
        upstream_url=config.DESIGN_UPSTREAM_URL,
        method="GET",
        path="/api/projects",
        mock_data=_PROJECTS,
    )


@router.get("/projects/{project_id}/schemes")
async def list_schemes(project_id: str, user: dict = Depends(get_current_user)):
    """List schemes for a project."""
    return await proxy_or_mock(
        upstream_url=config.DESIGN_UPSTREAM_URL,
        method="GET",
        path=f"/api/projects/{project_id}/schemes",
        mock_data=_SCHEMES,
    )


@router.post("/compliance/check")
async def check_compliance(
    body: dict,
    user: dict = Depends(get_current_user),
):
    """Run compliance check on a scheme."""
    mock_result = {
        "scheme_id": body.get("scheme_id", "unknown"),
        "compliant": True,
        "issues": [],
        "checked_rules": 24,
    }
    return await proxy_or_mock(
        upstream_url=config.DESIGN_UPSTREAM_URL,
        method="POST",
        path="/api/compliance/check",
        json_body=body,
        mock_data=mock_result,
    )
