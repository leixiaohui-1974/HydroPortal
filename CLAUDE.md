# HydroPortal - 水网门户

Unified Web portal for the HydroMind ecosystem.

## Architecture

- **backend/**: FastAPI application serving as a unified gateway to all Hydro application repos
- **frontend/**: React + Vite + TailwindCSS with role-based dynamic panels
- **tests/**: pytest-based backend tests using httpx TestClient
- **docker/**: Container definitions for deployment

## Development

### Backend
```bash
pip install -e ".[dev]"
uvicorn backend.app:app --reload --port 8000
```

### Frontend
```bash
cd frontend && npm install && npm run dev
```

### Tests
```bash
pytest tests/
```

## Key Design Decisions

- Gateway pattern: all client requests go through `/api/gateway/*` and are routed to the appropriate Hydro app
- JWT-based auth with role-based access (admin, designer, operator)
- WebSocket streaming for real-time SCADA data
- Each Hydro app (Guard, Design, Lab, Edu, Arena) has its own proxy router
- App discovery via entry_points for plugin-style architecture
- Token bucket rate limiting per client
