# Codebase Overview

## 🏗️ Architecture

LucidWork (working name) is a FastAPI backend paired with a single Next.js web app. The Hub surface highlights today’s plan, connection status, and a queued set of suggested actions; the Workroom provides a graph-inspired workspace for projects/tasks. Microsoft Graph is the primary mail/calendar provider, Notion OAuth is available for context, and Google connectors exist in an experimental router. LLM behavior is currently stubbed for local development.

### Core components

- **FastAPI backend** (`presentation/api/app.py` + `presentation/api/routes/`)
  - Connections: Microsoft Graph (`/connections/ms/*`), Notion (`/oauth/notion/*`), Google (experimental `/connections/google/*`)
  - Hub/brief data: `/api/brief/today`, `/api/schedule/today`, `/api/queue`, `/api/settings`, `/api/profile`
  - Actions: scan + approve/edit/skip/undo endpoints, queue helpers, WhatsApp webhook
  - Workroom: `/workroom/*` APIs for projects, tasks, comments, and graph navigation
- **Web app** (`web/`)
  - Pages for Hub, Workroom, Review, Drafts, Connections, History, Chat, Automations/Settings
  - Shared UI primitives come from `shared-ui`
- **Infra repos** (`infra/`)
  - In-memory defaults with Supabase/Postgres implementations selectable via env flags
- **Core services** (`core/`)
  - Triage engine, memory store/retrieval/writer, narrative memory
- **LLM testing** (`llm_testing/`)
  - Optional evaluation utilities and canned scenarios

## 📁 Project Structure

```
ygt-assistant/
├── presentation/api/            # FastAPI application and route modules
├── web/                         # Next.js web app (Hub + Workroom)
├── shared-ui/                   # Reusable React primitives
├── core/                        # Memory + triage services
├── services/                    # Provider shims (Graph/Notion/Google), LLM stubs, WhatsApp helpers
├── infra/                       # Repositories (memory and Supabase), mailer factory
├── supabase/                    # SQL schema + migrations
├── tests/                       # Pytest suite (API, services, memory)
├── llm_testing/                 # Optional evaluation harness
├── docs/                        # Documentation
├── settings.py                  # Environment configuration and feature flags
├── Dockerfile / fly.toml        # Fly.io deployment artifacts
└── requirements.txt             # Python dependencies
```

Notes:

- Supabase can be enabled with `USE_DB=true`; otherwise in-memory repositories are used.
- SMTP/Postmark helpers remain but email sending defaults to the Microsoft Graph provider when configured.

## 🔄 High-level flows

1) **Hub data**

```
/api/brief/today → weather/news + greeting
/api/schedule/today → calendar agenda
/api/queue → suggested actions (from /actions/scan + stored queue)
```

2) **Connections**

```
User → /connections/ms/oauth/start → callback → encrypted token storage
User → /oauth/notion/start → callback → Notion access token persisted
User → /connections/google/oauth/start → optional experimental Google flow
```

3) **Actions + Workroom**

```
/actions/scan → suggested approvals → approve/edit/skip/undo
/workroom/* → projects/tasks/comments for the Workroom surfaces
```

## 🌐 Web API (selected)

- `GET /health` → `{ "status": "ok" }`
- Connections: `/connections/ms/oauth/start|callback|status|disconnect`, `/oauth/notion/start|callback`
- Hub data: `/api/brief/today`, `/api/schedule/today`, `/api/queue`, `/api/settings`, `/api/profile`
- Actions: `/actions/scan`, `/actions/approve/{id}`, `/actions/edit/{id}`, `/actions/skip/{id}`, `/actions/undo/{id}`
- Email: `/email/drafts`, `/email/send/{draft_id}`
- Calendar helpers: `/calendar/plan-today`, `/calendar/reschedule`
- Workroom: `/workroom/projects`, `/workroom/tasks`, `/workroom/comments`, `/workroom/graph`
- WhatsApp: `/whatsapp/webhook` (GET verify, POST ingest)

## 🔐 Environment & Deployment

- Dev mode enabled by `DEV_MODE=true`; hardening kicks in when unset.
- Required secrets (typical): `ENCRYPTION_KEY`, `ADMIN_SECRET`, `MS_CLIENT_ID/MS_CLIENT_SECRET/MS_REDIRECT_URI`, `NOTION_CLIENT_ID/NOTION_CLIENT_SECRET/NOTION_REDIRECT_URI`; Supabase credentials when `USE_DB=true`.
- Deployment: Fly.io via `fly.toml` + `Dockerfile`; web app deployable separately (Vercel/Node host).

## 🧠 Core services

- **Triage engine** (`core/services/triage_engine.py`): rule-driven triage; emits suggested actions for `/actions/scan`.
- **Memory** (`core/memory_manager.py`, `core/store.py`): deterministic recall, with vector search disabled by default until pgvector is configured.

## 🧪 Testing

- Default suite: `pytest -q`
- LLM scenarios: `python -m llm_testing.runner --scenarios <path>` (optional)

## 🧰 Developer workflow

- Prefer TDD for API changes; add/update tests in `tests/api` or relevant packages.
- Keep provider selection env-driven; avoid reintroducing legacy Nylas/EventKit code paths.
- Update docs alongside endpoint or workflow changes (Hub/Workroom/Connections).
