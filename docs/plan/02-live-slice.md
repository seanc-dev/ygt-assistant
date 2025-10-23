# Live Slice (Microsoft Graph)

## Endpoints (server)
- GET /actions/live/inbox (gated by FEATURE_GRAPH_LIVE + FEATURE_LIVE_LIST_INBOX)
- POST /actions/live/send (FEATURE_LIVE_SEND_MAIL)
- POST /actions/live/create-events (FEATURE_LIVE_CREATE_EVENTS)
- POST /actions/live/undo-event/{event_id}

## Flags
- FEATURE_GRAPH_LIVE=false
- FEATURE_LIVE_LIST_INBOX=false
- FEATURE_LIVE_SEND_MAIL=false
- FEATURE_LIVE_CREATE_EVENTS=false

## Error taxonomy (brief)
- not_supported: provider method unavailable
- not_found: undo target not tracked
- retry=true: provider delete failed; user may retry

## Manual smoke
- Enable flags locally and hit /connections/ms/test for visibility.
- List inbox, send test mail to self, create+undo day-plan events.
