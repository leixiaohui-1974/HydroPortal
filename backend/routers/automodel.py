"""Auto-modeling workbench router backed by local research artifacts."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends

from backend.deps import get_current_user

router = APIRouter(prefix="/api/automodel", tags=["automodel"])

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
_DADUHE_ROOT = _WORKSPACE_ROOT / "cases" / "daduhe"
_SOURCE_SELECTION_ROOT = _DADUHE_ROOT / "source_selection"
_PRODUCT_OUTPUT_ROOT = _SOURCE_SELECTION_ROOT / "product_outputs"
_LONGRUN_STATE = _WORKSPACE_ROOT / ".team" / "longrun" / "current.json"


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _summarize_inventory(source_inventory: dict[str, Any]) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for item in source_inventory.get("sources", [])[:8]:
        results.append(
            {
                "name": Path(item.get("path", "")).name or item.get("source_id", "unknown"),
                "role": item.get("role", "unknown"),
                "status": "authoritative" if item.get("exists") else "missing",
                "note": item.get("origin", "unknown"),
            }
        )
    return results


def _summarize_scope(control_mapping: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in control_mapping.get("mappings", [])[:10]:
        candidate = item.get("outlet_candidate") or {}
        evidence = item.get("evidence") or []
        raw_type = ""
        if evidence:
            raw_type = (
                evidence[0]
                .get("properties", {})
                .get("raw_row", {})
                .get("类型", "")
            )
        entity_type = "hydrology_station"
        if "雨量站" in raw_type:
            entity_type = "rain_gauge"
        elif "reservoir" in item.get("canonical_station_id", "") or "node" in item.get("canonical_station_id", ""):
            entity_type = "reservoir_or_node"

        decision_status = item.get("decision_status", "unknown")
        decision = "待复核"
        confidence = "不足"
        if decision_status == "proposed_authoritative":
            decision = "纳入主线"
            confidence = "较高"
        elif decision_status == "review_required":
            decision = "待复核"
            confidence = "不足"

        if entity_type == "rain_gauge":
            decision = "延后到面雨量阶段"
            confidence = "已明确"

        rows.append(
            {
                "name": candidate.get("name") or item.get("canonical_station_name", "unknown"),
                "type": entity_type,
                "decision": decision,
                "confidence": confidence,
                "decision_status": decision_status,
                "geometry_status": item.get("geometry_status", "unknown"),
                "evidence_count": str(len(item.get("evidence", []))),
                "score": str(item.get("score", "")),
            }
        )
    return rows


def _load_hm_watch() -> dict[str, Any]:
    try:
        result = subprocess.run(
            ["./hm", "watch", "--json"],
            cwd=_WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        )
    except Exception:
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


@router.get("/workbench")
async def get_workbench_snapshot(user: dict = Depends(get_current_user)):
    source_inventory = _load_json(_PRODUCT_OUTPUT_ROOT / "source_inventory.json", {})
    source_reliability = _load_json(_PRODUCT_OUTPUT_ROOT / "source_reliability.json", {})
    control_mapping = _load_json(_PRODUCT_OUTPUT_ROOT / "control_station_mapping.json", {})
    longrun_state = _load_json(_LONGRUN_STATE, {})
    hm_watch = _load_hm_watch()

    runtime_log = Path(longrun_state.get("log_file", "")) if longrun_state.get("log_file") else None
    latest_runtime_excerpt = None
    if runtime_log and runtime_log.exists():
        latest_runtime_excerpt = "\n".join(runtime_log.read_text(encoding="utf-8").splitlines()[-20:])

    station_candidates = source_reliability.get("station_candidates", [])
    review_required = [
        item.get("name", "unknown")
        for item in station_candidates
        if item.get("decision") == "raw_or_rejected"
    ]

    return {
        "project": {
            "name": "大渡河流域划分 MVP",
            "basin": "大渡河",
            "objective": "先完成流域划分输入收敛，再进入后续模拟与审查",
            "phase": "数据发现与空间建模",
            "currentWorkflow": "watershed_delineation",
            "blocker": "canonical artifact 仍未稳定落仓，运行管道待收口",
            "nextAction": "修复 native coder 的 workspace/output-root 对齐后，重跑 canonical 写入与审查",
        },
        "status_cards": [
            {"title": "当前阶段", "value": "数据发现", "tone": "blue"},
            {"title": "主线对象", "value": "干流水库 + 水文站", "tone": "green"},
            {"title": "待人工确认", "value": "、".join(review_required[:3]) or "无", "tone": "amber"},
            {"title": "延后处理", "value": "雨量站", "tone": "slate"},
        ],
        "data_sources": _summarize_inventory(source_inventory),
        "scope_rows": _summarize_scope(control_mapping),
        "workflow_steps": [
            {"name": "数据发现", "status": "done", "detail": "已能生成 source inventory / reliability"},
            {"name": "站点与 Outlet 规范化", "status": "active", "detail": "主线范围已清楚，canonical 落仓未完成"},
            {"name": "流域划分", "status": "pending", "detail": "等待 data pack 与 canonical 输入稳定"},
            {"name": "审查报告", "status": "pending", "detail": "待 workflow_run 产出后生成 review bundle"},
        ],
        "runtime_signals": [
            ["当前运行器", hm_watch.get("backend", "hm + agent-teams")],
            ["当前工作流", hm_watch.get("workflow", "未启动")],
            ["当前步骤", f"{hm_watch.get('current_step', '-')} / {hm_watch.get('total_steps', '-')}" if hm_watch else "未启动"],
            ["当前 step", hm_watch.get("step_name", "未知")],
            ["进度信号", hm_watch.get("progress_signal", "未知")],
            ["当前 session", longrun_state.get("session_id", "未启动")],
        ],
        "runtime": hm_watch,
        "latest_runtime_excerpt": latest_runtime_excerpt,
        "station_validation_report_path": str(_SOURCE_SELECTION_ROOT / "station_validation" / "station_validation_report.json"),
        "artifacts": {
            "source_inventory_path": str(_PRODUCT_OUTPUT_ROOT / "source_inventory.json"),
            "source_reliability_path": str(_PRODUCT_OUTPUT_ROOT / "source_reliability.json"),
            "control_station_mapping_path": str(_PRODUCT_OUTPUT_ROOT / "control_station_mapping.json"),
            "longrun_state_path": str(_LONGRUN_STATE),
        },
    }
