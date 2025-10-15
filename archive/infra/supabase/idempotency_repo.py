from infra.repos.interfaces import IdempotencyRepo
from settings import SUPABASE_URL, SUPABASE_SERVICE_KEY
import httpx


class SupabaseIdempotencyRepo(IdempotencyRepo):
    def __init__(self) -> None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise RuntimeError("Supabase not configured")
        self._base = f"{SUPABASE_URL}/rest/v1"
        self._headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        }

    def seen(self, tenant_id: str, kind: str, external_id: str) -> bool:
        with httpx.Client(
            headers=self._headers,
            timeout=httpx.Timeout(4.0, connect=2.0, read=4.0, write=4.0),
        ) as c:
            r = c.get(
                f"{self._base}/dedupe_keys",
                params={
                    "tenant_id": f"eq.{tenant_id}",
                    "kind": f"eq.{kind}",
                    "external_id": f"eq.{external_id}",
                    "select": "external_id",
                },
            )
            r.raise_for_status()
            return len(r.json()) > 0

    def record(self, tenant_id: str, kind: str, external_id: str) -> None:
        with httpx.Client(
            headers=self._headers,
            timeout=httpx.Timeout(4.0, connect=2.0, read=4.0, write=4.0),
        ) as c:
            r = c.post(
                f"{self._base}/dedupe_keys",
                json={"tenant_id": tenant_id, "kind": kind, "external_id": external_id},
            )
            r.raise_for_status()
