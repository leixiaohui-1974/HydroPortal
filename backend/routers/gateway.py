"""Unified gateway router — chat, skill execution, health, tools."""

from __future__ import annotations

import logging
import re
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


def _read_response_payload(resp: httpx.Response):
    try:
        return resp.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail="Downstream service returned an invalid JSON payload.",
        ) from exc


def _read_error_detail(resp: httpx.Response):
    content_type = resp.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            return resp.json()
        except ValueError:
            pass
    text = resp.text.strip()
    return text or f"Downstream service returned HTTP {resp.status_code}"

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


def _find_registry_app_by_message(message: str) -> str | None:
    registry = get_app_registry()
    lower = message.lower()
    message_tokens = set(re.findall(r"[a-z0-9]+", lower))
    best_app_id: str | None = None
    best_score = 0

    for app_id, endpoint in registry.items():
        candidates = [app_id, endpoint.name.lower(), *endpoint.role_names, *endpoint.routing_hints]
        for hint in candidates:
            token = str(hint).strip().lower()
            if len(token) < 3:
                continue
            parts = [part for part in re.split(r"[^a-z0-9]+", token) if len(part) >= 3]
            if not parts:
                continue
            if len(parts) == 1:
                matched = parts[0] in message_tokens or parts[0] in lower
                score = len(parts[0])
            else:
                matched = all(part in message_tokens or part in lower for part in parts)
                score = sum(len(part) for part in parts)
            if matched and score > best_score:
                best_app_id = app_id
                best_score = score

    return best_app_id


def _route_message(message: str) -> str:
    registry_match = _find_registry_app_by_message(message)
    if registry_match:
        return registry_match
    lower = message.lower()
    for kw, aid in _KEYWORD_MAP.items():
        if kw in lower:
            return aid
    return "guard"  # default


def _resolve_skill_endpoint(skill_name: str):
    """Resolve a skill name to its downstream app endpoint.

    Skill names use dotted notation: ``<domain>.<action>``
    (e.g. ``guard.get_alerts``, ``design.check_compliance``).
    Prefer discovered tool metadata, then app-id prefix fallback, then static routes.
    """
    registry = get_app_registry()
    normalized = skill_name.strip().lower()

    for endpoint in registry.values():
        for item in endpoint.tool_catalog:
            if item.get("name", "").strip().lower() == normalized:
                return endpoint

    prefix = normalized.split(".")[0] if "." in normalized else normalized
    endpoint = registry.get(prefix)
    if endpoint is not None:
        return endpoint

    downstream_url = config.SKILL_ROUTES.get(prefix)
    if downstream_url is None:
        return None

    for endpoint in registry.values():
        if endpoint.base_url == downstream_url:
            return endpoint
    return type("FallbackEndpoint", (), {"app_id": prefix, "base_url": downstream_url, "name": prefix})()


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
            if resp.status_code >= 400:
                if resp.status_code >= 500:
                    logger.warning(
                        "Chat downstream %s returned %d; using unavailable fallback",
                        app_id,
                        resp.status_code,
                    )
                    return ChatResponse(
                        reply=f"[{endpoint.name}] 服务暂不可达，请稍后重试。",
                        app_id=app_id,
                    )
                logger.warning(
                    "Chat downstream %s returned %d",
                    app_id,
                    resp.status_code,
                )
                raise HTTPException(
                    status_code=502,
                    detail={
                        "app_id": app_id,
                        "downstream_status": resp.status_code,
                        "detail": _read_error_detail(resp),
                    },
                )
            try:
                data = _read_response_payload(resp)
            except HTTPException:
                logger.warning(
                    "Chat downstream %s returned invalid JSON; using unavailable fallback",
                    app_id,
                )
                return ChatResponse(
                    reply=f"[{endpoint.name}] 服务暂不可达，请稍后重试。",
                    app_id=app_id,
                )
            logger.info("Chat forwarded to %s, status=%d", app_id, resp.status_code)
            return ChatResponse(
                reply=data.get("reply", str(data)),
                app_id=app_id,
                tool_calls=data.get("tool_calls", []),
            )
    except HTTPException:
        raise
    except httpx.HTTPError:
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
    endpoint = _resolve_skill_endpoint(req.skill_name)
    if endpoint is None:
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
                f"{endpoint.base_url}/api/skill",
                json=payload,
            )
        if resp.status_code >= 400:
            logger.error(
                "Downstream skill error: %s returned %d", endpoint.base_url, resp.status_code
            )
            raise HTTPException(
                status_code=resp.status_code,
                detail=_read_error_detail(resp),
            )
        data = _read_response_payload(resp)
        logger.info("Skill '%s' executed successfully via %s", req.skill_name, endpoint.base_url)
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

    for app_id, endpoint in registry.items():
        for item in endpoint.tool_catalog:
            tool_name = item.get("name", "")
            if not tool_name:
                continue
            tools.append(
                ToolInfo(
                    tool_name=tool_name,
                    app_id=app_id,
                    description=item.get("description", ""),
                )
            )

    return tools
