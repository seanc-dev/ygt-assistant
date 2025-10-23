# Inventory for Mock Expansion + Live Graph Slice

## Action Matrix (initial)
- Inbox list: live (flagged), mock default
- Send mail: live (flagged), mock default
- Create events (day plan): live (flagged), mock default
- Reschedule, triage v2, plan v2: mock only

## Routes touched
- /actions/* (plan, triage, reschedule, reconnect)
- /email/* (drafts, send)
- /calendar/* (plan-today)
- /connections/ms (status/test)

## Provider seams
- services/providers/registry.py
- services/providers/microsoft_email.py
- services/providers/microsoft_calendar.py
- presentation/api/deps/providers.py (to add per-action gates)

## Env flags (to add)
- FEATURE_GRAPH_LIVE=false
- FEATURE_LIVE_LIST_INBOX=false
- FEATURE_LIVE_SEND_MAIL=false
- FEATURE_LIVE_CREATE_EVENTS=false
- USE_MOCK_GRAPH=true (CI)
- GRAPH_TIMEOUT_MS=8000
- GRAPH_RETRY_MAX=3
- LIVE_MODE_BANNER=true
