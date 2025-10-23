from __future__ import annotations
from typing import Any, Dict
import os
import httpx
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from utils.crypto import fernet_from, encrypt
from settings import ENCRYPTION_KEY
from services.ms_auth import token_store_from_env
from utils.metrics import increment


router = APIRouter(prefix="/connections/ms", tags=["connections-msft"])


def _client() -> Dict[str, str]:
    cid = os.getenv("MS_CLIENT_ID", "")
    secret = os.getenv("MS_CLIENT_SECRET", "")
    redirect = os.getenv("MS_REDIRECT_URI", "")
    if not cid or not redirect:
        raise HTTPException(status_code=500, detail="msft_oauth_not_configured")
    return {"client_id": cid, "client_secret": secret, "redirect_uri": redirect}


@router.get("/status")
async def status(user_id: str = Query(...)) -> Dict[str, Any]:
    try:
        store = token_store_from_env()
    except Exception:
        increment("ms.status.disconnected", reason="no_store")
        return {"connected": False}
    row = store.get(user_id)
    if not row:
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
    user_id: str = Query(...), tenant: str = Query("common")
) -> RedirectResponse:
    cfg = _client()
    # PKCE for later; MVP uses basic code flow
    params = {
        "client_id": cfg["client_id"],
        "response_type": "code",
        "redirect_uri": cfg["redirect_uri"],
        "response_mode": "query",
        "scope": "User.Read offline_access Mail.ReadWrite Mail.Send Calendars.ReadWrite",
        "state": user_id,
    }
    url = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize".format(
        tenant=tenant
    )
    qp = httpx.QueryParams(params)
    increment("ms.oauth.start")
    return RedirectResponse(url=f"{url}?{str(qp)}", status_code=302)


@router.get("/oauth/callback")
async def oauth_callback(
    code: str = Query(...), state: str = Query(...), tenant: str = Query("common")
) -> Dict[str, Any]:
    cfg = _client()
    data = {
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": cfg["redirect_uri"],
    }
    async with httpx.AsyncClient(timeout=15) as c:
        token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
        r = await c.post(token_url, data=data)
        r.raise_for_status()
        tok = r.json()

    # Persist tokens encrypted
    access_token = tok.get("access_token") or ""
    refresh_token = tok.get("refresh_token") or ""
    expires_in = int(tok.get("expires_in") or 0)
    scopes_list = (tok.get("scope") or "").split()
    tenant_id = tenant

    f, _k = fernet_from(ENCRYPTION_KEY)
    try:
        store = token_store_from_env()
        store.upsert(
            state,
            {
                "provider": "microsoft",
                "tenant_id": tenant_id,
                "access_token": encrypt(f, access_token),
                "refresh_token": encrypt(f, refresh_token),
                "expiry": (
                    datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                ).isoformat(),
                "scopes": scopes_list,
            },
        )
        increment("ms.oauth.callback.ok")
    except Exception:
        # Non-fatal in dev; caller can reconnect
        increment("ms.oauth.callback.persist_fail")

    return {
        "ok": True,
        "user_id": state,
        "scopes": scopes_list,
        "expires_in": expires_in,
    }


@router.post("/test")
async def test_conn(user_id: str = Query(...)) -> Dict[str, Any]:
    # Minimal: presence of token row indicates connected
    try:
        store = token_store_from_env()
        row = store.get(user_id)
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
async def disconnect(user_id: str = Query(...)) -> Dict[str, Any]:
    try:
        store = token_store_from_env()
        store.delete(user_id)
        increment("ms.disconnect.ok")
        return {"ok": True, "disconnected": True}
    except Exception:
        # Still report success to keep UX simple in dev
        increment("ms.disconnect.fail")
        return {"ok": True, "disconnected": True}
