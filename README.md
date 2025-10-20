YGT Assistant

Intent

- WhatsApp-first personal assistant with a calm web “control tower”.
- LLM-first flows: propose actions (approve/edit/skip) with undo and history.
- Multi-level memory core (episodic, semantic, procedural, narrative).
- Direct Google integrations (Gmail/Calendar) behind provider abstractions.

High-level architecture

- Backend: FastAPI (`presentation/api`) with modular routers and request-id middleware.
- Web: Next.js (pages) in `web/`, React 19, shared UI in `shared-ui`.
- DB: Postgres (Supabase), optional `pgvector` for semantic recall.
- Services: provider registry delegates to selected implementations by env.
- Testing/dev: in-memory stores and chat stand‑in endpoint until WhatsApp is live.

Key features

- Approvals: `/actions/scan` → list of low-risk actions; Approve/Edit/Skip/Undo.
- Drafts: create/send drafts; WhatsApp cards supported when Meta is enabled.
- Calendar: plan-today and reschedule flows (provider-backed).
- Core memory: deterministic recall; vectors off by default.
- Connections: Google OAuth (store encrypted tokens in Supabase).

Repo layout

- `presentation/api`: FastAPI app, middleware, routes, in-memory state.
- `services`: provider shims, Google provider scaffolding, LLM stubs, WhatsApp client.
- `core`: memory store/retrieval/writer/policy/glue.
- `supabase/migrations`: idempotent SQL migrations (oauth_tokens, profiles, core tables).
- `web`: Next.js app (pages). Chat stand‑in at `/chat`.
- `shared-ui`: small UI kit published via workspace alias `@ygt-assistant/ui`.
- `docs`: reference docs and inventory/cutover plans.

Prerequisites

- Python 3.11+; Node 18+; Supabase CLI (optional for DB push).
- A Supabase project (optional during POC with in‑memory stores).

Environment
Create `.env.local` at repo root:

```
# Core
DEV_MODE=true
CORE_ENABLE_VECTORS=false

# Providers
PROVIDER_EMAIL=google
PROVIDER_CAL=google

# API origins
WEB_ORIGIN=http://localhost:3001
ADMIN_UI_ORIGIN=http://localhost:3001
CLIENT_UI_ORIGIN=http://localhost:3001

# DB (optional; set USE_DB=true to enable)
USE_DB=false
SUPABASE_URL=
SUPABASE_API_SECRET=

# Google OAuth
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REDIRECT_URI=http://localhost:8000/connections/google/oauth/callback

# WhatsApp (Meta) — optional
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=

# Secrets (dev auto-generates if unset)
ADMIN_EMAIL=admin@example.com
ADMIN_SECRET=
ENCRYPTION_KEY=

# Web
NEXT_PUBLIC_ADMIN_API_BASE=http://localhost:8000
NEXT_PUBLIC_CLIENT_APP_URL=http://localhost:3001
```

First run (local)
Backend (FastAPI):

```
python -m pip install -r requirements.txt
PYTHONPATH=. uvicorn presentation.api.app:app --reload --port 8000
```

Web (Next.js):

```
cd web
npm install
npm run dev  # serves on http://localhost:3001
```

Smoke test:

```
curl http://localhost:8000/health
curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{"text":"scan"}'
open http://localhost:3001/chat
```

Supabase migrations (optional)

- CLI path:

```
supabase login
supabase link --project-ref <your-ref>
supabase db push --yes
```

Google connections

```
open "http://localhost:8000/connections/google/oauth/start?user_id=local-user"
curl "http://localhost:8000/connections/google/status?user_id=local-user"
```

Make targets

```
make status             # provider + DB flags
make db-migrate         # applies SQL with SUPABASE_DB_URL
make connect-google USER_ID=local-user
make test-gmail USER_ID=local-user
make test-calendar USER_ID=local-user
```

API surface (selected)

- WhatsApp webhook verify/handler: `/whatsapp/webhook` (GET/POST)
- Actions: `/actions/scan`, `/actions/approve/{id}`, `/actions/edit/{id}`, `/actions/skip/{id}`, `/actions/undo/{id}`
- Email: `/email/drafts`, `/email/send/{draft_id}`, `/drafts`
- Calendar: `/calendar/plan-today`, `/calendar/reschedule`
- Core memory: `/core/context`, `/core/notes`, `/core/preview`
- Chat stand‑in: `/chat` (scan/approve/skip text interface)
- Connections (Google): `/connections/google/oauth/start|callback|status|disconnect`

Design principles

- Calm UI: one primary action per page, keyboard shortcuts, undo, history.
- Safety: request-id tracing; dev stubs avoid leaking secrets; no logging of message bodies or tokens.
- Modularity: providers behind clean interfaces; env‑driven selection; feature flags.

Troubleshooting

- Chat hangs in web: verify backend `/chat` returns 200; see terminal for dev server port (3001).
- Module not found or hook errors: ensure `web/next.config.js` transpiles `@ygt-assistant/ui` and aliases React to `web/node_modules`.
- ADMIN_SECRET error on startup: `.env.local` or `DEV_MODE=true` (dev auto-generates safe values).

Roadmap

- Implement Google providers via REST (gmail v1, calendar v3) with token refresh.
- Persist approvals/drafts/history in DB when `USE_DB=true`.
- WhatsApp cards end‑to‑end and reconnection UX.
- Vector recall behind `CORE_ENABLE_VECTORS=true`.

License

- Proprietary – internal use.
