from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
import os

CORE_ENABLE_VECTORS = os.getenv("CORE_ENABLE_VECTORS", "false").lower() in {
    "1",
    "true",
    "yes",
    "on",
}


@dataclass
class CoreMemoryItem:
    id: str
    level: str  # episodic | semantic | procedural | narrative
    key: str
    value: Dict[str, Any]
    vector: Optional[List[float]] = None
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime = datetime.now()
    last_used_at: Optional[datetime] = None


class InMemoryCoreStore:
    def __init__(self) -> None:
        self._items: Dict[str, CoreMemoryItem] = {}

    def upsert(self, item: CoreMemoryItem) -> None:
        self._items[item.id] = item

    def get_by_id(self, item_id: str) -> Optional[CoreMemoryItem]:
        item = self._items.get(item_id)
        if item:
            item.last_used_at = datetime.now()
        return item

    def get_by_key(self, key: str, level: Optional[str] = None) -> List[CoreMemoryItem]:
        results = []
        for it in self._items.values():
            if it.key == key and (level is None or it.level == level):
                results.append(it)
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results

    def list_by_level(self, level: str) -> List[CoreMemoryItem]:
        items = [it for it in self._items.values() if it.level == level]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items


_STORE_SINGLETON: InMemoryCoreStore | None = None


def get_store() -> InMemoryCoreStore:
    # For POC, return a process-wide in-memory singleton store.
    global _STORE_SINGLETON
    if _STORE_SINGLETON is None:
        _STORE_SINGLETON = InMemoryCoreStore()
    return _STORE_SINGLETON
