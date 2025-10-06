from __future__ import annotations
from typing import Any, Dict, List, Optional
from .store import get_store, CoreMemoryItem, CORE_ENABLE_VECTORS

_store = get_store()


def recall_by_key(key: str, level: Optional[str] = None) -> List[CoreMemoryItem]:
    return _store.get_by_key(key, level)


def recall_similar(text: str, top_k: int = 5) -> List[CoreMemoryItem]:
    if not CORE_ENABLE_VECTORS:
        return []
    # Placeholder: vector search behind feature flag; integrate embeddings later
    return []


def context_for(target: str) -> Dict[str, List[CoreMemoryItem]]:
    # Simple heuristic: group latest items by level for now
    levels = ["episodic", "semantic", "procedural", "narrative"]
    ctx: Dict[str, List[CoreMemoryItem]] = {}
    for lvl in levels:
        ctx[lvl] = _store.get_by_key(key="*", level=lvl)  # using wildcard pattern as placeholder
    return ctx
