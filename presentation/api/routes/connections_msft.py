from __future__ import annotations
from typing import Any, Dict, Optional
import os
import base64
import secrets
import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse


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
    # MVP: return disconnected; later, check oauth_tokens via repo
    return {"connected": False}


@router.get("/oauth/start")
async def oauth_start(user_id: str = Query(...), tenant: str = Query("common")) -> RedirectResponse:
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
    url = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize".format(tenant=tenant)
    return RedirectResponse(url=f"{url}?" + httpx.QueryParams(params).render(), status_code=302)


@router.get("/oauth/callback")
async def oauth_callback(code: str = Query(...), state: str = Query(...), tenant: str = Query("common")) -> Dict[str, Any]:
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
    return {"ok": True, "user_id": state, "scopes": (tok.get("scope") or "").split(), "expires_in": tok.get("expires_in")}


@router.post("/test")
async def test_conn(user_id: str = Query(...)) -> Dict[str, Any]:
    # MVP: return ok to avoid external calls in dev
    return {"ok": True}


@router.post("/disconnect")
async def disconnect(user_id: str = Query(...)) -> Dict[str, Any]:
    return {"ok": True, "disconnected": True}


