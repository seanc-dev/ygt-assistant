# Codebase Overview

## 🏗️ CoachFlow Architecture

CoachFlow is a multi-service system that helps coaches triage email, manage calendars, and keep Notion in sync. It surfaces approval-first suggestions via a web admin portal. The platform integrates with Nylas (email/calendar), Notion API, Postmark (SMTP), and OpenAI. The API is deployed on Fly.io; the public marketing site runs on Vercel.

### Core components

- **FastAPI backend** (`presentation/api/app.py`)
  - OAuth flows: Notion, Nylas (Hosted Auth)
  - Webhooks: Nylas events → rules-based triage → suggested actions
  - Actions executor → Notion operations (dry-run by default)
  - Admin endpoints: tenants, rules, settings, invites
- **Admin UI** (`admin-ui/`) – Next.js app for approvals and setup
- **Marketing site** (`site/`) – Next.js site at `https://coachflow.nz`
- **Infra repos** (`infra/`) – interchangeable persistence (memory or Supabase)
- **Core services** (`core/`) – triage engine, memory, embeddings
- **LLM testing** (`llm_testing/`) – internal evaluation utilities (optional)

## 📁 Project Structure

```
coach-flow-app/
├── presentation/api/            # FastAPI application
│   └── app.py                   # Main API with OAuth, webhooks, actions
├── admin-ui/                    # Admin portal (Next.js)
├── site/                        # Marketing site (Next.js)
├── core/                        # Core services (triage, memory, embeddings)
├── infra/                       # Repos (memory, Supabase); mailer integrations
├── adapters/                    # External providers (Notion, EventKit legacy)
├── utils/                       # Utilities (crypto, admin session, CLI helpers)
├── tests/                       # Pytest suite (API, services, adapters)
├── llm_testing/                 # Optional evaluation tools
├── docs/                        # Documentation
├── settings.py                  # Environment configuration
├── Dockerfile                   # Root Dockerfile for Fly.io
├── fly.toml                     # Fly app config
└── requirements.txt
```

Notes:

- Supabase can be enabled with `USE_DB=true` (otherwise memory repos are used).
- SMTP (Postmark) can be enabled with `USE_SMTP=true`.
- The legacy EventKit calendar adapter remains for dev experiments but is not used in production flows.

## 🔄 High-level Data Flow

1. **Nylas webhook → triage**

```
Nylas → POST /webhooks/nylas → triage_engine → suggested actions (dry-run)
```

2. **Admin approval → actions execute**

```
Admin UI → POST /actions/execute (dry_run=false) → Notion adapter
```

3. **OAuth connections**

```
User → /oauth/notion/start → callback → store access (ConnectionsRepo)
User → /oauth/nylas/start?provider=google|microsoft → callback → store grant
```

## 🌐 Web API (selected)

- `GET /health` → `{ "status": "ok" }`
- `GET /oauth/notion/start` → 302 to Notion authorize
- `GET /oauth/notion/callback?code&state` → token exchange + persist, 302 to Admin UI
- `GET /oauth/nylas/start?provider=google|microsoft` → 302 to Nylas
- `GET /oauth/nylas/callback?provider&code&state` → exchange + persist, 302 to Admin UI
- `GET /webhooks/nylas?challenge=...` → echo challenge
- `POST /webhooks/nylas` → verify optional `X-Nylas-Signature` (when `VERIFY_NYLAS=true`), process events
- `POST /actions/execute` → execute suggested actions (dry-run or live)
- `GET /audit/{request_id}` → retrieve last run (in-memory or DB)
- Admin APIs under `/admin/*` for login, tenants, rules, settings, invites

## 🔐 Environment & Deployment

- Fly app: `coach-flow-app`
- Real mode: `MOCK_OAUTH=false`
- Required secrets (typical):
  - Always: `ENCRYPTION_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
  - OAuth: `NOTION_CLIENT_ID`, `NOTION_CLIENT_SECRET`, `NOTION_REDIRECT_URI`
  - Nylas: `NYLAS_CLIENT_ID`, `NYLAS_CLIENT_SECRET`, `NYLAS_REDIRECT_URI`, `NYLAS_SIGNING_SECRET`, `VERIFY_NYLAS`
  - Email sending:
    - Set `USE_SMTP=true`
    - If using generic SMTP: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`
    - If using Postmark SMTP/API: set appropriate Postmark values (e.g., `POSTMARK_SERVER_TOKEN`, `POSTMARK_FROM_EMAIL`, `POSTMARK_MESSAGE_STREAM`)
    - Note: Postmark variables are NOT required if you use a non-Postmark SMTP provider
  - CORS: `ADMIN_UI_ORIGIN` (e.g., `https://admin.coachflow.nz`), `CLIENT_UI_ORIGIN`

## 🧠 Core Services

### Triage Engine (`core/services/triage_engine.py`)

- YAML rules from `config/rules.yaml`
- Fallback creates a low-confidence `create_task` when no rule matches

### Memory & Embeddings

- Embeddings manager supports OpenAI vectors with ChromaDB (falls back to JSON when unavailable)

## 🧪 Testing

- Default unit suite: `pytest -q`
- Integration markers exist; e2e disabled by default in `pytest.ini`
- Minimal OAuth tests for Notion + Nylas; webhook signature tests

## 🧰 Developer Workflow

- TDD flow documented in `docs/QUICK_REFERENCE.md`
- Use feature branches and PRs to `main`
- Deploy to Fly via `flyctl deploy`

## 📝 Onboarding Prompt (for a Chat LLM)

Use this prompt when asking an LLM to add a feature safely:

```
You are pair-programming on coach-flow-app, a FastAPI backend and Next.js admin/site.

Context:
- OAuth: Notion + Nylas; triage suggestions via rules; actions sync to Notion.
- Persistence: memory repos by default; Supabase optional with USE_DB=true.
- Webhooks: /webhooks/nylas with optional signature verification.
- Admin UI: https://admin.coachflow.nz (CORS via ADMIN_UI_ORIGIN).

Rules:
1) Follow TDD: write/adjust tests first; run pytest.
2) Keep edits minimal; do not reformat unrelated code.
3) Update docs for API changes.
4) Ensure new endpoints have tests.
```
