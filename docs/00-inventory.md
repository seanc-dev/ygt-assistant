# YGT Assistant — Repository Inventory

This document is an authoritative inventory of the current repository as of this cutover. It catalogs services, apps, shared libraries, database/migrations, environment, tooling, and highlights candidates to keep, deprecate, or archive for the WhatsApp-first POC.

## Components Overview

- Backend API: FastAPI app at `presentation/api/app.py` (serves OAuth/webhooks/actions; CORS configured via env).
- Core services: `core/` (conversation state, memory, embeddings manager, narrative memory, triage/action glue).
- Infra repos: `infra/` (memory and Supabase-backed repos; mailer integration; HTTP client wrappers).
- Adapters: `adapters/` (Notion adapter; EventKit calendar legacy dev adapter).
- Frontends:
  - `admin-ui/` Next.js Pages app (to be renamed to `web` for the slim control tower).
  - `client-ui/` Next.js Pages app (auth + dashboard; not required for POC).
  - `site/` Marketing site (Next.js; not required for POC).
- Shared UI: `shared-ui/` (design system/theme exports used by frontends).
- Database: `supabase/` schema + migrations (Postgres; `vector` extension present).
- Tests: `tests/` (pytest), `llm_testing/` (evaluation utilities and tests), `client-ui/tests` (Playwright e2e).
- Tooling & Ops: `Dockerfile` (uvicorn FastAPI), `fly.toml` (Fly.io), `requirements.txt`, `pytest.ini`.

## Backend (API & Services)

- Entrypoint: `presentation/api/app.py` (FastAPI).
- Selected endpoints (today): OAuth for Notion/Nylas; Nylas webhooks; actions executor; admin endpoints; health.
- Domain/services under `core/` include triage engine and memory layers.
- Utilities under `utils/` include sessions, crypto, CLI helpers.
- OpenAI integration: `openai_client.py` wraps GPT calls for CLI assistant; uses `OPENAI_API_KEY`.

## Frontends (Next.js)

- `admin-ui/` (Next.js Pages) — uses shared UI and points to the FastAPI backend via env origins.
  - Frameworks: Next `15.5.3`, React `19.1.0`, TypeScript `5.6.3`.
- `client-ui/` (Next.js Pages) — NextAuth, dashboard, integrations; not required for the WhatsApp-first POC.
  - Frameworks: Next `15.5.3`, React `19.1.0`, NextAuth `4.24.11`, Playwright `1.55.0` (e2e).
- `site/` (Next.js) — marketing; out of POC scope.

## Database & Migrations (Supabase/Postgres)

- Base schema: `supabase/schema.sql` (includes `create extension if not exists vector` and app tables like `tenants`, `connections`, `actions`, `audit_log`, `rules`, `tenant_settings`).
- Migrations: `supabase/migrations/*` include RLS enablement and user/client session tables.
- Infra clients: `infra/supabase/*` (e.g., `connections_repo.py`, `settings_repo.py`, `idempotency_repo.py`).
- Repos factory selects Supabase or in-memory implementation based on env flags.

## Environment Configuration

- Central config: `settings.py` — toggles dev mode and feature flags (e.g., `USE_DB`, SMTP enablement), loads `.env.local` then `.env`.
- Supabase service role key variable will standardize to `SUPABASE_API_SECRET` for this project’s conventions.
- Common envs: `OPENAI_API_KEY`, CORS origins, mailer token (Postmark), DB flags.

## Dependencies & Versions

- Python: `fastapi`, `uvicorn`, `pydantic>=2`, `httpx`, `python-dotenv`, `cryptography`, `pyyaml`, `bcrypt`, `numpy` (see `requirements.txt`).
- Node (admin-ui): Next `15.5.3`, React `19.1.0`, Tailwind `3.4.x`, TypeScript `5.6.3`.
- Node (client-ui): Next `15.5.3`, React `19.1.0`, NextAuth `4.24.11`, Tailwind `3.4.x`, Playwright `1.55.0`.

## Risky Couplings & Dead Code Candidates

- Nylas dependency in current OAuth/webhooks — plan to keep behind a flag while introducing Google APIs for POC.
- Duplicate Next.js apps (`admin-ui`, `client-ui`) — consolidate to one slim `web` for control tower; archive `client-ui`.
- `site/` marketing app — archive to reduce CI surface area.
- EventKit adapter under `adapters/` is legacy dev-only — retain for local experiments behind flags.

## Keep / Drop / Archive

- Keep
  - `presentation/api/`, `core/`, `infra/`, `adapters/` (selectively), `shared-ui/`, `supabase/`, `tests/`, `llm_testing/`.
  - Rename `admin-ui` → `web` and trim routes to minimal control tower.
- Archive (out of scope for POC)
  - `client-ui/`, `site/` under `archive/` with CI excluded.
- Drop
  - None immediately; prefer feature flags and archival to minimize risk.

## Notes

- API runs via uvicorn per `Dockerfile` and exposes port 8000.
- Fly.io config present (`fly.toml`); GitHub Actions not yet present — will be added for lint/tests/evals.
