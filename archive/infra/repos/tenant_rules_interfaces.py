from typing import Dict, Any, Optional, List


class TenantsRepo:
    def create(self, name: str) -> str:  # pragma: no cover - interface
        ...

    def list(self) -> List[Dict[str, Any]]:  # pragma: no cover - interface
        ...

    def exists(self, tenant_id: str) -> bool:  # pragma: no cover - interface
        ...


class RulesRepo:
    def get_yaml(self, tenant_id: str) -> str | None:  # pragma: no cover - interface
        ...

    def set_yaml(self, tenant_id: str, yaml_text: str) -> None:  # pragma: no cover - interface
        ...


