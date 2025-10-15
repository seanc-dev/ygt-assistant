from typing import Dict, Any
from infra.repos.interfaces import UsersRepo
import uuid


class MemoryUsersRepo(UsersRepo):
    def __init__(self) -> None:
        self._by_email: Dict[str, Dict[str, Any]] = {}

    def upsert(
        self,
        tenant_id: str,
        email: str,
        name: str | None,
        password_hash: str,
        must_change: bool = True,
    ) -> str:
        row = self._by_email.get(email) or {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "email": email,
            "created_at": None,
        }
        row.update(
            {
                "name": name,
                "password_hash": password_hash,
                "must_change_password": must_change,
            }
        )
        self._by_email[email] = row
        return row["id"]

    def get_by_email(self, email: str) -> Dict[str, Any] | None:
        return self._by_email.get(email)

    def get_by_id(self, user_id: str) -> Dict[str, Any] | None:
        for row in self._by_email.values():
            if row.get("id") == user_id:
                return row
        return None

    def update_password(
        self, user_id: str, new_password_hash: str, must_change: bool = False
    ) -> None:
        for email, row in self._by_email.items():
            if row.get("id") == user_id:
                row["password_hash"] = new_password_hash
                row["must_change_password"] = must_change
                self._by_email[email] = row
                return

    def update_profile(self, user_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        for email, row in self._by_email.items():
            if row.get("id") == user_id:
                row.update({k: v for k, v in patch.items() if k in {"name"}})
                self._by_email[email] = row
                return row
        return {}
