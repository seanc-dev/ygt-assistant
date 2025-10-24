# Observability (Graph Live Slice)

Metrics
- graph.inbox.listed
- graph.mail.sent
- graph.events.created
- live.action.error
- undo.success

Redaction
- Never log tokens or message bodies; only counts, ids, deep links.

Backoff
- Retry 429 and 5xx up to 3 attempts with exponential backoff.
