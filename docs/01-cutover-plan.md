# YGT Assistant — Cutover Plan (POC)

This one-pager defines the minimal, low-blast-radius path to a WhatsApp-first assistant plus a slim web control tower, grounded in the current repo.

## Folder Moves / Structure

- Rename `admin-ui/` → `web/` (keep Pages Router, trim to 6 routes).
- Archive `client-ui/` and `site/` under `archive/` (excluded from CI).
- Add `contracts/` (JSON Schemas + codegen to TS and Pydantic).
- Add `services/whatsapp/` (Meta Cloud API client) or `services/whatsapp.py`.

## Database (idempotent migration)

Add new tables (reuse existing `audit_log` — do not create a new `audit` table):

- `approvals(id uuid pk, kind text, source text, title text, summary text, payload jsonb, risk text, status text, expires_at timestamptz, created_at timestamptz default now())`
- `drafts(id uuid pk, to jsonb, subject text, body text, tone text, status text, risk text, created_at timestamptz default now())`
- `automations(id uuid pk, trigger jsonb, conditions jsonb, action jsonb, enabled bool default false, created_at timestamptz default now())`
- `core_memory(id uuid pk, level text, key text, value jsonb, vector vector(1536) null, meta jsonb, created_at timestamptz default now(), last_used_at timestamptz)`

Indexes:

- `approvals(status, expires_at)`, `drafts(status)`, `automations(enabled)`, `core_memory(level, key)`.
- Conditional `ivfflat (vector)` index only if `pgvector` is available.

## API (FastAPI)

New/Adjusted endpoints (all behind feature flags where appropriate):

- WhatsApp
  - `GET /whatsapp/webhook` (verify)
  - `POST /whatsapp/webhook` (messages + button callbacks → Approvals/Drafts)
- Actions
  - `POST /actions/scan` `{domains:["email","calendar"]}` → `[Approval]`
  - `POST /actions/approve/{id}`
  - `POST /actions/edit/{id}` `{instructions}`
  - `POST /actions/skip/{id}`
- Email
  - `POST /email/drafts`
  - `POST /email/send/{draft_id}` (Postmark via existing mailer; Google support later)
- Calendar
  - `POST /calendar/plan-today`
  - `POST /calendar/reschedule`
- UI data
  - `GET /home`, `GET /approvals?filter=all|email|calendar`, `GET /drafts`, `GET /history?limit=100`
- Core
  - `GET /core/context?for=email|calendar|today`, `POST /core/notes`, `GET /core/preview?intent=...`

Infra:

- Request-id middleware; structured logs.
- Audit all effectful actions by writing to `audit_log`.

## Web (Next.js, Pages Router)

In `web/` keep only these routes and rename navigation for non-technical users:

- `/` Home (Now; top 3 approvals with Approve · Edit · Skip)
- `/review` To review (tabs: All · Email · Calendar; bulk approve)
- `/drafts` Drafts (list + side panel editor: Send · Schedule · Edit)
- `/automations` Automations (recipe toggles; English preview)
- `/connections` Connections (Gmail · Calendar · WhatsApp; Reconnect/Test)
- `/history` History (timeline with “Show details”)

Copy changes: Logs→History, Approvals→To review, Integrations→Connections, Rules→Automations.

## Contracts (shared)

Add `contracts/` schemas and codegen:

- `approval.schema.json`, `draft.schema.json`, `automation.schema.json`, `note.schema.json`, `core_memory.schema.json`
- Generate TS types (`contracts/gen/ts`) and Pydantic models (`contracts/gen/py`).
- CI step to verify schemas and deterministic codegen.

## Core Engine (phase 1)

- `core/store.py` (CRUD; `CORE_ENABLE_VECTORS` flag; Supabase or memory backend)
- `core/retrieval.py` (by_key, similar, context_for)
- `core/writer.py` (episodic, semantic, procedural, narrative)
- `core/policy.py` (risk flags, redaction)
- `core/glue.py` (prompt builders)
- `core/seed.py` (seed 5 items/level)

## Services (POC)

- `services/whatsapp.py` with `send_text`, `send_buttons`, `send_list`, `parse_webhook`.
- `services/gmail.py` minimal direct Google (behind `USE_GOOGLE=true`), else fallback via existing infra.
- `services/calendar.py` minimal list/create/update/freebusy.
- `services/llm.py` summarise/propose approvals and draft emails using `core` context.

## ENV Matrix and Example

Create `.env.example` and standardize Supabase service role env var to `SUPABASE_API_SECRET` for this project’s convention.

```
# Server
DEV_MODE=true
PORT=8000

# OpenAI
OPENAI_API_KEY=

# Core
CORE_ENABLE_VECTORS=false

# Supabase
SUPABASE_URL=
SUPABASE_API_SECRET=
USE_DB=false

# Mailer
USE_SMTP=false
POSTMARK_TOKEN=

# WhatsApp (Meta Cloud)
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=

# Web origins
ADMIN_UI_ORIGIN=http://localhost:3000
CLIENT_UI_ORIGIN=

# Google (optional POC direct)
USE_GOOGLE=false
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_PROJECT_ID=
```

## PR Sequence (acceptance criteria abbreviated)

1. `chore/docs-inventory-cutover` — inventory + cutover docs
2. `feat/contracts-shared` — schemas + codegen + CI check
3. `feat/db-approvals-drafts-core-memory` — idempotent migration + tests
4. `feat/core-engine-v1` — store/retrieval/writer/policy/glue + tests + seed
5. `feat/whatsapp-poc` — service + webhooks + audit + risk gating
6. `feat/web-trim` — rename `admin-ui`→`web`, add 6 routes, snapshot tests, archive `client-ui`/`site`
7. `feat/actions-and-llm` — actions endpoints, Gmail/Calendar, LLM flows
8. `feat/agent-evals-ci` — e2e agent evals + CI integration
9. `chore/env-matrix-alignment` — `.env.example`, env standardization, flags

## Rollout & Risk

- Feature flags and idempotent migrations keep blast radius small.
- Keep Nylas paths behind a flag during transition; prefer Google direct for POC.
- Audit every effectful action; add request-id for traceability.
