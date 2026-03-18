"""Repository classes for HydroPortal database access."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from backend.db import db_session


class UserRepository:
    """CRUD operations for the users table."""

    @staticmethod
    def create(username: str, password_hash: str, role: str = "operator") -> dict[str, Any]:
        user_id = str(uuid.uuid4())
        with db_session() as conn:
            conn.execute(
                "INSERT INTO users (id, username, password_hash, role) VALUES (?, ?, ?, ?)",
                (user_id, username, password_hash, role),
            )
        return {"id": user_id, "username": username, "role": role}

    @staticmethod
    def get_by_username(username: str) -> dict[str, Any] | None:
        with db_session() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
        if row is None:
            return None
        return dict(row)

    @staticmethod
    def get_by_id(user_id: str) -> dict[str, Any] | None:
        with db_session() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
        if row is None:
            return None
        return dict(row)

    @staticmethod
    def update_last_login(user_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with db_session() as conn:
            conn.execute(
                "UPDATE users SET last_login = ? WHERE id = ?", (now, user_id)
            )

    @staticmethod
    def list_all() -> list[dict[str, Any]]:
        with db_session() as conn:
            rows = conn.execute("SELECT * FROM users ORDER BY created_at").fetchall()
        return [dict(r) for r in rows]


class AlertRepository:
    """CRUD operations for the alerts table."""

    @staticmethod
    def create(station_id: str, severity: str, message: str) -> int:
        with db_session() as conn:
            cursor = conn.execute(
                "INSERT INTO alerts (station_id, severity, message) VALUES (?, ?, ?)",
                (station_id, severity, message),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    @staticmethod
    def get_by_id(alert_id: int) -> dict[str, Any] | None:
        with db_session() as conn:
            row = conn.execute(
                "SELECT * FROM alerts WHERE id = ?", (alert_id,)
            ).fetchone()
        if row is None:
            return None
        return dict(row)

    @staticmethod
    def list_unacknowledged(limit: int = 100) -> list[dict[str, Any]]:
        with db_session() as conn:
            rows = conn.execute(
                "SELECT * FROM alerts WHERE acknowledged = 0 ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def list_by_station(station_id: str, limit: int = 100) -> list[dict[str, Any]]:
        with db_session() as conn:
            rows = conn.execute(
                "SELECT * FROM alerts WHERE station_id = ? ORDER BY created_at DESC LIMIT ?",
                (station_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def acknowledge(alert_id: int) -> bool:
        with db_session() as conn:
            cursor = conn.execute(
                "UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,)
            )
            return cursor.rowcount > 0


class StationRepository:
    """CRUD operations for the stations table."""

    @staticmethod
    def create(
        station_id: str,
        name: str,
        station_type: str | None = None,
        location: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        config_json = json.dumps(config) if config else None
        with db_session() as conn:
            conn.execute(
                "INSERT INTO stations (id, name, type, location, config) VALUES (?, ?, ?, ?, ?)",
                (station_id, name, station_type, location, config_json),
            )
        return {"id": station_id, "name": name, "type": station_type, "location": location}

    @staticmethod
    def get_by_id(station_id: str) -> dict[str, Any] | None:
        with db_session() as conn:
            row = conn.execute(
                "SELECT * FROM stations WHERE id = ?", (station_id,)
            ).fetchone()
        if row is None:
            return None
        result = dict(row)
        if result.get("config"):
            result["config"] = json.loads(result["config"])
        return result

    @staticmethod
    def list_all() -> list[dict[str, Any]]:
        with db_session() as conn:
            rows = conn.execute("SELECT * FROM stations ORDER BY name").fetchall()
        results = []
        for r in rows:
            d = dict(r)
            if d.get("config"):
                d["config"] = json.loads(d["config"])
            results.append(d)
        return results

    @staticmethod
    def update_status(station_id: str, status: str) -> bool:
        with db_session() as conn:
            cursor = conn.execute(
                "UPDATE stations SET status = ? WHERE id = ?", (status, station_id)
            )
            return cursor.rowcount > 0

    @staticmethod
    def delete(station_id: str) -> bool:
        with db_session() as conn:
            cursor = conn.execute(
                "DELETE FROM stations WHERE id = ?", (station_id,)
            )
            return cursor.rowcount > 0
