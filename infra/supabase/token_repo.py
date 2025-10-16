from __future__ import annotations
from typing import Any, Dict, Optional
from datetime import datetime

from archive.infra.supabase.client import client


class TokenRepo:
    def get(self, user_id: str) -> Optional[Dict[str, Any]]:
        with client() as c:
            r = c.get(
                "/oauth_tokens", params={"user_id": f"eq.{user_id}", "select": "*"}
            )
            r.raise_for_status()
            items = r.json()
            return items[0] if items else None

    def upsert(
        self,
        user_id: str,
        provider: str,
        access_token_encrypted: str,
        refresh_token_encrypted: str,
        expiry: datetime,
        scopes: list[str],
    ) -> None:
        payload = {
            "user_id": user_id,
            "provider": provider,
            "access_token": access_token_encrypted,
            "refresh_token": refresh_token_encrypted,
            "expiry": expiry.isoformat(),
            "scopes": scopes,
        }
        with client() as c:
            r = c.post("/oauth_tokens", json=payload)
            if r.status_code == 409:
                # update existing
                r = c.patch(
                    "/oauth_tokens",
                    params={"user_id": f"eq.{user_id}"},
                    json={k: v for k, v in payload.items() if k != "user_id"},
                )
            r.raise_for_status()
