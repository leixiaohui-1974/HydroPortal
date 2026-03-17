"""HydroLab proxy router — experiments, literature, papers."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.deps import get_current_user

router = APIRouter(prefix="/api/lab", tags=["lab"])


@router.get("/experiments")
async def list_experiments(user: dict = Depends(get_current_user)):
    """List simulation experiments."""
    return [
        {"exp_id": "EXP-001", "name": "渠道非恒定流模拟", "status": "completed", "created_by": "admin"},
        {"exp_id": "EXP-002", "name": "闸门调度优化", "status": "running", "created_by": "operator"},
    ]


@router.get("/literature")
async def search_literature(q: str = "", user: dict = Depends(get_current_user)):
    """Search academic literature."""
    results = [
        {"title": "长距离调水工程冰期输水研究", "authors": "张三, 李四", "year": 2024},
        {"title": "智慧水网调度决策支持系统", "authors": "王五, 赵六", "year": 2025},
    ]
    if q:
        results = [r for r in results if q.lower() in r["title"].lower()]
    return results


@router.get("/papers")
async def list_papers(user: dict = Depends(get_current_user)):
    """List generated / managed papers."""
    return [
        {"paper_id": "PAP-001", "title": "基于知识图谱的水利工程设计规范检索", "status": "draft"},
    ]
