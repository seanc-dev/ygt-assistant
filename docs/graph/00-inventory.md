# Graph Live Slice Inventory

- Providers:
  - services/microsoft_email.py: list_threads, create_draft, send_draft, send_message, get_message, list_inbox
  - services/microsoft_calendar.py: list_events, freebusy, create_event, update_event, delete_event, create_events_batch
  - services/ms_auth.py: token store + refresh (sync/async)
- DI:
  - presentation/api/deps/providers.py (present) – currently routes by env; action-aware gating planned
- Routes:
  - /actions/live/inbox, /actions/live/send, /actions/live/create-events, /actions/live/undo-event/{id}
- Flags (settings.py):
  - FEATURE_GRAPH_LIVE, FEATURE_LIVE_LIST_INBOX, FEATURE_LIVE_SEND_MAIL, FEATURE_LIVE_CREATE_EVENTS, GRAPH_TIMEOUT_MS, GRAPH_RETRY_MAX
- Mocks:
  - services/providers/mock_graph.py
- CI:
  - USE_MOCK_GRAPH=true; evaluator scenarios run in mock-only configuration
