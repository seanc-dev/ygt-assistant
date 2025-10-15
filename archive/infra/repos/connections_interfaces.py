from typing import Dict, Any, Optional, List


class ConnectionsRepo:
    def upsert(
        self,
        tenant_id: str,
        provider: str,
        access_token_encrypted: str,
        refresh_token_encrypted: str | None,
        meta: Dict[str, Any],
    ) -> None:  # pragma: no cover - interface
        ...

    def get(self, tenant_id: str, provider: str) -> Optional[Dict[str, Any]]:  # pragma: no cover - interface
        ...

    def list_for_tenant(self, tenant_id: str, provider: str) -> List[Dict[str, Any]]:  # pragma: no cover - interface
        ...


