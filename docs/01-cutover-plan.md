# LucidWork cutover guide (current repo)

This plan describes how to ship the Microsoft Graph-first Hub/Workroom experience from the current code. It assumes the existing FastAPI + Next.js stack and the removal of Nylas/EventKit code.

## Structure

- Keep `web/` as the single Next.js Pages app (Hub, Workroom, Review, Drafts, Connections, History, Chat).
- Keep FastAPI entrypoint in `presentation/api/app.py` with route modules under `presentation/api/routes`.
- Use `shared-ui/` for all UI primitives; avoid introducing new design-system forks.

## Database (idempotent)

- Rely on `supabase/schema.sql` and existing migrations for oauth tokens, profiles, audit log, actions, and workroom tables.
- Ensure `pgvector` is enabled when `CORE_ENABLE_VECTORS=true`; otherwise remain on deterministic memory paths.

## API focus areas

- **Connections**: Microsoft Graph OAuth (`/connections/ms/oauth/*`) as primary; keep Notion (`/oauth/notion/*`) for context; leave Google under an explicit feature flag.
- **Hub data**: `/api/brief/today`, `/api/schedule/today`, `/api/queue`, `/api/settings`, `/api/profile` should respond with real data (or safe stubs) for Hub cards.
- **Actions**: `/actions/scan` and approve/edit/skip/undo flows should populate the queue consumed by Hub/Review pages; audit writes should be durable when DB is enabled.
- **Workroom**: `/workroom/*` endpoints back the node/kanban workspace; keep them behind the existing store abstractions.
- **WhatsApp**: `/whatsapp/webhook` should stay idempotent and behind verification tokens; link responses back to approvals/drafts when Meta is configured.

## Web (Next.js)

- Keep Hub and Workroom as primary entry points; ensure data hooks (`useHubData`, `useWorkroomStore`) tolerate empty/placeholder responses in dev.
- Keep Connections page pointed at Microsoft Graph first; surface Notion/Google only when configured.
- Preserve Chat page as a debugging stand‑in for `/chat`.

## Environment & flags

- Default `DEV_MODE=true`, `USE_DB=false` for local; require `ENCRYPTION_KEY`/`ADMIN_SECRET` when hardening.
- Live Graph flags: `FEATURE_GRAPH_LIVE`, `FEATURE_LIVE_LIST_INBOX`, `FEATURE_LIVE_SEND_MAIL`, `FEATURE_LIVE_CREATE_EVENTS` remain opt-in.
- Keep `USE_MOCK_GRAPH` true by default for safe local runs; disable when exercising live Microsoft Graph.

## PR sequence (suggested)

1. Harden connections and action execution paths (fix stub fallbacks, ensure `/actions/scan` works with DB enabled).
2. Stabilize Hub data responses with fixtures plus telemetry; add contract tests for `/api/brief/today`, `/api/schedule/today`, `/api/queue`.
3. Wire Workroom endpoints to durable storage when `USE_DB=true`; add smoke tests for kanban/document views.
4. Turn on pgvector-backed memory under a flag and add tests for `core/store.py` recall.
5. Harden WhatsApp webhook with verification and audit, keeping it feature-flagged.

## Rollout & risk

- Default to Microsoft Graph; avoid reintroducing legacy Nylas/EventKit flows.
- Keep feature flags on by default for safe local stubs; fail fast when required secrets are missing in live modes.
- Audit every effectful action (approvals, drafts, workroom mutations) when DB is enabled; attach request IDs for traceability.
