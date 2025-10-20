### Google Provider Integration — TDD Plan

- Objective: Replace stubbed Gmail/Calendar with Google APIs behind clean provider abstractions; persist OAuth; keep WhatsApp-first flows; wire Connections UI.

#### Scope A — Provider abstractions (this PR)

- Define `ProviderError` with provider, operation, status_code, hint.
- Create `EmailProvider` and `CalendarProvider` abstract classes.
- Implement provider registry selected by env: `PROVIDER_EMAIL`, `PROVIDER_CAL`.
- Add stub providers implementing the interfaces (no external calls).
- Refactor `services/gmail.py` and `services/calendar.py` to delegate.
- Tests: registry selection, error structure, delegation smoke.

#### Scope B — Google implementations (next PR)

- `services/google_email.py` and `services/google_calendar.py` skeletons.
- OAuth routes under `/connections/google/*` (start, callback, status, disconnect).
- Supabase migrations: `oauth_tokens`, `profiles`.
- Token storage encrypted via `ENCRYPTION_KEY` (reuse Fernet util for now).
- Retry/refresh on 401; redaction of secrets.

#### Scope C — UI + CLI + E2E (later PRs)

- Web `connections` page status + Test/Reconnect/Disconnect.
- CLI `make` targets to drive local auth and provider tests.
- E2E: approve flow sending draft + scheduling event, undo semantics, audit writes.

#### Test Outline

- Unit: `ProviderError` fields; registry env selection; stub provider methods return shapes; services delegate to registry.
- Integration: (later) token refresh logic.

#### Exit Criteria (Scope A)

- All new unit tests pass locally and in CI.
- Existing tests remain green.
- No runtime dependency on Google libs yet.
