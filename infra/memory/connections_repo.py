from typing import Dict, Any, Optional, Tuple, List
from infra.repos.connections_interfaces import ConnectionsRepo

_conn: Dict[Tuple[str, str], Dict[str, Any]] = {}


class MemoryConnectionsRepo(ConnectionsRepo):
    def upsert(
        self,
        tenant_id: str,
        provider: str,
        access_token_encrypted: str,
        refresh_token_encrypted: str | None,
        meta: Dict[str, Any],
    ) -> None:
        _conn[(tenant_id, provider)] = {
            "tenant_id": tenant_id,
            "provider": provider,
            "access_token_encrypted": access_token_encrypted,
            "refresh_token_encrypted": refresh_token_encrypted,
            "meta": meta,
        }

    def get(self, tenant_id: str, provider: str) -> Optional[Dict[str, Any]]:
        return _conn.get((tenant_id, provider))

    def list_for_tenant(self, tenant_id: str, provider: str) -> List[Dict[str, Any]]:
        """List all connections for a tenant and provider."""
        return [
            conn for (tid, prov), conn in _conn.items()
            if tid == tenant_id and prov == provider
        ]


