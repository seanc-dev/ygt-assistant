from typing import Dict, Any
from infra.repos.interfaces import AuditRepo
from settings import SUPABASE_URL, SUPABASE_SERVICE_KEY
import httpx


class SupabaseAuditRepo(AuditRepo):
    def __init__(self) -> None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise RuntimeError("Supabase not configured")
        self._base = f"{SUPABASE_URL}/rest/v1"
        self._headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        }

    def write(self, entry: Dict[str, Any]) -> str:
        rid = entry.get("request_id")
        with httpx.Client(
            headers=self._headers,
            timeout=httpx.Timeout(4.0, connect=2.0, read=4.0, write=4.0),
        ) as c:
            r = c.post(f"{self._base}/audit_log", json=entry)
            r.raise_for_status()
            return rid or (
                r.json()[0].get("request_id", "")
                if isinstance(r.json(), list) and r.json()
                else ""
            )

    def get(self, request_id: str) -> Dict[str, Any]:
        with httpx.Client(
            headers=self._headers,
            timeout=httpx.Timeout(4.0, connect=2.0, read=4.0, write=4.0),
        ) as c:
            r = c.get(
                f"{self._base}/audit_log",
                params={"request_id": f"eq.{request_id}", "select": "*"},
            )
            r.raise_for_status()
            rows = r.json()
            return rows[0] if rows else {}
