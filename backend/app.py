"""HydroMind Portal — FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend import config
from backend.db import init_db
from backend.deps import init_app_registry, get_app_registry
from backend.logging_config import setup_logging
from backend.middleware.cors import add_cors
from backend.middleware.rate_limit import default_limiter
from backend.routers import gateway, auth, apps, guard, design, lab, edu, arena
from backend.ws import scada_stream

# Initialise structured logging before anything else
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # Initialize SQLite database tables
    init_db()
    logger.info("Database initialized.")
    # Discover installed Hydro apps
    init_app_registry()
    registry = get_app_registry()
    logger.info("Registered %d apps: %s", len(registry), list(registry.keys()))
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="HydroMind Portal",
    description=(
        "HydroPortal 水网门户 — Unified Web portal and API gateway for the "
        "HydroMind ecosystem. Routes requests to HydroGuard, HydroDesign, "
        "HydroLab, HydroEdu, and HydroArena."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware
add_cors(app)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Enforce per-client rate limiting using the token-bucket limiter."""
    client_ip = request.client.host if request.client else "unknown"
    if not default_limiter.check(client_ip):
        logger.warning("Rate limit exceeded for client %s", client_ip)
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."},
        )
    return await call_next(request)

# Routers
app.include_router(gateway.router)
app.include_router(auth.router)
app.include_router(apps.router)
app.include_router(guard.router)
app.include_router(design.router)
app.include_router(lab.router)
app.include_router(edu.router)
app.include_router(arena.router)
app.include_router(scada_stream.router)


@app.get("/", tags=["root"])
async def root():
    return {
        "service": "HydroMind Portal",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["root"])
async def health():
    return {"status": "ok", "service": "hydroportal"}
