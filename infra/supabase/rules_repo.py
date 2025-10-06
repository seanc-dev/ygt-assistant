import httpx
from infra.repos.tenant_rules_interfaces import RulesRepo
from settings import SUPABASE_URL, SUPABASE_SERVICE_KEY


class SupabaseRulesRepo(RulesRepo):
    def __init__(self) -> None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise RuntimeError("Supabase not configured")
        self._base = f"{SUPABASE_URL}/rest/v1"
        self._headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        }

    def get_yaml(self, tenant_id: str) -> str | None:
        with httpx.Client(
            headers=self._headers,
            timeout=httpx.Timeout(4.0, connect=2.0, read=4.0, write=4.0),
        ) as c:
            r = c.get(
                f"{self._base}/rules",
                params={"tenant_id": f"eq.{tenant_id}", "select": "yaml"},
            )
            r.raise_for_status()
            arr = r.json()
            return arr[0]["yaml"] if arr else None

    def set_yaml(self, tenant_id: str, yaml_text: str) -> None:
        with httpx.Client(
            headers=self._headers,
            timeout=httpx.Timeout(4.0, connect=2.0, read=4.0, write=4.0),
        ) as c:
            r = c.post(
                f"{self._base}/rules",
                json={"tenant_id": tenant_id, "yaml": yaml_text},
                params={"on_conflict": "tenant_id", "return": "minimal"},
            )
            r.raise_for_status()
