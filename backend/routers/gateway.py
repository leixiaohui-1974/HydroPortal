"""Unified gateway router — chat, skill execution, health, tools."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException

from backend import config
from backend.deps import get_current_user, get_app_registry
from backend.models import (
    ChatRequest,
    ChatResponse,
    HealthStatus,
    SkillRequest,
    SkillResponse,
    ToolInfo,
)

logger = logging.getLogger(__name__)

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


def _resolve_skill_url(skill_name: str) -> str | None:
    """Resolve a skill name to its downstream service URL.

    Skill names use dotted notation: ``<domain>.<action>``
    (e.g. ``guard.get_alerts``, ``design.check_compliance``).
    The prefix before the first dot is matched against the route table.
    """
    prefix = skill_name.split(".")[0] if "." in skill_name else skill_name
    return config.SKILL_ROUTES.get(prefix)


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
        logger.warning("Chat request for unregistered app: %s", app_id)
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
            logger.info("Chat forwarded to %s, status=%d", app_id, resp.status_code)
            return ChatResponse(
                reply=data.get("reply", str(data)),
                app_id=app_id,
                tool_calls=data.get("tool_calls", []),
            )
    except Exception:
        logger.warning("Downstream %s unreachable for chat", app_id, exc_info=True)
        return ChatResponse(
            reply=f"[{endpoint.name}] 服务暂不可达，请稍后重试。",
            app_id=app_id,
        )


@router.post("/skill", response_model=SkillResponse)
async def gateway_skill(
    req: SkillRequest,
    user: dict = Depends(get_current_user),
):
    """Execute a named skill across the ecosystem.

    Resolves *skill_name* via the skill route table and forwards the request
    to the downstream MCP service.  The downstream service is expected to
    expose a ``POST /api/skill`` endpoint that accepts ``{skill_name, params, role}``.
    """
    downstream_url = _resolve_skill_url(req.skill_name)
    if downstream_url is None:
        logger.warning("No route found for skill: %s", req.skill_name)
        raise HTTPException(
            status_code=404,
            detail=f"No downstream service registered for skill '{req.skill_name}'",
        )

    payload = {
        "skill_name": req.skill_name,
        "params": req.params,
        "role": user.get("role", ""),
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{downstream_url}/api/skill",
                json=payload,
            )
        if resp.status_code >= 400:
            logger.error(
                "Downstream skill error: %s returned %d", downstream_url, resp.status_code
            )
            raise HTTPException(
                status_code=resp.status_code,
                detail=resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
            )
        data = resp.json()
        logger.info("Skill '%s' executed successfully via %s", req.skill_name, downstream_url)
        return SkillResponse(
            result=data.get("result", data),
            status=data.get("status", "ok"),
        )
    except httpx.HTTPError as exc:
        logger.error("Skill '%s' downstream unreachable: %s", req.skill_name, exc)
        raise HTTPException(
            status_code=502,
            detail=f"Downstream service for '{req.skill_name}' is unreachable",
        ) from exc


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
