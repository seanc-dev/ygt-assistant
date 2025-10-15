from typing import Dict, Any
import httpx
from infra.repos.interfaces import UsersRepo
from settings import SUPABASE_URL, SUPABASE_SERVICE_KEY


class SupabaseUsersRepo(UsersRepo):
    def __init__(self) -> None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise RuntimeError("Supabase not configured")
        self._base = f"{SUPABASE_URL}/rest/v1"
        self._headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def upsert(
        self,
        tenant_id: str,
        email: str,
        name: str | None,
        password_hash: str,
        must_change: bool = True,
    ) -> str:
        payload = {
            "tenant_id": tenant_id,
            "email": email,
            "name": name,
            "password_hash": password_hash,
            "must_change_password": must_change,
        }
        with httpx.Client(
            headers=self._headers,
            timeout=httpx.Timeout(4.0, connect=2.0, read=4.0, write=4.0),
        ) as c:
            r = c.post(f"{self._base}/users", json=payload)
            if r.status_code == 409:
                # existing: update
                r = c.patch(
                    f"{self._base}/users",
                    params={"email": f"eq.{email}"},
                    json={
                        k: v
                        for k, v in payload.items()
                        if k not in {"tenant_id", "email"}
                    },
                )
            r.raise_for_status()
            data = r.json()
            row = data[0] if isinstance(data, list) else data
            return row.get("id")

    def get_by_email(self, email: str) -> Dict[str, Any] | None:
        with httpx.Client(
            headers=self._headers,
            timeout=httpx.Timeout(4.0, connect=2.0, read=4.0, write=4.0),
        ) as c:
            r = c.get(
                f"{self._base}/users", params={"email": f"eq.{email}", "select": "*"}
            )
            r.raise_for_status()
            arr = r.json()
            return arr[0] if arr else None

    def get_by_id(self, user_id: str) -> Dict[str, Any] | None:
        with httpx.Client(
            headers=self._headers,
            timeout=httpx.Timeout(4.0, connect=2.0, read=4.0, write=4.0),
        ) as c:
            r = c.get(
                f"{self._base}/users", params={"id": f"eq.{user_id}", "select": "*"}
            )
            r.raise_for_status()
            arr = r.json()
            return arr[0] if arr else None

    def update_password(
        self, user_id: str, new_password_hash: str, must_change: bool = False
    ) -> None:
        with httpx.Client(
            headers=self._headers,
            timeout=httpx.Timeout(4.0, connect=2.0, read=4.0, write=4.0),
        ) as c:
            r = c.patch(
                f"{self._base}/users",
                params={"id": f"eq.{user_id}"},
                json={
                    "password_hash": new_password_hash,
                    "must_change_password": must_change,
                },
            )
            r.raise_for_status()

    def update_profile(self, user_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        payload = {k: v for k, v in patch.items() if k in {"name"}}
        if not payload:
            return self.get_by_id(user_id) or {}
        with httpx.Client(
            headers=self._headers,
            timeout=httpx.Timeout(4.0, connect=2.0, read=4.0, write=4.0),
        ) as c:
            r = c.patch(
                f"{self._base}/users", params={"id": f"eq.{user_id}"}, json=payload
            )
            r.raise_for_status()
            out = c.get(
                f"{self._base}/users", params={"id": f"eq.{user_id}", "select": "*"}
            )
            out.raise_for_status()
            arr = out.json()
            return arr[0] if arr else {}
