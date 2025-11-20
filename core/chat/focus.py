"""Focus resolution helpers when messages have no tokens."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

from core.chat.context import ThreadContext
from core.chat.tokens import ParsedMessage

UiMode = Literal["hub", "workroom-task", "workroom-project"]


def _uniquify(values: List[Optional[str]], exclude: Optional[str] = None) -> List[str]:
    result: List[str] = []
    seen = set()
    for value in values:
        if not value or value == exclude or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


@dataclass
class UiContext:
    mode: UiMode
    hub_suggested_task_id: Optional[str] = None
    workroom_task_id: Optional[str] = None
    workroom_project_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {
            "mode": self.mode,
            "hub_suggested_task_id": self.hub_suggested_task_id,
            "workroom_task_id": self.workroom_task_id,
            "workroom_project_id": self.workroom_project_id,
        }


@dataclass
class FocusCandidates:
    default_task_id: Optional[str] = None
    default_project_id: Optional[str] = None
    candidate_task_ids: List[str] = field(default_factory=list)
    candidate_project_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "default_task_id": self.default_task_id,
            "default_project_id": self.default_project_id,
            "candidate_task_ids": list(self.candidate_task_ids),
            "candidate_project_ids": list(self.candidate_project_ids),
        }


def resolve_focus_candidates(
    thread_context: ThreadContext,
    ui_context: UiContext,
    parsed: ParsedMessage,
) -> FocusCandidates:
    """Determine deterministic focus IDs when no tokens are present."""

    # Tokens win. Candidates only matter if there are no references.
    if parsed.references:
        return FocusCandidates()

    candidates = FocusCandidates()

    if ui_context.mode == "workroom-task":
        candidates.default_task_id = (
            ui_context.workroom_task_id
            or thread_context.pinned_task_id
            or thread_context.last_task_id
        )
        candidates.default_project_id = (
            ui_context.workroom_project_id
            or thread_context.pinned_project_id
            or thread_context.last_project_id
        )
        candidates.candidate_task_ids = _uniquify(
            [thread_context.pinned_task_id]
            + thread_context.recent_task_ids,
            exclude=candidates.default_task_id,
        )
        candidates.candidate_project_ids = _uniquify(
            [thread_context.pinned_project_id]
            + thread_context.recent_project_ids,
            exclude=candidates.default_project_id,
        )
    elif ui_context.mode == "workroom-project":
        candidates.default_project_id = (
            ui_context.workroom_project_id
            or thread_context.pinned_project_id
            or thread_context.last_project_id
        )
        candidates.candidate_project_ids = _uniquify(
            [thread_context.pinned_project_id]
            + thread_context.recent_project_ids,
            exclude=candidates.default_project_id,
        )
    else:  # hub
        candidates.default_task_id = (
            ui_context.hub_suggested_task_id
            or thread_context.pinned_task_id
            or thread_context.last_task_id
        )
        candidates.candidate_task_ids = _uniquify(
            [thread_context.last_task_id]
            + thread_context.recent_task_ids,
            exclude=candidates.default_task_id,
        )
        candidates.candidate_project_ids = _uniquify(
            [thread_context.last_project_id]
            + thread_context.recent_project_ids,
            exclude=None,
        )

    return candidates


__all__ = [
    "FocusCandidates",
    "UiContext",
    "resolve_focus_candidates",
]
