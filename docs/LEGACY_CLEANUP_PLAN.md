# Legacy functionality cleanup plan

With Nylas-hosted flows and EventKit CLI code removed, the cleanup focus shifts to preventing reintroduction of those paths and finishing the migration to Microsoft Graph/Google connectors. The items below document what was removed and the guardrails/tests that keep the codebase aligned with the current direction.

## Removed legacy functionality

- **Nylas-hosted OAuth/webhooks and grant storage**: `/webhooks/nylas`, `/oauth/nylas/*`, `NylasGrant`, and archived grant repos were deleted. Admin onboarding now links to Microsoft Graph. Documentation and settings were updated to drop Nylas references.
- **EventKit/macOS CLI calendar agent**: EventKit agent, CLI dispatcher, and related integration tests were removed. CLI-specific utilities (`main.py`, command dispatcher) were pruned.
- **Archived/stubbed providers**: Archived Nylas grant repos and EventKit adapters were deleted; quick-reference docs no longer mention them.

## Guardrails and TDD steps

- **Regression tests for supported connectors**
  - Add FastAPI tests that assert `/connections/ms/oauth/start` returns a 302 to Microsoft login when env vars are set.
  - Add guard tests that `/webhooks/nylas` and `/oauth/nylas/*` return 404 to prevent accidental reintroduction.
  - Keep a smoke test for Google OAuth start once env is provided.

- **API surface validation**
  - Admin status payloads now expose `has_ms_connection`; frontend should rely on that instead of legacy `has_nylas_connection`.
  - Invitations reference Notion + Microsoft Graph links; mail templates should stay in sync.

- **Documentation alignment**
  - Ensure new docs stay Graph-first (no Nylas or EventKit setup). Keep env samples limited to Notion/Microsoft/Google and SMTP.
  - Note removals in changelog/releases to reduce confusion for operators.

- **Repository hygiene**
  - Block new archived/stubbed providers from being imported; add lint/tests to flag new `Nylas`/`EventKit` strings in active code paths.
  - Prefer durable repos over in-memory stubs when adding new integrations.

Following these steps keeps the codebase clean and maintains test coverage as legacy providers are retired.
