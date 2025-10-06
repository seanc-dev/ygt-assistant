from __future__ import annotations
from typing import Any, Dict
from uuid import uuid4
from .store import CoreMemoryItem, get_store

_store = get_store()


def write_episodic(event: Dict[str, Any], meta: Dict[str, Any] | None = None) -> CoreMemoryItem:
    item = CoreMemoryItem(id=str(uuid4()), level="episodic", key=event.get("key", "*"), value=event, meta=meta)
    _store.upsert(item)
    return item


def write_semantic(fact: str, source: str | None = None) -> CoreMemoryItem:
    item = CoreMemoryItem(id=str(uuid4()), level="semantic", key=fact, value={"fact": fact}, meta={"source": source} if source else None)
    _store.upsert(item)
    return item


def write_procedural(how_to: str, source: str | None = None) -> CoreMemoryItem:
    item = CoreMemoryItem(id=str(uuid4()), level="procedural", key=how_to, value={"how_to": how_to}, meta={"source": source} if source else None)
    _store.upsert(item)
    return item


def write_narrative(journal: str, tags: list[str] | None = None) -> CoreMemoryItem:
    item = CoreMemoryItem(id=str(uuid4()), level="narrative", key=journal[:64], value={"journal": journal, "tags": tags or []})
    _store.upsert(item)
    return item
