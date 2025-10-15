from typing import Dict, Any, Optional
from infra.repos.settings_interfaces import SettingsRepo

_store: Dict[str, Dict[str, str]] = {}


class MemorySettingsRepo(SettingsRepo):
    def get_all(self, tenant_id: str) -> Dict[str, Any]:
        return dict(_store.get(tenant_id, {}))

    def get(self, tenant_id: str, key: str) -> Optional[str]:
        return (_store.get(tenant_id) or {}).get(key)

    def set_many(self, tenant_id: str, data: Dict[str, str]) -> None:
        cur = _store.setdefault(tenant_id, {})
        cur.update({k: str(v) for k, v in data.items()})
