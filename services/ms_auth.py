from __future__ import annotations
from typing import Any, Dict, Optional
from datetime import datetime, timezone, timedelta
import os
import httpx

from utils.crypto import fernet_from, decrypt
from settings import ENCRYPTION_KEY


class MsTokenStore:
    """Minimal token accessor for oauth_tokens table via Supabase REST.

    For MVP we rely on Supabase REST; later, use typed repos.
    """

    def __init__(self, base_url: str, api_key: str):
        self._base = base_url.rstrip("/") + "/rest/v1"
        self._headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def get(self, user_id: str) -> Optional[Dict[str, Any]]:
        with httpx.Client(timeout=8) as c:
            r = c.get(
                f"{self._base}/oauth_tokens",
                params={"user_id": f"eq.{user_id}", "select": "*"},
                headers=self._headers,
            )
            r.raise_for_status()
            items = r.json()
            return items[0] if items else None

    def upsert(self, user_id: str, data: Dict[str, Any]) -> None:
        with httpx.Client(timeout=8) as c:
            payload = {"user_id": user_id, **data}
            r = c.post(
                f"{self._base}/oauth_tokens", json=payload, headers=self._headers
            )
            if r.status_code == 409:
                c.patch(
                    f"{self._base}/oauth_tokens",
                    params={"user_id": f"eq.{user_id}"},
                    json=data,
                    headers=self._headers,
                )

    def delete(self, user_id: str) -> None:
        with httpx.Client(timeout=8) as c:
            r = c.delete(
                f"{self._base}/oauth_tokens",
                params={"user_id": f"eq.{user_id}"},
                headers=self._headers,
            )
            # treat 204/200 as success; 404 means already gone
            if r.status_code not in (200, 204):
                r.raise_for_status()


def token_store_from_env() -> MsTokenStore:
    base_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    api_key = os.getenv("SUPABASE_API_SECRET", "")
    if not base_url or not api_key:
        raise RuntimeError("supabase_not_configured for token store")
    return MsTokenStore(base_url, api_key)


def needs_refresh(expiry_iso: str, skew_seconds: int = 120) -> bool:
    try:
        exp = datetime.fromisoformat(expiry_iso)
    except Exception:
        return True
    return exp < (datetime.now(timezone.utc) + timedelta(seconds=skew_seconds))


async def ensure_access_token(
    user_id: str, token_row: Dict[str, Any], tenant_id: str
) -> str:
    """Return a valid bearer token, refreshing if needed."""
    f, _ = fernet_from(ENCRYPTION_KEY)
    access_token = (
        decrypt(f, token_row["access_token"]) if token_row.get("access_token") else ""
    )
    refresh_token = (
        decrypt(f, token_row["refresh_token"]) if token_row.get("refresh_token") else ""
    )
    expiry = token_row.get("expiry") or ""
    if access_token and expiry and not needs_refresh(expiry):
        return access_token

    # Refresh
    # Note: client_id/secret provided via env; for MVP assume confidential client
    client_id = os.getenv("MS_CLIENT_ID", "")
    client_secret = os.getenv("MS_CLIENT_SECRET", "")
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": "User.Read offline_access Mail.ReadWrite Mail.Send Calendars.ReadWrite",
    }
    token_url = (
        f"https://login.microsoftonline.com/{tenant_id or 'common'}/oauth2/v2.0/token"
    )
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(token_url, data=data)
        r.raise_for_status()
        t = r.json()
        return t.get("access_token") or ""
