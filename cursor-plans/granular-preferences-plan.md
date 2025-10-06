# Granular automation preferences - TDD Plan

## Scope

Add overall automation controls (askFirst, proactiveness) and per-app overrides (email/calendar/notion). Maintain backward compatibility with legacy fields riskLevel and neverAutoSendEmails.

## API Behavior

- GET /api/profile returns preferences in V2 shape:
  - preferences.notificationsEmail, notificationsPush
  - preferences.global { askFirst: boolean, proactiveness: 'low'|'medium'|'high' }
  - preferences.domains { email?: {...}, calendar?: {...}, notion?: {...} }
  - Also expose legacy fields derived for compatibility during transition.
- PATCH /api/profile accepts partial updates with either V2 shape or legacy fields. Server merges and persists.

## Tests

1. Defaults
   - GET returns V2 preferences with sensible defaults (askFirst=true, proactiveness='medium').
2. Patch V2
   - PATCH preferences.global.askFirst=false and domains.email.proactiveness='low' → GET reflects merge.
3. Patch legacy
   - PATCH legacy riskLevel='high' and neverAutoSendEmails=true → GET maps into V2 (global.proactiveness='high', domains.email.askFirst=true).
4. Backward compatibility
   - GET includes legacy fields for client compatibility (riskLevel derived from global.proactiveness).

## Client UI

- Profile → Automation section with Overall and per-app overrides behind disclosure.
- Snapshot tests for the new UI tree.

## Rollout

- Add TS types; update API client as needed.
- Implement server mapping; keep behavior minimal.
- Follow-up: wire into engines using effective preferences (out of scope here).
