LucidWork (working name)

LucidWork is a FastAPI + Next.js workspace built around a Hub (control room) and Workroom (node-based workspace). The current implementation focuses on Microsoft Graph-first email/calendar flows, Notion context, and a guided queue of suggested actions that can be approved or edited from the web app. Providers default to in-memory stubs in local dev and can target Supabase for persistence.

High-level architecture

- Backend: FastAPI (`presentation/api`) with route modules for actions, calendar/email helpers, brief/summary data, workroom APIs, and connection flows for Microsoft Graph + Notion (Google connector remains experimental).
- Web: Next.js app in `web/` (React 19) with Hub, Workroom, Review, Drafts, Connections, History, and Chat pages; shared UI primitives live in `shared-ui`.
- Data: Supabase/Postgres schema under `supabase/` (optional; in-memory repos remain the default during development).
- Services: provider registry for Microsoft Graph mail/calendar, Notion adapter, LLM stubs, WhatsApp webhook handler, and translation/weather/news helpers.

Key features (implemented)

- Hub: aggregated queue (`/api/queue`), today’s agenda (`/api/schedule/today`), sync status (`/connections/ms/status`), and brief cards (`/api/brief/today`).
- Workroom: projects/tasks workspace backed by `/workroom/*` APIs with Kanban and document views.
- Actions: `/actions/scan` plus Approve/Edit/Skip/Undo endpoints; queue surfaced in Hub and Review pages.
- Drafts & email: compose/send via `/email/drafts` + `/email/send/{draft_id}` with provider-backed Graph calls when enabled.
- Calendar helpers: `/calendar/plan-today` and `/calendar/reschedule`.
- Core memory/context: `/core/context`, `/core/notes`, `/core/preview` for deterministic recall; vector recall is disabled by default.
- Connections: Microsoft OAuth (`/connections/ms/oauth/*`) with encrypted token storage; Notion OAuth (`/oauth/notion/*`) for context; Google connector routed through `presentation/api/routes/connections_google.py` (experimental/off by default).
- WhatsApp: webhook verify/ingest at `/whatsapp/webhook` (Meta Cloud payloads), currently stubbed for local dev.

Repository layout

- `presentation/api`: FastAPI app, middleware, and routers (actions, brief/summary, queue, workroom, chat, connections, WhatsApp).
- `services`: provider shims (Microsoft Graph, Notion, Google stub), LLM/testing helpers, WhatsApp client, translation/weather/news utilities.
- `core`: memory store/retrieval/writer/policy/glue and triage engine used by `/actions/scan`.
- `supabase/migrations`: SQL for oauth tokens, profiles, memory, and audit tables (optional).
- `web`: Next.js app with Hub/Workroom and related pages; uses shared UI from `shared-ui`.
- `docs`: reference docs, inventory, and cutover plans.

Prerequisites

- Python 3.11+; Node 18+; Supabase CLI (optional for DB push).
- A Supabase project if `USE_DB=true` (otherwise in-memory repos are used).

Environment
Create `.env.local` at repo root (Microsoft-first defaults):

```
# Core
DEV_MODE=true
CORE_ENABLE_VECTORS=false

# Providers
PROVIDER_EMAIL=microsoft
PROVIDER_CAL=microsoft

# API origins
WEB_ORIGIN=http://localhost:3001
ADMIN_UI_ORIGIN=http://localhost:3001
CLIENT_UI_ORIGIN=http://localhost:3001

# DB (optional; set USE_DB=true to enable Supabase)
USE_DB=false
SUPABASE_URL=
SUPABASE_API_SECRET=

# Microsoft OAuth
MS_CLIENT_ID=
MS_CLIENT_SECRET=
MS_REDIRECT_URI=http://localhost:8000/connections/ms/oauth/callback
MS_TENANT_ID=common

# Notion OAuth
NOTION_CLIENT_ID=
NOTION_CLIENT_SECRET=
NOTION_REDIRECT_URI=http://localhost:8000/oauth/notion/callback

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
LIVE_MODE_BANNER=true

# Live Graph feature flags (default off)
FEATURE_GRAPH_LIVE=false
FEATURE_LIVE_LIST_INBOX=false
FEATURE_LIVE_SEND_MAIL=false
FEATURE_LIVE_CREATE_EVENTS=false
GRAPH_TIMEOUT_MS=8000
GRAPH_RETRY_MAX=3
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
open http://localhost:3001/hub
open http://localhost:3001/workroom
```

Supabase migrations (optional)

- CLI path:

```
supabase login
supabase link --project-ref <your-ref>
supabase db push --yes
```

Microsoft connections

```
open "http://localhost:8000/connections/ms/oauth/start"
curl -i --cookie-jar cookies.txt "http://localhost:8000/connections/ms/status"
```

Make targets

```
make status             # provider + DB flags
make db-migrate         # applies SQL with SUPABASE_DB_URL
make ms-connect USER_ID=local-user
make ms-test-mail USER_ID=local-user
make ms-test-cal USER_ID=local-user
make live-smoke         # requires FEATURE_GRAPH_LIVE=true locally
```

Design principles

- Calm UI: Hub/Workroom layouts focus on one primary action at a time with undo/history affordances.
- Safety: request-id tracing; dev stubs avoid leaking secrets; no logging of message bodies or tokens.
- Modularity: providers behind clean interfaces; env-driven selection; feature flags.

Troubleshooting

- Chat or Hub hangs: verify backend `/chat`, `/api/queue`, and `/api/schedule/today` return 200; ensure backend is on port 8000.
- Next.js module resolution errors: ensure `web/next.config.js` transpiles `@ygt-assistant/ui` and aliases React to `web/node_modules`.
- ADMIN_SECRET error on startup: set `.env.local` or `DEV_MODE=true` (dev auto-generates safe values).

Roadmap (near-term)

- Harden Microsoft Graph providers with retries and metrics.
- Persist approvals/drafts/history in DB when `USE_DB=true`.
- Complete WhatsApp cards end-to-end and reconnection UX.
- Enable vector recall behind `CORE_ENABLE_VECTORS=true` once embeddings store is wired to Postgres/pgvector.

License

- Proprietary – internal use.
