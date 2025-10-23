# Observability

## Metrics (counters)
- live.inbox.listed
- live.mail.sent
- live.events.created
- undo.success
- live.action.error
- ms.oauth.* (existing)

## Redaction
- Never log message bodies or tokens.
- Only emit counts, ids, or deep links (not raw content).

## Sampling
- Default: sample all in dev.
- In prod: add sampling if volume grows.
