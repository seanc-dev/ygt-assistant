from typing import Set, Tuple
from infra.repos.interfaces import IdempotencyRepo

_keys: Set[Tuple[str, str, str]] = set()


class MemoryIdempotencyRepo(IdempotencyRepo):
    def seen(self, tenant_id: str, kind: str, external_id: str) -> bool:
        return (tenant_id, kind, external_id) in _keys

    def record(self, tenant_id: str, kind: str, external_id: str) -> None:
        _keys.add((tenant_id, kind, external_id))


