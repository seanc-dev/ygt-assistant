from __future__ import annotations
from typing import Dict, Any
import os
from datetime import datetime, timedelta, timezone
import httpx

try:
    from fastapi import APIRouter, HTTPException, Query  # type: ignore[import]
    from fastapi.responses import RedirectResponse  # type: ignore[import]
except Exception:  # pragma: no cover
    # Minimal stubs to satisfy static analysis when FastAPI isn't available
    class APIRouter:  # type: ignore
        def __init__(self, *_args, **_kwargs):
            pass

        def get(self, *_args, **_kwargs):  # type: ignore
            def _wrap(fn):
                return fn

            return _wrap

        def post(self, *_args, **_kwargs):  # type: ignore
            def _wrap(fn):
                return fn

            return _wrap

    class HTTPException(Exception):  # type: ignore
        def __init__(self, status_code: int = 500, detail: str = ""):
            self.status_code = status_code
            super().__init__(detail)

    def Query(default=None, **_kwargs):  # type: ignore
        return default

    class RedirectResponse:  # type: ignore
        def __init__(self, url: str, status_code: int = 302):
            self.url = url
            self.status_code = status_code


from utils.crypto import fernet_from, encrypt
from settings import ENCRYPTION_KEY
from infra.supabase.token_repo import TokenRepo


router = APIRouter(prefix="/connections/google", tags=["connections-google"])


def _oauth_client() -> Dict[str, str]:
    cid = os.getenv("GMAIL_CLIENT_ID") or os.getenv("GOOGLE_CLIENT_ID") or ""
    secret = os.getenv("GMAIL_CLIENT_SECRET") or os.getenv("GOOGLE_CLIENT_SECRET") or ""
    redirect = os.getenv("GMAIL_REDIRECT_URI") or os.getenv("GOOGLE_REDIRECT_URI") or ""
    if not cid or not secret or not redirect:
        raise HTTPException(status_code=500, detail="google_oauth_not_configured")
    return {"client_id": cid, "client_secret": secret, "redirect_uri": redirect}


@router.get("/oauth/start")
async def oauth_start(user_id: str = Query(...)) -> RedirectResponse:
    cfg = _oauth_client()
    scopes = [
        "openid",
        "email",
        "profile",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/calendar",
    ]
    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": cfg["redirect_uri"],
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent",
        "state": user_id,
    }
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        + "?"
        + str(httpx.QueryParams(params))
    )
    return RedirectResponse(url=url, status_code=302)


@router.get("/oauth/callback")
async def oauth_callback(
    code: str = Query(...), state: str = Query(...)
) -> Dict[str, Any]:
    cfg = _oauth_client()
    data = {
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": cfg["redirect_uri"],
    }
    async with httpx.AsyncClient(timeout=15) as c:
        resp = await c.post("https://oauth2.googleapis.com/token", data=data)
        resp.raise_for_status()
        tok = resp.json()
    user_id = state
    access_token = tok.get("access_token") or ""
    refresh_token = tok.get("refresh_token") or ""
    expires_in = int(tok.get("expires_in") or 3600)
    expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    scope_str = tok.get("scope") or ""
    scopes = [s for s in scope_str.split(" ") if s]
    f, _ = fernet_from(ENCRYPTION_KEY)
    TokenRepo().upsert(
        user_id=user_id,
        provider="google",
        access_token_encrypted=encrypt(f, access_token),
        refresh_token_encrypted=encrypt(f, refresh_token),
        expiry=expiry,
        scopes=scopes,
    )
    return {
        "ok": True,
        "user_id": user_id,
        "scopes": scopes,
        "expires_at": expiry.isoformat(),
    }


@router.get("/status")
async def status(user_id: str = Query(...)) -> Dict[str, Any]:
    rec = TokenRepo().get(user_id)
    if not rec:
        return {"connected": False}
    return {
        "connected": True,
        "provider": rec.get("provider"),
        "scopes": rec.get("scopes") or [],
        "expiry": rec.get("expiry"),
    }


@router.post("/disconnect")
async def disconnect(user_id: str = Query(...)) -> Dict[str, Any]:
    # Soft disconnect: delete row; revocation optional (not implemented here)
    rec = TokenRepo().get(user_id)
    if not rec:
        return {"ok": True, "disconnected": False}
    from archive.infra.supabase.client import client as _sb

    with _sb() as c:
        r = c.delete("/oauth_tokens", params={"user_id": f"eq.{user_id}"})
        r.raise_for_status()
    return {"ok": True, "disconnected": True}
