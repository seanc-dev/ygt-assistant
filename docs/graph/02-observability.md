# Graph Live Slice – Observability and Safety

## Metrics

Emit counters/tags via `utils.metrics.increment`:

- ms.oauth.start
- ms.oauth.callback.ok
- ms.oauth.callback.persist_fail
- ms.status.connected / ms.status.disconnected
- ms.test (ok=true/false)
- ms.tokens.get / ms.tokens.upsert / ms.tokens.delete
- ms.tokens.refresh.ok / .retryable / .empty
- graph.inbox.listed
- graph.mail.sent
- graph.events.created
- live.action.error (action, status)
- undo.success / undo.fail

## Redaction Policy

- Never log access or refresh tokens.
- Never log full message bodies or calendar descriptions.
- Error messages must exclude PII; include only status codes and anonymized ids.

## Backoff Strategy

- For 429 and 5xx from Graph, apply exponential backoff with jitter up to GRAPH_RETRY_MAX.
- Respect Retry-After header when present.
- Timeouts governed by GRAPH_TIMEOUT_MS.

## Sampling

- Default to info-level summaries; sample warn-level errors in bursts to avoid noise.
- Consider future structured tracing around action ids.
