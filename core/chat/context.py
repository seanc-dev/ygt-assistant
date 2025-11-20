"""Thread context helpers for LucidWork chat."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from core.chat.tokens import ParsedRef

_MAX_RECENT = 10
_THREAD_CONTEXTS: Dict[str, "ThreadContext"] = {}


def _dedupe(values: List[str]) -> List[str]:
    seen = set()
    deduped: List[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


def _prepend(existing: List[str], value: Optional[str]) -> List[str]:
    if not value:
        return existing[:]
    return _dedupe([value] + existing)[:_MAX_RECENT]


@dataclass
class ThreadContext:
    """Per-thread memory of the last referenced objects."""

    last_task_id: Optional[str] = None
    last_project_id: Optional[str] = None
    recent_task_ids: List[str] = field(default_factory=list)
    recent_project_ids: List[str] = field(default_factory=list)
    pinned_task_id: Optional[str] = None
    pinned_project_id: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "last_task_id": self.last_task_id,
            "last_project_id": self.last_project_id,
            "recent_task_ids": list(self.recent_task_ids),
            "recent_project_ids": list(self.recent_project_ids),
            "pinned_task_id": self.pinned_task_id,
            "pinned_project_id": self.pinned_project_id,
        }

    @classmethod
    def from_existing(cls, ctx: "ThreadContext") -> "ThreadContext":
        return cls(
            last_task_id=ctx.last_task_id,
            last_project_id=ctx.last_project_id,
            recent_task_ids=list(ctx.recent_task_ids),
            recent_project_ids=list(ctx.recent_project_ids),
            pinned_task_id=ctx.pinned_task_id,
            pinned_project_id=ctx.pinned_project_id,
        )


def load_thread_context(thread_id: str) -> ThreadContext:
    """Load thread context from the in-memory store."""

    if not thread_id:
        raise ValueError("thread_id is required to load thread context")
    ctx = _THREAD_CONTEXTS.get(thread_id)
    if not ctx:
        ctx = ThreadContext()
        _THREAD_CONTEXTS[thread_id] = ctx
    return ThreadContext.from_existing(ctx)


def save_thread_context(thread_id: str, ctx: ThreadContext) -> None:
    """Persist thread context back to the in-memory store."""

    if not thread_id:
        raise ValueError("thread_id is required to save thread context")
    _THREAD_CONTEXTS[thread_id] = ThreadContext.from_existing(ctx)


def update_thread_context_with_refs(
    ctx: ThreadContext, refs: List[ParsedRef]
) -> ThreadContext:
    """Update thread context based on reference tokens."""

    updated = ThreadContext.from_existing(ctx)

    for ref in refs:
        ref_type = ref.type.lower()
        if ref_type == "task":
            updated.last_task_id = ref.id
            updated.recent_task_ids = _prepend(updated.recent_task_ids, ref.id)
        elif ref_type == "project":
            updated.last_project_id = ref.id
            updated.recent_project_ids = _prepend(updated.recent_project_ids, ref.id)

    return updated


__all__ = [
    "ThreadContext",
    "load_thread_context",
    "save_thread_context",
    "update_thread_context_with_refs",
]
