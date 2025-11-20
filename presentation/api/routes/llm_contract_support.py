"""Helpers for wiring LucidWork LLM contract data into routes."""
from __future__ import annotations

from typing import Any, Dict, Optional

from core.chat.context import ThreadContext
from core.chat.focus import FocusCandidates, UiContext
from core.chat.tokens import ParsedMessage
from core.chat.validation import ResolvedReference, ValidationOk


def _candidate_metadata_from_context(context: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    tasks = context.get("tasks", []) if context else []
    projects = context.get("projects", []) if context else []
    actions = context.get("actions", []) if context else []
    return {
        "tasks": {t.get("id"): t.get("title") or t.get("name") or "" for t in tasks if t.get("id")},
        "projects": {p.get("id"): p.get("name") or "" for p in projects if p.get("id")},
        "actions": {
            a.get("id"): a.get("preview") or a.get("title") or ""
            for a in actions
            if a.get("id")
        },
    }


def build_contract_payload(
    *,
    parsed_message: ParsedMessage,
    thread_context: ThreadContext,
    ui_context: UiContext,
    focus_candidates: Optional[FocusCandidates],
    validation: Optional[ValidationOk],
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Assemble payload passed to LLM service for contract compliance."""

    payload: Dict[str, Any] = {
        "parsed_message": parsed_message.to_dict(),
        "thread_context": thread_context.to_dict(),
        "ui_context": ui_context.to_dict(),
        "focus_candidates": focus_candidates.to_dict() if focus_candidates else {},
        "candidate_metadata": _candidate_metadata_from_context(context or {}),
    }

    if validation:
        payload["resolved_references"] = [ref.to_dict() for ref in validation.resolved_references]
    else:
        payload["resolved_references"] = []

    return payload


__all__ = ["build_contract_payload"]
