import yaml
from typing import Optional
from core.config.model import AppCfg, normalize
from infra.repos import settings_factory

KEY = "notion_config_yaml"

def load_for_tenant(tenant_id: str) -> Optional[AppCfg]:
    repo = settings_factory.repo()
    y = repo.get(tenant_id, KEY)
    if not y:
        return None
    data = yaml.safe_load(y) or {}
    return normalize(data)

def save_for_tenant(tenant_id: str, yaml_text: str) -> None:
    repo = settings_factory.repo()
    # Lightweight sanity parse
    try:
        data = yaml.safe_load(yaml_text) or {}
        _ = normalize(data)
    except yaml.YAMLError as e:
        raise ValueError(f"invalid_yaml: {e}")
    except ValueError as e:
        raise e
    repo.set_many(tenant_id, {KEY: yaml_text})
