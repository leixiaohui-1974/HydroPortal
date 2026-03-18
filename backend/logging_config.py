"""Structured logging configuration for HydroPortal."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

from backend import config


class JSONFormatter(logging.Formatter):
    """Emit each log record as a single JSON object (one per line)."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging() -> None:
    """Configure root logger based on ``config.LOG_LEVEL``.

    In production (LOG_LEVEL != DEBUG) uses JSON formatting.
    In development (LOG_LEVEL == DEBUG) uses a human-readable format.
    """
    level = getattr(logging, config.LOG_LEVEL, logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers to avoid duplicate output on reload
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)

    if config.LOG_LEVEL == "DEBUG":
        # Developer-friendly plain text
        fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        # Structured JSON for production / staging
        fmt = JSONFormatter()

    console.setFormatter(fmt)
    root.addHandler(console)

    # Quieten noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
