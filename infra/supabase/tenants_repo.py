import httpx
from typing import Dict, Any, List
from infra.repos.tenant_rules_interfaces import TenantsRepo
from settings import SUPABASE_URL, SUPABASE_SERVICE_KEY


class SupabaseTenantsRepo(TenantsRepo):
    def __init__(self) -> None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise RuntimeError("Supabase not configured")
        self._base = f"{SUPABASE_URL}/rest/v1"
        self._headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
        }

    def create(self, name: str) -> str:
        # Request representation so we can parse the created row id
        pref_headers = {**self._headers, "Prefer": "return=representation"}
        with httpx.Client(
            headers=pref_headers,
            timeout=httpx.Timeout(4.0, connect=2.0, read=4.0, write=4.0),
        ) as c:
            r = c.post(f"{self._base}/tenants", json={"name": name})
            r.raise_for_status()
            data = r.json()
            row = data[0] if isinstance(data, list) else data
            return row.get("id")

    def list(self) -> List[Dict[str, Any]]:
        with httpx.Client(
            headers=self._headers,
            timeout=httpx.Timeout(4.0, connect=2.0, read=4.0, write=4.0),
        ) as c:
            r = c.get(f"{self._base}/tenants", params={"select": "*"})
            r.raise_for_status()
            return r.json()

    def exists(self, tenant_id: str) -> bool:
        with httpx.Client(
            headers=self._headers,
            timeout=httpx.Timeout(4.0, connect=2.0, read=4.0, write=4.0),
        ) as c:
            r = c.get(
                f"{self._base}/tenants",
                params={"id": f"eq.{tenant_id}", "select": "id"},
            )
            r.raise_for_status()
            return len(r.json()) > 0
