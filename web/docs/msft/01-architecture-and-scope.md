# Architecture and Scope — Microsoft-first MVP

## Providers
- Interfaces unchanged: `EmailProvider`, `CalendarProvider`.
- Implement Microsoft Graph providers: `services/microsoft_email.py`, `services/microsoft_calendar.py`.
- Registry selects via env: `PROVIDER_EMAIL=microsoft`, `PROVIDER_CAL=microsoft`.

## OAuth
- Azure AD Authorization Code with PKCE.
- Store tokens in `oauth_tokens` with: user_id, tenant_id, provider, access_token, refresh_token, expiry, scopes.
- Scopes: `User.Read`, `offline_access`, `Mail.ReadWrite`, `Mail.Send`, `Calendars.ReadWrite`.

## UI Pages
- Home, To review, Drafts, Schedule, Connections, History.
- Non-gateway: deep links to Outlook/Events via `webLink`; YGT is not an inbox replacement.

## Data
- Ensure `oauth_tokens`, `profiles` exist with required columns.
- Add indexes: `oauth_tokens(provider,tenant_id)`, `audit(ts)`.

## Flags
- `FEATURE_MSFT=true`, `FEATURE_GOOGLE=false`, `FEATURE_WHATSAPP=false`.

## Risks
- Need Azure app creds later; tenant handling (common vs organizations).
- Token refresh and throttling (429) handling.
