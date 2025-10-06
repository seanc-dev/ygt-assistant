from typing import Dict, Any
import httpx
from infra.repos.interfaces import ClientSessionsRepo
from settings import SUPABASE_URL, SUPABASE_SERVICE_KEY


class SupabaseClientSessionsRepo(ClientSessionsRepo):
    def __init__(self) -> None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise RuntimeError("Supabase not configured")
        self._base = f"{SUPABASE_URL}/rest/v1"
        self._headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
        }

    def create(self, user_id: str, token: str, expires_at: str | None = None) -> None:
        payload = {"user_id": user_id, "token": token, "expires_at": expires_at}
        with httpx.Client(headers=self._headers, timeout=10) as c:
            r = c.post(f"{self._base}/client_sessions", json=payload)
            r.raise_for_status()

    def get(self, token: str) -> Dict[str, Any] | None:
        with httpx.Client(headers=self._headers, timeout=10) as c:
            r = c.get(
                f"{self._base}/client_sessions",
                params={"token": f"eq.{token}", "select": "*"},
            )
            r.raise_for_status()
            arr = r.json()
            return arr[0] if arr else None
