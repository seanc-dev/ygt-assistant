# LucidWork — Microsoft Pivot Inventory

This document captures the current repo state before pivoting to Microsoft-first, web-only MVP.

## Backend (FastAPI)
- App: `presentation/api/app.py`
- Routers present:
  - actions, email, calendar, core, chat
  - connections_google (exists), whatsapp (to be trimmed/flagged)
- Middleware: CORS, request-id, admin guards

## Providers
- Interfaces: `services/providers/{email_provider,calendar_provider,errors,registry}.py`
- Registry: env-driven provider selection (defaults to stub)
- Stubs: `services/gmail.py`, `services/calendar.py`

## Services
- LLM stubs: `services/llm.py`
- WhatsApp client: `services/whatsapp.py` (not needed for MVP)

## Web (Next.js / React 19)
- App: `web/` with pages: Home, Review, Drafts, Automations, Connections, History, Chat
- Shared UI: `@lucid-work/ui` in `shared-ui/`

## Database / Migrations (Supabase)
- Migrations: `supabase/migrations/`
  - Approvals, drafts, automations, core_memory
  - oauth_tokens, profiles (present) — may need tenant_id, indexes

## Environment (observed)
- Core flags: DEV_MODE, CORE_ENABLE_VECTORS, USE_DB
- CORS: WEB_ORIGIN, ADMIN_UI_ORIGIN, CLIENT_UI_ORIGIN
- Supabase: SUPABASE_URL, SUPABASE_API_SECRET, SUPABASE_DB_URL
- Secrets: ADMIN_EMAIL, ADMIN_SECRET, ENCRYPTION_KEY
- Google (to replace): GMAIL_CLIENT_ID/SECRET/REDIRECT_URI
- WhatsApp: WHATSAPP_* (to be disabled for MVP)
- LLM: OPENAI_API_KEY

## Tests / CI hooks (relevant)
- Provider registry unit tests
- E2E scaffolding (llm_testing)
- CI runs pytest; migrations can be pushed via Supabase CLI

## Keep / Trim / Replace
- Keep: provider interfaces, registry, core engine, web pages
- Trim: WhatsApp routes behind a feature flag
- Replace: Google stubs with Microsoft Graph providers; add Microsoft connections router
