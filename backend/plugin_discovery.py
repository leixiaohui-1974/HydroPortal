"""HydroMind plugin discovery for HydroPortal.

Discovers installed role modules from either:
1. installed ``hydromind-contracts`` entry points, or
2. sibling repositories in the current HydroMind workspace.
"""

from __future__ import annotations

import importlib
import logging
import os
import sys
from pathlib import Path
from typing import Any

from backend import config

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib

logger = logging.getLogger(__name__)

ROLE_TO_APP_ID = {
    "operator": "guard",
    "designer": "design",
    "researcher": "lab",
    "educator": "edu",
    "student": "edu",
    "contest": "arena",
}

MODULE_PREFIX_TO_APP_ID = {
    "hydroguard": "guard",
    "hydrodesign": "design",
    "hydrolab": "lab",
    "hydroedu": "edu",
    "hydroarena": "arena",
}

WORKSPACE_PROJECTS = {
    "HydroGuard": "guard",
    "HydroDesign": "design",
    "HydroLab": "lab",
    "HydroEdu": "edu",
    "HydroArena": "arena",
}


def get_workspace_root() -> Path:
    override = os.environ.get("HYDROMIND_WORKSPACE")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parents[2]


def _project_root_map() -> dict[str, Path]:
    workspace = get_workspace_root()
    return {name: workspace / name for name in WORKSPACE_PROJECTS}


def _ensure_import_paths() -> None:
    workspace = get_workspace_root()
    candidates = [workspace / "hydromind-contracts", *list(_project_root_map().values())]
    for path in candidates:
        if path.exists() and str(path) not in sys.path:
            sys.path.insert(0, str(path))


def _normalize_tools(role_instance: Any) -> list[dict[str, str]]:
    if hasattr(role_instance, "get_tools"):
        tools = role_instance.get_tools()
        if isinstance(tools, list):
            normalized = []
            for tool in tools:
                if isinstance(tool, dict) and tool.get("name"):
                    normalized.append(
                        {
                            "name": str(tool["name"]),
                            "description": str(tool.get("description", "")),
                        }
                    )
            if normalized:
                return normalized

    tool_names: list[str] = []
    if hasattr(role_instance, "get_mcp_tools"):
        value = role_instance.get_mcp_tools()
        if isinstance(value, list):
            tool_names = [str(item) for item in value]
    elif hasattr(role_instance, "get_config"):
        cfg = role_instance.get_config()
        items = getattr(cfg, "mcp_tools", [])
        if isinstance(items, list):
            tool_names = [str(item) for item in items]

    return [{"name": name, "description": ""} for name in tool_names if name]


def _normalize_name(role_instance: Any, fallback: str) -> str:
    for attr in ("get_display_name", "get_name"):
        if hasattr(role_instance, attr):
            value = getattr(role_instance, attr)()
            if value:
                return str(value)
    value = getattr(role_instance, "name", "")
    return str(value or fallback)


def _normalize_version(role_instance: Any) -> str:
    return str(getattr(role_instance, "version", "unknown"))


def _normalize_routing_hints(role_name: str, role_instance: Any) -> list[str]:
    hints: list[str] = [role_name]
    hints.extend(part for part in role_name.replace("_", " ").split() if part)

    if hasattr(role_instance, "get_skills"):
        value = role_instance.get_skills()
        if isinstance(value, list):
            hints.extend(str(item) for item in value)
    elif hasattr(role_instance, "get_config"):
        cfg = role_instance.get_config()
        skills = getattr(cfg, "skills", [])
        if isinstance(skills, list):
            hints.extend(str(item) for item in skills)

    hints.extend(tool["name"] for tool in _normalize_tools(role_instance))

    name = _normalize_name(role_instance, "")
    if name:
        hints.extend(name.lower().replace("(", " ").replace(")", " ").split())

    # Deduplicate while keeping order
    return list(dict.fromkeys(item.strip().lower() for item in hints if item and item.strip()))


def _configured_app_map() -> dict[str, config.AppEndpoint]:
    return {app.app_id: app for app in config.HYDRO_APPS}


def _build_endpoint(
    app_id: str,
    role_name: str,
    role_instance: Any,
    source: str,
) -> config.AppEndpoint:
    configured = _configured_app_map().get(app_id)
    if configured is None:
        configured = config.AppEndpoint(
            app_id=app_id,
            name=app_id,
            base_url=f"http://localhost:0",
        )
    return config.AppEndpoint(
        app_id=app_id,
        name=configured.name or _normalize_name(role_instance, configured.name),
        base_url=configured.base_url,
        enabled=configured.enabled,
        available_tools=[tool["name"] for tool in _normalize_tools(role_instance)],
        tool_catalog=_normalize_tools(role_instance),
        role_names=[role_name],
        routing_hints=_normalize_routing_hints(role_name, role_instance),
        source=source,
        version=_normalize_version(role_instance),
    )


def _merge_endpoint(existing: config.AppEndpoint, incoming: config.AppEndpoint) -> config.AppEndpoint:
    tool_names = list(dict.fromkeys([*existing.available_tools, *incoming.available_tools]))
    tool_catalog_map = {item["name"]: item for item in existing.tool_catalog}
    for item in incoming.tool_catalog:
        tool_catalog_map[item["name"]] = item
    role_names = list(dict.fromkeys([*existing.role_names, *incoming.role_names]))
    return config.AppEndpoint(
        app_id=existing.app_id,
        name=existing.name if existing.name != existing.app_id else incoming.name,
        base_url=existing.base_url,
        enabled=existing.enabled,
        available_tools=tool_names,
        tool_catalog=list(tool_catalog_map.values()),
        role_names=role_names,
        routing_hints=list(dict.fromkeys([*existing.routing_hints, *incoming.routing_hints])),
        source=existing.source if existing.source != "static" else incoming.source,
        version=existing.version if existing.version != "unknown" else incoming.version,
    )


def _register(
    registry: dict[str, config.AppEndpoint],
    app_id: str,
    role_name: str,
    role_instance: Any,
    source: str,
) -> None:
    endpoint = _build_endpoint(app_id, role_name, role_instance, source)
    if app_id in registry:
        registry[app_id] = _merge_endpoint(registry[app_id], endpoint)
    else:
        registry[app_id] = endpoint


def _discover_installed_role_modules() -> dict[str, Any]:
    _ensure_import_paths()
    try:
        from hydromind_contracts import discover_role_modules
    except ImportError:
        return {}
    try:
        return discover_role_modules()
    except Exception:
        logger.exception("Installed role-module discovery failed")
        return {}


def _parse_workspace_role_entry_points(pyproject_path: Path) -> dict[str, str]:
    if not pyproject_path.exists():
        return {}
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    return (
        data.get("project", {})
        .get("entry-points", {})
        .get("hydromind.roles", {})
    )


def _discover_workspace_role_modules() -> dict[str, Any]:
    _ensure_import_paths()
    discovered: dict[str, Any] = {}
    for project_name, project_path in _project_root_map().items():
        if not project_path.exists():
            continue
        entries = _parse_workspace_role_entry_points(project_path / "pyproject.toml")
        for role_name, target in entries.items():
            try:
                module_path, class_name = target.split(":", 1)
                module = importlib.import_module(module_path)
                role_cls = getattr(module, class_name)
                discovered[role_name] = role_cls()
            except Exception:
                logger.exception("Workspace role discovery failed for %s:%s", project_name, role_name)
    return discovered


def discover_hydromind_apps() -> dict[str, config.AppEndpoint]:
    registry: dict[str, config.AppEndpoint] = {}

    installed = _discover_installed_role_modules()
    for role_name, entry_point in installed.items():
        try:
            instance = entry_point.load() if hasattr(entry_point, "load") else entry_point
            app_id = ROLE_TO_APP_ID.get(role_name)
            if app_id:
                _register(registry, app_id, role_name, instance, "entry_point")
        except Exception:
            logger.exception("Failed to load installed role module: %s", role_name)

    workspace_roles = _discover_workspace_role_modules()
    for role_name, instance in workspace_roles.items():
        app_id = ROLE_TO_APP_ID.get(role_name)
        if app_id is None:
            module_name = instance.__class__.__module__.split(".", 1)[0]
            app_id = MODULE_PREFIX_TO_APP_ID.get(module_name)
        if app_id:
            _register(registry, app_id, role_name, instance, "workspace")

    return registry
