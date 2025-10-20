# Microsoft 365 Developer Sandbox Setup

1) Join Microsoft 365 Developer Program and create a sandbox tenant (sample data pack optional).
2) Register an Azure AD app (multi-tenant or single-tenant for MVP):
   - Redirect URI: `http://localhost:8000/connections/ms/oauth/callback`
   - Client type: Confidential (temporary for MVP)
   - Scopes (delegated): `User.Read`, `offline_access`, `Mail.ReadWrite`, `Mail.Send`, `Calendars.ReadWrite`
3) Capture credentials:
   - MS_CLIENT_ID, MS_CLIENT_SECRET, MS_REDIRECT_URI
4) Local `.env.local`:
```
PROVIDER_EMAIL=microsoft
PROVIDER_CAL=microsoft
MS_CLIENT_ID=...
MS_CLIENT_SECRET=...
MS_REDIRECT_URI=http://localhost:8000/connections/ms/oauth/callback
FEATURE_MSFT=true
FEATURE_GOOGLE=false
FEATURE_WHATSAPP=false
```
5) Connect flow:
   - Start backend: `uvicorn presentation.api.app:app --reload --port 8000`
   - Open: `http://localhost:8000/connections/ms/oauth/start?user_id=local-user`
   - Verify tokens with: `GET /connections/ms/status?user_id=local-user`
6) Test providers (once wired):
   - `make ms-test-mail USER_ID=local-user`
   - `make ms-test-cal USER_ID=local-user`

Security notes:
- Do not log tokens or message bodies. Redact error payloads.
- Use PKCE and confidential client for MVP; plan public client for web-only later.
