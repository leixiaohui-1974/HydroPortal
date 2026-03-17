"""HydroMind Portal — FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend import config
from backend.deps import init_app_registry, get_app_registry
from backend.middleware.cors import add_cors
from backend.routers import gateway, auth, apps, guard, design, lab, edu, arena
from backend.ws import scada_stream


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # Discover installed Hydro apps
    init_app_registry()
    registry = get_app_registry()
    print(f"[HydroPortal] Registered {len(registry)} apps: {list(registry.keys())}")
    yield
    print("[HydroPortal] Shutting down.")


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
