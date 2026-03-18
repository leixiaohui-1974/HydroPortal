"""HydroLab proxy router — experiments, literature, papers."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from backend import config
from backend.deps import get_current_user
from backend.routers._proxy import proxy_or_mock

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/lab", tags=["lab"])

# ---------------------------------------------------------------------------
# Demo data (fallback)
# ---------------------------------------------------------------------------

_EXPERIMENTS = [
    {"exp_id": "EXP-001", "name": "渠道非恒定流模拟", "status": "completed", "created_by": "admin"},
    {"exp_id": "EXP-002", "name": "闸门调度优化", "status": "running", "created_by": "operator"},
]

_LITERATURE = [
    {"title": "长距离调水工程冰期输水研究", "authors": "张三, 李四", "year": 2024},
    {"title": "智慧水网调度决策支持系统", "authors": "王五, 赵六", "year": 2025},
]

_PAPERS = [
    {"paper_id": "PAP-001", "title": "基于知识图谱的水利工程设计规范检索", "status": "draft"},
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/experiments")
async def list_experiments(user: dict = Depends(get_current_user)):
    """List simulation experiments."""
    return await proxy_or_mock(
        upstream_url=config.LAB_UPSTREAM_URL,
        method="GET",
        path="/api/experiments",
        mock_data=_EXPERIMENTS,
    )


@router.get("/literature")
async def search_literature(q: str = "", user: dict = Depends(get_current_user)):
    """Search academic literature."""
    if q:
        mock = [r for r in _LITERATURE if q.lower() in r["title"].lower()]
    else:
        mock = _LITERATURE

    return await proxy_or_mock(
        upstream_url=config.LAB_UPSTREAM_URL,
        method="GET",
        path="/api/literature",
        params={"q": q} if q else None,
        mock_data=mock,
    )


@router.get("/papers")
async def list_papers(user: dict = Depends(get_current_user)):
    """List generated / managed papers."""
    return await proxy_or_mock(
        upstream_url=config.LAB_UPSTREAM_URL,
        method="GET",
        path="/api/papers",
        mock_data=_PAPERS,
    )
