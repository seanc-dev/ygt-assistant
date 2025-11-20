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


def context_for(target: str, *, limit_per_level: int = 5) -> Dict[str, List[CoreMemoryItem]]:
    """Return recent core memories grouped by level.

    The previous implementation returned empty context buckets because it
    queried a placeholder "*" key that no memories used. To ensure the
    assistant can actually "learn" from stored user facts and journals, this
    now pulls the latest items for each level directly.
    """

    levels = ["episodic", "semantic", "procedural", "narrative"]
    ctx: Dict[str, List[CoreMemoryItem]] = {}

    for lvl in levels:
        items = _store.list_by_level(lvl)
        if limit_per_level > 0:
            items = items[:limit_per_level]
        ctx[lvl] = items

    return ctx
