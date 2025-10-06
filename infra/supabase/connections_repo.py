import httpx
from typing import Dict, Any, Optional, List
from infra.repos.connections_interfaces import ConnectionsRepo
from settings import SUPABASE_URL, SUPABASE_SERVICE_KEY


class SupabaseConnectionsRepo(ConnectionsRepo):
    def __init__(self) -> None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise RuntimeError("Supabase not configured")
        self._base = f"{SUPABASE_URL}/rest/v1"
        self._headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Prefer": "return=minimal",
        }

    def upsert(
        self,
        tenant_id: str,
        provider: str,
        access_token_encrypted: str,
        refresh_token_encrypted: str | None,
        meta: Dict[str, Any],
    ) -> None:
        body = {
            "tenant_id": tenant_id,
            "provider": provider,
            "access_token_encrypted": access_token_encrypted,
            "refresh_token_encrypted": refresh_token_encrypted,
            "meta": meta,
        }
        with httpx.Client(
            headers=self._headers,
            timeout=httpx.Timeout(4.0, connect=2.0, read=4.0, write=4.0),
        ) as c:
            r = c.post(
                f"{self._base}/connections",
                json=body,
                params={"on_conflict": "tenant_id,provider"},
            )
            r.raise_for_status()

    def get(self, tenant_id: str, provider: str) -> Optional[Dict[str, Any]]:
        with httpx.Client(
            headers=self._headers,
            timeout=httpx.Timeout(4.0, connect=2.0, read=4.0, write=4.0),
        ) as c:
            r = c.get(
                f"{self._base}/connections",
                params={
                    "tenant_id": f"eq.{tenant_id}",
                    "provider": f"eq.{provider}",
                    "select": "*",
                },
            )
            r.raise_for_status()
            arr = r.json()
            return arr[0] if arr else None

    def list_for_tenant(self, tenant_id: str, provider: str) -> List[Dict[str, Any]]:
        """List all connections for a tenant and provider."""
        with httpx.Client(
            headers=self._headers,
            timeout=httpx.Timeout(4.0, connect=2.0, read=4.0, write=4.0),
        ) as c:
            r = c.get(
                f"{self._base}/connections",
                params={
                    "tenant_id": f"eq.{tenant_id}",
                    "provider": f"eq.{provider}",
                    "select": "*",
                },
            )
            r.raise_for_status()
            return r.json()

    def list_exists_for_tenants(
        self, tenant_ids: List[str]
    ) -> Dict[str, Dict[str, bool]]:
        """Return existence flags per provider for multiple tenants.

        { tenant_id: { 'notion': bool, 'nylas': bool } }
        """
        if not tenant_ids:
            return {}
        ids = ",".join(tenant_ids)
        with httpx.Client(headers=self._headers, timeout=10) as c:
            r = c.get(
                f"{self._base}/connections",
                params={"tenant_id": f"in.({ids})", "select": "tenant_id,provider"},
            )
            r.raise_for_status()
            out: Dict[str, Dict[str, bool]] = {}
            for row in r.json():
                tid = row["tenant_id"]
                prov = row["provider"]
                flags = out.setdefault(tid, {"notion": False, "nylas": False})
                if prov in flags:
                    flags[prov] = True
            return out
