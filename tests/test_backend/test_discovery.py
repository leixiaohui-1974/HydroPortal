"""Plugin discovery tests for HydroPortal app registry."""

from __future__ import annotations

from backend import config
from backend.deps import get_app_registry, init_app_registry


def test_init_app_registry_prefers_dynamic_discovery(monkeypatch):
    discovered = {
        "guard": config.AppEndpoint(
            app_id="guard",
            name="HydroGuard",
            base_url="http://localhost:8001",
            available_tools=["station.collect_data"],
            routing_hints=["operator", "station.collect_data"],
            role_names=["operator"],
            source="workspace",
        )
    }
    monkeypatch.setattr("backend.deps.discover_hydromind_apps", lambda: discovered)

    init_app_registry()
    registry = get_app_registry()

    assert set(registry.keys()) == {"guard"}
    assert registry["guard"].source == "workspace"
    assert registry["guard"].available_tools == ["station.collect_data"]
    assert "operator" in registry["guard"].routing_hints


def test_init_app_registry_falls_back_to_static_config(monkeypatch):
    monkeypatch.setattr("backend.deps.discover_hydromind_apps", lambda: {})

    init_app_registry()
    registry = get_app_registry()

    expected = {app.app_id for app in config.HYDRO_APPS}
    assert expected.issubset(set(registry.keys()))
    assert all(registry[app_id].source == "static" for app_id in expected)
