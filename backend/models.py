"""Pydantic request / response models for HydroPortal."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    username: str
    role: str
    display_name: str


# ---------------------------------------------------------------------------
# Gateway
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    app_id: str | None = None  # if None, gateway decides routing
    context: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    reply: str
    app_id: str
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)


class SkillRequest(BaseModel):
    skill_name: str
    params: dict[str, Any] = Field(default_factory=dict)


class SkillResponse(BaseModel):
    result: Any
    status: str = "ok"


class HealthStatus(BaseModel):
    portal: str = "ok"
    apps: dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ToolInfo(BaseModel):
    tool_name: str
    app_id: str
    description: str = ""


# ---------------------------------------------------------------------------
# Apps
# ---------------------------------------------------------------------------

class AppInfo(BaseModel):
    app_id: str
    name: str
    version: str = "unknown"
    status: str = "unknown"
    base_url: str = ""
    available_tools: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Guard domain
# ---------------------------------------------------------------------------

class Station(BaseModel):
    station_id: str
    name: str
    lat: float = 0.0
    lon: float = 0.0
    status: str = "online"


class Alert(BaseModel):
    alert_id: str
    station_id: str
    level: str  # info / warning / critical
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False


class DispatchCommand(BaseModel):
    station_id: str
    command: str
    params: dict[str, Any] = Field(default_factory=dict)


class DispatchResult(BaseModel):
    dispatch_id: str
    status: str = "submitted"
    message: str = ""
