from typing import Dict
from infra.repos.tenant_rules_interfaces import RulesRepo

_rules: Dict[str, str] = {}


class MemoryRulesRepo(RulesRepo):
    def get_yaml(self, tenant_id: str) -> str | None:
        return _rules.get(tenant_id)

    def set_yaml(self, tenant_id: str, yaml_text: str) -> None:
        _rules[tenant_id] = yaml_text


