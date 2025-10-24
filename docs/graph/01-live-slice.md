# Live Slice Endpoints

- Inbox (GET): /me/messages?$top=5&$select=subject,from,toRecipients,receivedDateTime,bodyPreview,webLink&$orderby=receivedDateTime desc
- Send (POST): /me/sendMail
- Create Event (POST): /me/events; Delete (DELETE): /me/events/{id}

Flags
- FEATURE_GRAPH_LIVE=false
- FEATURE_LIVE_LIST_INBOX=false
- FEATURE_LIVE_SEND_MAIL=false
- FEATURE_LIVE_CREATE_EVENTS=false

Undo Policy
- Email send is irreversible; show confirm copy.
- Events are undoable by delete.

Errors (short)
- 401 -> reconnect hint, no logs of tokens
- 429/5xx -> backoff and retry up to 3
