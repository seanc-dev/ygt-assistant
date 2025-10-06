# Nylas Hosted Auth Integration

This document describes the Nylas OAuth integration for Google and Microsoft calendar/email access.

## Environment Variables

Set these environment variables in your deployment:

```bash
# Nylas OAuth Configuration
NYLAS_CLIENT_ID=your_nylas_client_id
NYLAS_CLIENT_SECRET=your_nylas_client_secret
NYLAS_API_URL=https://api.us.nylas.com  # or https://api.eu.nylas.com for EU
NYLAS_REDIRECT_URI=https://api.coachflow.nz/oauth/nylas/callback

# Optional: Enable webhook signature verification
VERIFY_NYLAS=true
NYLAS_SIGNING_SECRET=your_webhook_signing_secret
```

## API Endpoints

### 1. Start OAuth Flow

**GET** `/oauth/nylas/start`

Starts the Nylas OAuth flow for Google or Microsoft.

**Parameters:**
- `provider` (required): `google` or `microsoft`
- `tenant_id` (optional): Tenant identifier (defaults to `tenant-default`)

**Example:**
```bash
curl "https://api.coachflow.nz/oauth/nylas/start?provider=google"
# Returns 302 redirect to Nylas login page
```

### 2. OAuth Callback

**GET** `/oauth/nylas/callback`

Handles the OAuth callback from Nylas and exchanges the authorization code for tokens.

**Parameters:**
- `code` (required): Authorization code from Nylas
- `state` (required): CSRF state parameter
- `provider` (required): `google` or `microsoft`

**Example:**
```bash
# This is called by Nylas automatically after user authorization
curl "https://api.coachflow.nz/oauth/nylas/callback?provider=google&code=abc123&state=xyz789"
# Returns 302 redirect to success page
```

### 3. Webhook Challenge

**GET** `/webhooks/nylas`

Handles Nylas webhook challenge verification.

**Parameters:**
- `challenge` (optional): Challenge token from Nylas

**Example:**
```bash
curl "https://api.coachflow.nz/webhooks/nylas?challenge=ping"
# Returns: ping
```

### 4. Webhook Events

**POST** `/webhooks/nylas`

Receives webhook events from Nylas.

**Headers:**
- `X-Nylas-Signature` (optional): HMAC signature for verification

**Example:**
```bash
curl -X POST "https://api.coachflow.nz/webhooks/nylas" \
  -H "Content-Type: application/json" \
  -H "X-Nylas-Signature: sha256=abc123..." \
  -d '{"type":"email.created","data":{"id":"123","subject":"Test"}}'
```

## OAuth Flow

1. **User clicks "Connect Google/Microsoft"** in your app
2. **Redirect to start endpoint**: `GET /oauth/nylas/start?provider=google`
3. **User authorizes** on Nylas login page
4. **Nylas redirects back**: `GET /oauth/nylas/callback?provider=google&code=...&state=...`
5. **App exchanges code for tokens** and stores grant
6. **User redirected to success page**

## Grant Storage

OAuth grants are stored in `nylas_grants.json` with the following structure:

```json
{
  "grant_id": "nylas_grant_123",
  "provider": "google",
  "email": "user@example.com",
  "scopes": ["calendar", "email"],
  "access_token": "ya29.abc123...",
  "refresh_token": "1//abc123...",
  "expires_at": "2024-01-01T12:00:00",
  "created_at": "2024-01-01T10:00:00",
  "updated_at": "2024-01-01T10:00:00"
}
```

## Scopes

### Google
- `https://www.googleapis.com/auth/calendar` - Calendar read/write
- `https://www.googleapis.com/auth/gmail.readonly` - Email read-only

### Microsoft
- `https://graph.microsoft.com/calendars.readwrite` - Calendar read/write
- `https://graph.microsoft.com/mail.read` - Email read-only

## Testing

Run the test suite:

```bash
pytest tests/test_nylas_oauth.py -v
```

## Mock Mode

For development/testing, set `MOCK_OAUTH=true` to use mock tokens instead of real Nylas API calls.

## Security

- CSRF protection via state parameter
- Webhook signature verification (optional)
- Tokens stored securely with encryption
- HTTPS required for all endpoints
