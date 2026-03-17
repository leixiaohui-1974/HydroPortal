"""Unified gateway router — chat, skill execution, health, tools."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends

from backend.deps import get_current_user, get_app_registry
from backend.models import (
    ChatRequest,
    ChatResponse,
    HealthStatus,
    SkillRequest,
    SkillResponse,
    ToolInfo,
)

router = APIRouter(prefix="/api/gateway", tags=["gateway"])

# ---------------------------------------------------------------------------
# Routing heuristic: keyword -> app_id
# ---------------------------------------------------------------------------
_KEYWORD_MAP: dict[str, str] = {
    "station": "guard",
    "alert": "guard",
    "scada": "guard",
    "dispatch": "guard",
    "design": "design",
    "scheme": "design",
    "compliance": "design",
    "experiment": "lab",
    "paper": "lab",
    "literature": "lab",
    "course": "edu",
    "quiz": "edu",
    "contest": "arena",
    "leaderboard": "arena",
}


def _route_message(message: str) -> str:
    lower = message.lower()
    for kw, aid in _KEYWORD_MAP.items():
        if kw in lower:
            return aid
    return "guard"  # default


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
async def gateway_chat(
    req: ChatRequest,
    user: dict = Depends(get_current_user),
):
    """Unified chat endpoint — routes to appropriate app agent."""
    app_id = req.app_id or _route_message(req.message)
    registry = get_app_registry()
    endpoint = registry.get(app_id)

    if endpoint is None:
        return ChatResponse(
            reply=f"App '{app_id}' is not registered in the portal.",
            app_id=app_id,
        )

    # Try to forward to downstream; fall back to echo
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{endpoint.base_url}/api/chat",
                json={"message": req.message, "context": req.context},
            )
            data = resp.json()
            return ChatResponse(
                reply=data.get("reply", str(data)),
                app_id=app_id,
                tool_calls=data.get("tool_calls", []),
            )
    except Exception:
        return ChatResponse(
            reply=f"[{endpoint.name}] 服务暂不可达，请稍后重试。",
            app_id=app_id,
        )


@router.post("/skill", response_model=SkillResponse)
async def gateway_skill(
    req: SkillRequest,
    user: dict = Depends(get_current_user),
):
    """Execute a named skill across the ecosystem."""
    # Stub — in production this resolves the skill from the MCP tool registry
    return SkillResponse(
        result={"skill": req.skill_name, "params": req.params, "note": "skill execution stub"},
        status="ok",
    )


@router.get("/health", response_model=HealthStatus)
async def gateway_health():
    """Ping all installed apps and report health."""
    registry = get_app_registry()
    statuses: dict[str, str] = {}

    async with httpx.AsyncClient(timeout=3.0) as client:
        for app_id, endpoint in registry.items():
            try:
                resp = await client.get(f"{endpoint.base_url}/health")
                statuses[app_id] = "ok" if resp.status_code == 200 else f"http-{resp.status_code}"
            except Exception:
                statuses[app_id] = "unreachable"

    return HealthStatus(
        portal="ok",
        apps=statuses,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/tools", response_model=list[ToolInfo])
async def gateway_tools(user: dict = Depends(get_current_user)):
    """List all available MCP tools across installed apps."""
    registry = get_app_registry()
    tools: list[ToolInfo] = []

    # Predefined tool catalog (in production, discovered dynamically)
    _TOOL_CATALOG: dict[str, list[tuple[str, str]]] = {
        "guard": [
            ("guard.list_stations", "List all monitoring stations"),
            ("guard.get_alerts", "Get active alerts"),
            ("guard.create_dispatch", "Create a dispatch command"),
            ("guard.scada_query", "Query SCADA time-series data"),
        ],
        "design": [
            ("design.list_projects", "List design projects"),
            ("design.check_compliance", "Run compliance check on a scheme"),
        ],
        "lab": [
            ("lab.search_literature", "Search academic literature"),
            ("lab.run_experiment", "Run a simulation experiment"),
        ],
        "edu": [
            ("edu.list_courses", "List available courses"),
            ("edu.submit_quiz", "Submit quiz answers"),
        ],
        "arena": [
            ("arena.list_contests", "List active contests"),
            ("arena.submit_solution", "Submit a contest solution"),
        ],
    }

    for app_id in registry:
        for tool_name, desc in _TOOL_CATALOG.get(app_id, []):
            tools.append(ToolInfo(tool_name=tool_name, app_id=app_id, description=desc))

    return tools
