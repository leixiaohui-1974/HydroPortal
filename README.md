# HydroPortal - 水网门户

Unified Web portal for the **HydroMind** ecosystem. HydroPortal provides a single entry point for all Hydro applications — monitoring, design, research, education, and competition — through a modern React frontend and a FastAPI gateway backend.

## Features

- **Unified Gateway** — single API surface routing to HydroGuard, HydroDesign, HydroLab, HydroEdu, HydroArena
- **Role-Based Access** — JWT authentication with admin / designer / operator roles
- **Real-Time SCADA** — WebSocket streaming of station telemetry data
- **App Discovery** — automatically detects installed Hydro applications
- **Rate Limiting** — token-bucket rate limiter to protect backend services
- **Responsive UI** — React + TailwindCSS with dynamic sidebar based on installed apps

## Quick Start

### Backend

```bash
pip install -e ".[dev]"
uvicorn backend.app:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
cd docker
docker compose up -d
```

## Architecture

```
Browser  -->  React (Vite)  -->  FastAPI Gateway  -->  HydroGuard / HydroDesign / ...
                                      |
                                 WebSocket (SCADA)
```

## Demo Credentials

| Username  | Password  | Role     |
|-----------|-----------|----------|
| admin     | admin123  | admin    |
| designer  | design123 | designer |
| operator  | oper123   | operator |

## License

MIT
