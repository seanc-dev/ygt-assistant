# Quick Reference Guide

This guide captures the fastest way to work with the current LucidWork codebase (FastAPI backend + Next.js web app).

## Run locally

```bash
python -m pip install -r requirements.txt
PYTHONPATH=. uvicorn presentation.api.app:app --reload --port 8000

cd web
npm install
npm run dev
```

Visit `http://localhost:3001/hub` (Hub) or `http://localhost:3001/workroom` (Workroom).

## Core endpoints to know

- Health: `GET /health`
- Connections: `GET /connections/ms/oauth/start`, `GET /connections/ms/status`, `GET /oauth/notion/start`
- Hub data: `GET /api/brief/today`, `GET /api/schedule/today`, `GET /api/queue`, `GET /api/settings`, `GET /api/profile`
- Actions: `POST /actions/scan`, `POST /actions/approve/{id}`, `POST /actions/edit/{id}`, `POST /actions/skip/{id}`, `POST /actions/undo/{id}`
- Workroom: `GET/POST /workroom/projects`, `/workroom/tasks`, `/workroom/comments`, `/workroom/graph`
- Chat/stand‑in: `POST /chat`
- WhatsApp: `GET|POST /whatsapp/webhook` (stubbed in dev)

## Environment defaults

Create `.env.local` in the repo root (see `README.md` for full list). Key values:

```
DEV_MODE=true
USE_DB=false
USE_MOCK_GRAPH=true
MS_CLIENT_ID=...
MS_CLIENT_SECRET=...
MS_REDIRECT_URI=http://localhost:8000/connections/ms/oauth/callback
NOTION_CLIENT_ID=...
NOTION_CLIENT_SECRET=...
NOTION_REDIRECT_URI=http://localhost:8000/oauth/notion/callback
ADMIN_SECRET= # generated automatically in DEV_MODE
ENCRYPTION_KEY= # generated automatically in DEV_MODE
```

## TDD hints

- Add/modify tests beside the feature (e.g., `tests/api` for API contracts, `tests/core` for memory/triage logic, `tests/web` for utilities when present).
- Prefer deterministic fixtures for Hub (`/api/brief/today`, `/api/schedule/today`, `/api/queue`) and Workroom endpoints so pages render during local dev.
- Keep provider selection env-driven; avoid reintroducing Nylas/EventKit strings in live code.

## Troubleshooting

- Missing admin secret or encryption key: set `DEV_MODE=true` locally to auto-generate; set real secrets in staging/prod.
- OAuth hangs: confirm redirect URIs match env values and that `ADMIN_UI_ORIGIN`/`CLIENT_UI_ORIGIN` allow your web host.
- Hub shows empty state: ensure `/api/queue` and `/api/schedule/today` return 200 (backend running on port 8000).
