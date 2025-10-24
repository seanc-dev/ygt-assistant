# Observability (Graph Live Slice)

Metrics
- graph.inbox.listed
- graph.mail.sent
- graph.events.created
- live.action.error
- undo.success

Redaction
- Never log tokens or bodies; only counts, ids, deep links.

Backoff
- Retry 429 and 5xx with exponential backoff (max 3 attempts).
