from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
import os

CORE_ENABLE_VECTORS = (os.getenv("CORE_ENABLE_VECTORS", "false").lower() in {"1","true","yes","on"})

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


def get_store() -> InMemoryCoreStore:
    # For POC, return in-memory store. Later, wire Supabase-backed store via env USE_DB.
    return InMemoryCoreStore()
