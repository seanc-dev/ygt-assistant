from typing import Dict, Any


class IdempotencyRepo:
    def seen(
        self, tenant_id: str, kind: str, external_id: str
    ) -> bool:  # pragma: no cover - interface
        ...

    def record(
        self, tenant_id: str, kind: str, external_id: str
    ) -> None:  # pragma: no cover - interface
        ...


class AuditRepo:
    def write(self, entry: Dict[str, Any]) -> str:  # pragma: no cover - interface
        ...

    def get(self, request_id: str) -> Dict[str, Any]:  # pragma: no cover - interface
        ...


# Users
class UsersRepo:
    def upsert(
        self,
        tenant_id: str,
        email: str,
        name: str | None,
        password_hash: str,
        must_change: bool = True,
    ) -> str:  # pragma: no cover - interface
        ...

    def get_by_email(
        self, email: str
    ) -> Dict[str, Any] | None:  # pragma: no cover - interface
        ...

    def get_by_id(
        self, user_id: str
    ) -> Dict[str, Any] | None:  # pragma: no cover - interface
        ...

    def update_password(
        self, user_id: str, new_password_hash: str, must_change: bool = False
    ) -> None:  # pragma: no cover - interface
        ...

    def update_profile(
        self, user_id: str, patch: Dict[str, Any]
    ) -> Dict[str, Any]:  # pragma: no cover - interface
        ...


class ClientSessionsRepo:
    def create(
        self, user_id: str, token: str, expires_at: str | None = None
    ) -> None:  # pragma: no cover - interface
        ...

    def get(self, token: str) -> Dict[str, Any] | None:  # pragma: no cover - interface
        ...
