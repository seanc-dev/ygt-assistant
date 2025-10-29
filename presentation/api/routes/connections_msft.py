from __future__ import annotations
from typing import Any, Dict
import os
import httpx
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, JSONResponse

from utils.crypto import fernet_from, encrypt, decrypt
from settings import ENCRYPTION_KEY
from services.ms_auth import token_store_from_env
from utils.metrics import increment


router = APIRouter(prefix="/connections/ms", tags=["connections-msft"])

# Dev-only fallback when Supabase is not configured/available
_DEV_TOKEN_STORE: Dict[str, Dict[str, Any]] = {}


def _client() -> Dict[str, str]:
    cid = os.getenv("MS_CLIENT_ID", "")
    secret = os.getenv("MS_CLIENT_SECRET", "")
    redirect = os.getenv("MS_REDIRECT_URI", "")
    if not cid or not redirect:
        raise HTTPException(status_code=500, detail="msft_oauth_not_configured")
    return {"client_id": cid, "client_secret": secret, "redirect_uri": redirect}


def _resolve_user_id_from_cookie(request: Request) -> str | None:
    try:
        return request.cookies.get("ygt_user")
    except Exception:
        return None


@router.get("/debug")
async def debug(request: Request) -> Dict[str, Any]:
    """Dev helper: introspect cookie user and presence in stores (no secrets)."""
    cookie_uid = _resolve_user_id_from_cookie(request) or ""
    try:
        store = token_store_from_env()
        has_store = bool(cookie_uid and store.get(cookie_uid))
    except Exception:
        has_store = False
    has_dev = bool(cookie_uid and cookie_uid in _DEV_TOKEN_STORE)
    return {
        "cookie_uid": cookie_uid,
        "has_store": has_store,
        "has_dev_fallback": has_dev,
    }


@router.post("/dev/connect")
async def dev_connect(
    request: Request, uid: str | None = Query(None)
) -> Dict[str, Any]:
    """Dev-only helper: set cookie and a fake token row to simulate connection."""
    if not os.getenv("DEV_MODE"):
        raise HTTPException(status_code=404, detail="not_found")
    user_id = uid or _resolve_user_id_from_cookie(request) or "local-user"
    # populate minimal token row
    _DEV_TOKEN_STORE[user_id] = {
        "provider": "microsoft",
        "tenant_id": os.getenv("MS_TENANT_ID", "common"),
        "access_token": "dev-fallback",
        "refresh_token": "dev-fallback",
        "expiry": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "scopes": [
            "openid",
            "profile",
            "email",
            "User.Read",
            "offline_access",
            "Mail.ReadWrite",
            "Mail.Send",
            "Calendars.ReadWrite",
        ],
    }
    resp = JSONResponse({"ok": True, "user_id": user_id})
    resp.set_cookie(
        key="ygt_user", value=user_id, httponly=True, samesite="lax", path="/"
    )
    return resp


@router.get("/status")
async def status(request: Request, user_id: str | None = Query(None)) -> Dict[str, Any]:
    # Prefer cookie-derived user over query param to avoid stale ids in the UI
    cookie_uid = _resolve_user_id_from_cookie(request)
    if cookie_uid:
        user_id = cookie_uid
    try:
        store = token_store_from_env()
    except Exception:
        increment("ms.status.disconnected", reason="no_store")
        # Dev fallback
        row = _DEV_TOKEN_STORE.get(user_id or "") if user_id else None
        if not row:
            return {"connected": False}
        # continue with row from fallback
        expiry = row.get("expiry")
        scopes = row.get("scopes") or []
        provider = row.get("provider")
        tenant_id = row.get("tenant_id")
        increment("ms.status.connected")
        return {
            "connected": True,
            "scopes": scopes,
            "expires_at": expiry,
            "provider": provider,
            "tenant_id": tenant_id,
        }
    row = store.get(user_id or "") if user_id else None
    if not row:
        # Dev fallback: check in-memory store when no DB row
        if user_id and user_id in _DEV_TOKEN_STORE:
            row = _DEV_TOKEN_STORE[user_id]
        else:
            increment("ms.status.disconnected", reason="no_row")
            return {"connected": False}
    expiry = row.get("expiry")
    scopes = row.get("scopes") or []
    provider = row.get("provider")
    tenant_id = row.get("tenant_id")
    increment("ms.status.connected")
    return {
        "connected": True,
        "scopes": scopes,
        "expires_at": expiry,
        "provider": provider,
        "tenant_id": tenant_id,
    }


@router.get("/oauth/start")
async def oauth_start(
    tenant: str | None = Query(None), user_id: str | None = Query(None)
) -> RedirectResponse:
    cfg = _client()
    # Resolve tenant from query → env → common
    tenant = tenant or os.getenv("MS_TENANT_ID", "common")
    # Minimal state token (encrypted), PKCE later
    import secrets as _secrets

    f, _k = fernet_from(ENCRYPTION_KEY)
    payload = {
        "nonce": _secrets.token_urlsafe(16),
        "ts": datetime.now(timezone.utc).isoformat(),
        "tenant": tenant,
    }
    try:
        import json as _json

        state_token = encrypt(f, _json.dumps(payload))
    except Exception:
        state_token = encrypt(f, payload["nonce"])  # fallback
    # If a user_id is provided (legacy/dev), pass it through as state for compatibility with tests
    params = {
        "client_id": cfg["client_id"],
        "response_type": "code",
        "redirect_uri": cfg["redirect_uri"],
        "response_mode": "query",
        # Include User.Read for /me; keep OIDC + Graph scopes
        "scope": "openid profile email User.Read offline_access Mail.ReadWrite Mail.Send Calendars.ReadWrite",
        "state": user_id if user_id else state_token,
    }
    url = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize".format(
        tenant=tenant
    )
    qp = httpx.QueryParams(params)
    increment("ms.oauth.start")
    return RedirectResponse(url=f"{url}?{str(qp)}", status_code=302)


@router.get("/oauth/callback")
async def oauth_callback(
    request: Request,
    code: str | None = Query(None),
    state: str | None = Query(None),
    tenant: str | None = Query(None),
    error: str | None = Query(None),
    error_description: str | None = Query(None),
) -> JSONResponse:
    # Early error from IdP (e.g., MFA failure, policy)
    if error:
        return JSONResponse(
            {"ok": False, "error": error, "error_description": error_description},
            status_code=400,
        )
    cfg = _client()
    tenant = tenant or os.getenv("MS_TENANT_ID", "common")
    if not code:
        return JSONResponse(
            {
                "ok": False,
                "error": "missing_code",
                "error_description": "Authorization code not provided by identity provider.",
            },
            status_code=400,
        )
    data = {
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": cfg["redirect_uri"],
    }
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
            r = await c.post(token_url, data=data)
            r.raise_for_status()
            tok = r.json()
    except Exception as exc:
        return JSONResponse(
            {
                "ok": False,
                "error": "token_exchange_failed",
                "error_description": "Failed to exchange code for tokens. Please retry connect.",
            },
            status_code=400,
        )

    # Decode state (best-effort)
    user_cookie_id: str | None = None
    state_user_id: str | None = None
    try:
        if state:
            f, _k = fernet_from(ENCRYPTION_KEY)
            import json as _json

            decoded = decrypt(f, state)
            st = _json.loads(decoded)
            _ = st.get("nonce")
        else:
            st = {"tenant": tenant}
    except Exception:
        st = {"tenant": tenant}
        # Legacy/dev path: state may be a plain user id from older callers/tests
        if state and isinstance(state, str):
            state_user_id = state

    # Persist tokens encrypted
    access_token = tok.get("access_token") or ""
    refresh_token = tok.get("refresh_token") or ""
    expires_in = int(tok.get("expires_in") or 0)
    scopes_list = (tok.get("scope") or "").split()
    tenant_id = tenant

    # Identify user via Graph /me (avoid id_token parsing for MVP)
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            me = await c.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"$select": "id,userPrincipalName,mail,displayName"},
            )
            me.raise_for_status()
            me_json = me.json()
            aad_user_id = me_json.get("id") or ""
            email = me_json.get("mail") or me_json.get("userPrincipalName") or ""
            display_name = me_json.get("displayName") or ""
    except Exception:
        aad_user_id = ""
        email = ""
        display_name = ""

    # Fallback to legacy state user id when /me not available (tests/dev)
    if not aad_user_id and state_user_id:
        aad_user_id = state_user_id

    f, _k = fernet_from(ENCRYPTION_KEY)
    try:
        store = token_store_from_env()
        # Use aad_user_id as the key
        if not aad_user_id:
            raise RuntimeError("cannot_resolve_user")
        payload_row = {
            "provider": "microsoft",
            "tenant_id": tenant_id,
            "access_token": encrypt(f, access_token),
            "refresh_token": encrypt(f, refresh_token),
            "expiry": (
                datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            ).isoformat(),
            "scopes": scopes_list,
        }
        store.upsert(aad_user_id, payload_row)
        # Cache in dev fallback as well to ensure UI reflects connection immediately
        _DEV_TOKEN_STORE[aad_user_id] = payload_row
        # Upsert profiles via Supabase REST
        base_url = os.getenv("SUPABASE_URL", "").rstrip("/") + "/rest/v1"
        api_key = os.getenv("SUPABASE_API_SECRET", "")
        if base_url and api_key and aad_user_id:
            async with httpx.AsyncClient(timeout=10) as c:
                payload = {
                    "aad_user_id": aad_user_id,
                    "email": email,
                    "display_name": display_name,
                    "tenant_id": tenant_id,
                }
                r = await c.post(
                    f"{base_url}/profiles",
                    headers={
                        "apikey": api_key,
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    json=payload,
                )
                if r.status_code == 409:
                    await c.patch(
                        f"{base_url}/profiles",
                        params={"aad_user_id": f"eq.{aad_user_id}"},
                        headers={
                            "apikey": api_key,
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                        },
                        json={k: v for k, v in payload.items() if v},
                    )
        user_cookie_id = aad_user_id
        increment("ms.oauth.callback.ok")
    except Exception:
        # Dev fallback: keep tokens in memory to unblock local testing
        if aad_user_id:
            _DEV_TOKEN_STORE[aad_user_id] = {
                "provider": "microsoft",
                "tenant_id": tenant_id,
                "access_token": "dev-fallback",
                "refresh_token": "dev-fallback",
                "expiry": (
                    datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                ).isoformat(),
                "scopes": scopes_list,
            }
        increment("ms.oauth.callback.persist_fail")

    resp = JSONResponse(
        {
            "ok": True,
            "user_id": user_cookie_id or "",
            "scopes": scopes_list,
            "expires_in": expires_in,
        }
    )
    # Dev cookie for user resolution in subsequent calls
    if user_cookie_id:
        resp.set_cookie(
            key="ygt_user",
            value=user_cookie_id,
            httponly=True,
            samesite="lax",
            path="/",
        )
    # Optional redirect back to connections page if WEB_ORIGIN is set
    web_origin = os.getenv("WEB_ORIGIN") or os.getenv("NEXT_PUBLIC_CLIENT_APP_URL")
    if web_origin:
        try:
            redir = RedirectResponse(
                url=f"{web_origin.rstrip('/')}/connections", status_code=302
            )
            if user_cookie_id:
                redir.set_cookie(
                    key="ygt_user",
                    value=user_cookie_id,
                    httponly=True,
                    samesite="lax",
                    path="/",
                )
            return redir
        except Exception:
            pass
    return resp


@router.post("/test")
async def test_conn(
    request: Request, user_id: str | None = Query(None)
) -> Dict[str, Any]:
    # Minimal: presence of token row indicates connected
    try:
        store = token_store_from_env()
        cookie_uid = _resolve_user_id_from_cookie(request)
        uid = cookie_uid or user_id or ""
        row = store.get(uid)
        if not row and uid in _DEV_TOKEN_STORE:
            row = _DEV_TOKEN_STORE[uid]
        ok = bool(row)
        increment("ms.test", ok=ok)
        # Live slice flags visibility for manual smoke
        from settings import (
            FEATURE_GRAPH_LIVE,
            FEATURE_LIVE_LIST_INBOX,
            FEATURE_LIVE_SEND_MAIL,
            FEATURE_LIVE_CREATE_EVENTS,
        )

        return {
            "ok": ok,
            "live": bool(FEATURE_GRAPH_LIVE),
            "live_flags": {
                "list_inbox": bool(FEATURE_LIVE_LIST_INBOX),
                "send_mail": bool(FEATURE_LIVE_SEND_MAIL),
                "create_events": bool(FEATURE_LIVE_CREATE_EVENTS),
            },
        }
    except Exception:
        increment("ms.test", ok=False)
        return {"ok": False}


@router.post("/disconnect")
async def disconnect(
    request: Request, user_id: str | None = Query(None)
) -> JSONResponse:
    uid = user_id or _resolve_user_id_from_cookie(request) or ""
    ok = True
    try:
        store = token_store_from_env()
        if uid:
            try:
                store.delete(uid)
            except Exception:
                pass
        # Also clear dev fallback if present
        if uid and uid in _DEV_TOKEN_STORE:
            try:
                del _DEV_TOKEN_STORE[uid]
            except Exception:
                pass
        increment("ms.disconnect.ok")
    except Exception:
        # Still report success to keep UX simple in dev
        ok = True
        increment("ms.disconnect.fail")
    resp = JSONResponse({"ok": ok, "disconnected": True})
    # Clear cookie so subsequent status checks don't resolve stale user
    if uid:
        resp.set_cookie(
            key="ygt_user", value="", max_age=0, path="/", httponly=True, samesite="lax"
        )
    return resp
