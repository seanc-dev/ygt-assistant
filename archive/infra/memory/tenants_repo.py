import uuid
from typing import Dict, Any, List
from infra.repos.tenant_rules_interfaces import TenantsRepo

_tenants: Dict[str, Dict[str, Any]] = {}


class MemoryTenantsRepo(TenantsRepo):
    def create(self, name: str) -> str:
        tid = str(uuid.uuid4())
        _tenants[tid] = {"id": tid, "name": name}
        return tid

    def list(self) -> List[Dict[str, Any]]:
        return list(_tenants.values())

    def exists(self, tenant_id: str) -> bool:
        return tenant_id in _tenants


