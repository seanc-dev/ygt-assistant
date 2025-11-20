# YGT Assistant / LucidWork — Repository Inventory

This document inventories the current repository and highlights which pieces are active for the LucidWork Hub/Workroom experience. It reflects the present code, not historical CoachFlow/Nylas-era components.

## Components Overview

- Backend API: FastAPI at `presentation/api/app.py` with routes for actions, Hub/brief data, workroom, WhatsApp, and connection flows.
- Core services: `core/` (triage engine, memory, embeddings manager, narrative memory, triage/action glue).
- Infra repos: `infra/` (in-memory and Supabase-backed repos; mailer integration; HTTP client wrappers).
- Adapters/providers: Microsoft Graph + Notion connectors under `services/` and `presentation/api/routes`; experimental Google router remains.
- Frontend: `web/` Next.js Pages app (Hub, Workroom, Review, Drafts, Connections, History, Chat, Settings).
- Shared UI: `shared-ui/` (design system/theme exports used by the web app).
- Database: `supabase/` schema + migrations (Postgres; `vector` extension present).
- Tests: `tests/` (pytest) and `llm_testing/` (evaluation utilities and scenarios).
- Tooling & Ops: `Dockerfile` (uvicorn FastAPI), `fly.toml` (Fly.io), `requirements.txt`, `pytest.ini`.

## Backend (API & Services)

- Entrypoint: `presentation/api/app.py` (FastAPI).
- Selected endpoints: OAuth for Notion (`/oauth/notion/*`), Microsoft Graph (`/connections/ms/*`), experimental Google (`/connections/google/*`), Hub data (`/api/brief/today`, `/api/schedule/today`, `/api/queue`), Workroom (`/workroom/*`), actions (`/actions/*`), WhatsApp webhook, health.
- Domain/services under `core/` include triage engine and memory layers.
- Utilities under `utils/` include sessions and crypto helpers.
- OpenAI integration: `openai_client.py` wraps GPT calls; uses `OPENAI_API_KEY` (stubs remain for local dev).

## Frontend (Next.js)

- `web/` (Next.js Pages) — Hub + Workroom UI; uses shared UI and calls the FastAPI backend via env-configured origin.
  - Frameworks: Next `15.5.3`, React `19.1.0`, TypeScript `5.6.3`.

## Database & Migrations (Supabase/Postgres)

- Base schema: `supabase/schema.sql` (includes `create extension if not exists vector` and app tables such as `tenants`, `connections`, `actions`, `audit_log`, `rules`, `tenant_settings`, workroom tables).
- Migrations: `supabase/migrations/*` include RLS enablement and user/client session tables.
- Infra clients: `infra/supabase/*` (e.g., `connections_repo.py`, `settings_repo.py`, `idempotency_repo.py`).
- Repo factories select Supabase or in-memory implementation based on env flags.

## Environment Configuration

- Central config: `settings.py` — toggles dev mode and feature flags (e.g., `USE_DB`, Graph live flags, translation/weather/news), loads `.env.local` then `.env`.
- Common envs: `OPENAI_API_KEY`, CORS origins, mailer token (Postmark), DB flags, OAuth client IDs/secrets for Notion/Microsoft/Google, WhatsApp webhook secrets.

## Dependencies & Versions

- Python: `fastapi`, `uvicorn`, `pydantic>=2`, `httpx`, `python-dotenv`, `cryptography`, `pyyaml`, `bcrypt`, `numpy` (see `requirements.txt`).
- Node (web): Next `15.5.3`, React `19.1.0`, Tailwind `3.4.x`, TypeScript `5.6.3`.

## Risky Couplings & Dead Code Candidates

- In-memory repos for production data — replace with durable Supabase/Postgres implementations.
- Experimental Google connector — keep isolated behind flags until hardened.

## Keep / Drop / Archive

- Keep
  - `presentation/api/`, `core/`, `infra/`, `shared-ui/`, `supabase/`, `tests/`, `llm_testing/`, `web/`.
- Archive (already done)
  - Legacy Nylas/EventKit assets remain only in `archive/`; ensure CI ignores them.
- Drop
  - None immediately; prefer feature flags and archival to minimize risk.

## Notes

- API runs via uvicorn per `Dockerfile` and exposes port 8000.
- Fly.io config present (`fly.toml`); GitHub Actions to be enabled for lint/tests/evals.
