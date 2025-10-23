Microsoft-first environment setup

Overview

- Microsoft Graph for Mail and Calendar.
- OAuth 2.0 Authorization Code w/ confidential client (MVP) and refresh tokens.
- Tokens encrypted with Fernet and stored in Supabase `oauth_tokens`.

Azure AD app registration

1) Go to Azure Portal → App registrations → New registration.
2) Name: YGT Assistant (Local)
3) Supported account types: Accounts in any organizational directory (Any Azure AD directory) and personal Microsoft accounts.
4) Redirect URI (Web): http://localhost:8000/connections/ms/oauth/callback
5) After create, note Application (client) ID and Directory (tenant) ID.
6) Certificates & secrets → New client secret. Copy the value.
7) API permissions → Add permissions → Microsoft Graph → Delegated → select:
   - offline_access
   - User.Read
   - Mail.ReadWrite
   - Mail.Send
   - Calendars.ReadWrite
   Grant admin consent for your tenant (if required).

Environment variables (.env.local)

Required for Microsoft-first local dev:

```
# Core
DEV_MODE=true

# Providers
PROVIDER_EMAIL=microsoft
PROVIDER_CAL=microsoft

# Microsoft OAuth
MS_CLIENT_ID=<azure-app-client-id>
MS_CLIENT_SECRET=<azure-client-secret>
MS_REDIRECT_URI=http://localhost:8000/connections/ms/oauth/callback
MS_TENANT_ID=common

# Supabase (optional; set USE_DB=true to persist tokens)
USE_DB=false
SUPABASE_URL=
SUPABASE_API_SECRET=

# Secrets (auto-generated in dev if unset)
ADMIN_EMAIL=admin@example.com
ADMIN_SECRET=
ENCRYPTION_KEY=

# Web
WEB_ORIGIN=http://localhost:3001
ADMIN_UI_ORIGIN=http://localhost:3001
CLIENT_UI_ORIGIN=http://localhost:3001
NEXT_PUBLIC_ADMIN_API_BASE=http://localhost:8000
NEXT_PUBLIC_CLIENT_APP_URL=http://localhost:3001
```

Local run

Backend:

```
python -m pip install -r requirements.txt
PYTHONPATH=. uvicorn presentation.api.app:app --reload --port 8000
```

Web:

```
cd web
npm install
npm run dev
```

Connect Microsoft

```
open "http://localhost:8000/connections/ms/oauth/start?user_id=local-user"
curl "http://localhost:8000/connections/ms/status?user_id=local-user"
```

Make targets

```
make status
make ms-connect USER_ID=local-user
make ms-test-mail USER_ID=local-user
make ms-test-cal USER_ID=local-user
```

Notes

- Request IDs propagate via middleware; providers attach `x-ms-client-request-id` to Graph requests.
- Metrics are emitted via `utils/metrics.increment` (no-op logs in dev).
- No sensitive data (tokens, message bodies) are logged.


