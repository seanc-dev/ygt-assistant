import httpx
from typing import Dict, Any, Optional, List
from infra.repos.settings_interfaces import SettingsRepo
from settings import SUPABASE_URL, SUPABASE_SERVICE_KEY


class SupabaseSettingsRepo(SettingsRepo):
    def __init__(self) -> None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise RuntimeError("Supabase not configured")
        self._base = f"{SUPABASE_URL}/rest/v1"
        self._headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            # PostgREST expects return preference in the Prefer header, not as a query param
            "Prefer": "resolution=merge-duplicates,return=minimal",
        }
        self._client = httpx.Client(
            headers=self._headers,
            timeout=httpx.Timeout(4.0, connect=2.0, read=4.0, write=4.0),
            transport=httpx.HTTPTransport(retries=1),
        )

    def get_all(self, tenant_id: str) -> Dict[str, Any]:
        c = self._client
        r = c.get(
            f"{self._base}/tenant_settings",
            params={"tenant_id": f"eq.{tenant_id}", "select": "key,value"},
        )
        r.raise_for_status()
        return {row["key"]: row["value"] for row in r.json()}

    def get_all_for_tenants(self, tenant_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Batch fetch settings for multiple tenants.

        Returns mapping of tenant_id -> {key: value}.
        """
        if not tenant_ids:
            return {}
        # PostgREST IN filter: in.(val1,val2)
        ids = ",".join(tenant_ids)
        c = self._client
        r = c.get(
            f"{self._base}/tenant_settings",
            params={"tenant_id": f"in.({ids})", "select": "tenant_id,key,value"},
        )
        r.raise_for_status()
        out: Dict[str, Dict[str, Any]] = {}
        for row in r.json():
            tid = row["tenant_id"]
            out.setdefault(tid, {})[row["key"]] = row["value"]
        return out

    def get(self, tenant_id: str, key: str) -> Optional[str]:
        c = self._client
        r = c.get(
            f"{self._base}/tenant_settings",
            params={
                "tenant_id": f"eq.{tenant_id}",
                "key": f"eq.{key}",
                "select": "value",
            },
        )
        r.raise_for_status()
        arr = r.json()
        return arr[0]["value"] if arr else None

    def set_many(self, tenant_id: str, data: Dict[str, str]) -> None:
        # Upsert each key individually to avoid composite upsert quirks and to surface precise errors
        c = self._client
        for k, v in (data or {}).items():
            payload = {"tenant_id": tenant_id, "key": k, "value": v}
            r = c.post(
                f"{self._base}/tenant_settings",
                json=[payload],
                params={"on_conflict": "tenant_id,key"},
            )
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                detail = getattr(e.response, "text", "") or str(e)
                raise httpx.HTTPStatusError(
                    f"settings_upsert_failed for key={k}: {detail}",
                    request=e.request,
                    response=e.response,
                )
