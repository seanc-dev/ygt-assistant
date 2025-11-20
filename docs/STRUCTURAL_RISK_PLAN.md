# Structural risk remediation plan

This plan turns the outstanding production-readiness risks into concrete work items with test gates.

## 1) Replace process-local state with durable storage
- **Scope**: approvals, drafts/history, proposed blocks, core memory, idempotency/audit repos, session tokens.
- **Actions**:
  - Introduce Postgres/Supabase tables for approvals/history/drafts and migrate store access through repo interfaces.
  - Move core memory/cache to a tenant-aware persistence layer (Supabase or Redis) with eviction and TTL controls.
  - Replace in-memory idempotency/audit stubs with durable repos enforcing unique constraints and request-id correlation.
  - Replace dev session token shortcuts with expiring, random tokens persisted in a session repo.
- **Tests**:
  - Unit tests for each repo (create/list/update) backed by an in-memory test DB fixture.
  - Integration test asserting actions replay is prevented by idempotency keys.
  - Session tests verifying expiry and revocation across process restarts.

## 2) Decompose the FastAPI entrypoint
- **Scope**: `presentation/api/app.py` monolith and silent fallback imports.
- **Actions**:
  - Extract settings loading, dependency factories, and router registration into dedicated modules (e.g., `presentation/api/deps`, `presentation/api/routes`), removing try/except import fallbacks.
  - Enforce explicit configuration errors when required providers/repos are missing.
  - Split onboarding/invite handlers from triage/action routes to reduce coupling.
- **Tests**:
  - FastAPI app factory test that fails when required env vars are absent.
  - Router smoke tests to ensure only supported routes are registered (e.g., no legacy `/webhooks/nylas`).

## 3) Fix action execution path
- **Scope**: `core/services/action_executor.py` reference to undefined `factory`.
- **Actions**:
  - Correct repo wiring to use the imported `_factory` or dependency-injection container.
  - Add idempotency/audit writes around action execution with error handling and metrics.
- **Tests**:
  - Unit test covering duplicate execution with the same idempotency key (second call no-ops).
  - Test that audit entries are written with request IDs and outcomes.

## 4) Harden LLM orchestration
- **Scope**: stubbed LLM responses and missing retry/telemetry.
- **Actions**:
  - Introduce a provider-agnostic LLM client with retry/backoff, timeout controls, and structured prompts.
  - Add observability hooks (metrics/logs) for prompt/response sizes and errors.
  - Make `LLM_TESTING_MODE` gate fixtures only; require real provider configs otherwise.
- **Tests**:
  - Unit tests for prompt builder and retry logic (simulate transient failures).
  - Contract test that rejects startup when no provider credentials are present in non-testing mode.

## 5) Secure session handling
- **Scope**: dev-only deterministic tokens and in-memory session repo fallbacks.
- **Actions**:
  - Implement a durable session repository with hashed tokens and expiration timestamps.
  - Remove dev token shortcuts from production code paths; keep explicit `DEV_MODE` helpers in a separate module.
  - Add token rotation and logout endpoints that invalidate persisted sessions.
- **Tests**:
  - Session lifecycle tests (issue → validate → revoke/expire) against the repo.
  - API tests ensuring protected endpoints reject missing/expired tokens.

Delivering these items in small PRs with the outlined tests will bring the service closer to production readiness while preventing regressions.
