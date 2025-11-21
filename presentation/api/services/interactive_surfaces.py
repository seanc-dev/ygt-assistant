"""Helpers for attaching interactive surfaces to LLM operations."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence
import logging

logger = logging.getLogger(__name__)


def normalize_surfaces(raw: Any) -> List[Dict[str, Any]]:
    """Sanitize LLM-provided surfaces before persisting or returning."""
    surfaces: List[Dict[str, Any]] = []
    if not isinstance(raw, Iterable):
        return surfaces

    for candidate in raw:
        if not isinstance(candidate, dict):
            continue
        surface_id = candidate.get("surface_id") or candidate.get("surfaceId")
        kind = candidate.get("kind")
        title = candidate.get("title")
        payload = candidate.get("payload")
        if not all(isinstance(value, str) for value in (surface_id, kind, title)):
            logger.debug("Skipping surface with invalid envelope: %s", candidate)
            continue
        if not isinstance(payload, dict):
            logger.debug("Skipping surface missing payload: %s", candidate)
            continue
        surfaces.append(
            {
                "surface_id": surface_id,
                "kind": kind,
                "title": title,
                "payload": payload,
            }
        )
    return surfaces


def attach_surfaces_to_first_chat_op(
    operations: Sequence[Any], surfaces: List[Dict[str, Any]]
) -> None:
    """Attach sanitized surfaces to the first chat operation in-place."""
    if not surfaces:
        return

    for op in operations:
        op_type = None
        if isinstance(op, dict):
            op_type = op.get("op")
        else:
            op_type = getattr(op, "op", None)
        if op_type == "chat":
            if isinstance(op, dict):
                params = op.setdefault("params", {})
                if isinstance(params, dict):
                    params["surfaces"] = surfaces
            else:
                params = getattr(op, "params", None)
                if isinstance(params, dict):
                    params["surfaces"] = surfaces
            break


def _is_valid_navigate_to(target: Dict[str, Any], *, tasks: set, events: set) -> bool:
    destination = target.get("destination")
    if destination == "workroom_task":
        return isinstance(target.get("taskId"), str) and target.get("taskId") in tasks
    if destination == "calendar_event":
        return isinstance(target.get("eventId"), str) and target.get("eventId") in events
    if destination in {"hub", "hub_queue"}:
        return True
    return False


def _contains_only_known_ids(
    surface: Dict[str, Any], *, tasks: set, events: set, docs: set, queue_items: set
) -> bool:
    """Check whether a surface references only IDs contained in surface_input."""

    kind = surface.get("kind")
    payload = surface.get("payload") or {}

    if kind == "what_next_v1":
        primary = payload.get("primary") or {}
        target = primary.get("target")
        if target and not _is_valid_navigate_to(target, tasks=tasks, events=events):
            return False
        actions = []
        primary_action = primary.get("primaryAction")
        if primary_action:
            actions.append(primary_action)
        actions.extend(primary.get("secondaryActions") or [])
        for action in actions:
            if not isinstance(action, dict):
                continue
            navigate_to = action.get("navigateTo")
            if navigate_to and not _is_valid_navigate_to(
                navigate_to, tasks=tasks, events=events
            ):
                return False
        return True

    if kind == "today_schedule_v1":
        for block in payload.get("blocks", []):
            if not isinstance(block, dict):
                continue
            task_id = block.get("taskId")
            event_id = block.get("eventId")
            if task_id and task_id not in tasks:
                return False
            if event_id and event_id not in events:
                return False
        return True

    if kind == "priority_list_v1":
        for item in payload.get("items", []):
            if not isinstance(item, dict):
                continue
            if item.get("taskId") not in tasks:
                return False
            navigate_to = item.get("navigateTo")
            if navigate_to and not _is_valid_navigate_to(
                navigate_to, tasks=tasks, events=events
            ):
                return False
        return True

    if kind == "triage_table_v1":
        for group in payload.get("groups", []):
            if not isinstance(group, dict):
                continue
            for item in group.get("items", []):
                if not isinstance(item, dict):
                    continue
                if item.get("queueItemId") not in queue_items:
                    return False
                suggested = item.get("suggestedTask") or {}
                suggested_task_id = suggested.get("taskId")
                if suggested_task_id and suggested_task_id not in tasks:
                    return False
        return True

    return True


def validate_workroom_surfaces(
    surfaces: List[Dict[str, Any]],
    surface_input: Dict[str, Any],
    *,
    limit: int = 2,
) -> List[Dict[str, Any]]:
    """Validate workroom surfaces against provided surface_input.

    Drops any surface that references IDs absent from surface_input and enforces
    a global limit to encourage concise, high-value surfaces.
    """

    allowed_tasks = {
        t.get("id")
        for t in surface_input.get("tasks", [])
        if isinstance(t, dict) and t.get("id")
    }
    allowed_events = {
        e.get("id")
        for e in surface_input.get("events", [])
        if isinstance(e, dict) and e.get("id")
    }
    allowed_docs = {
        d.get("id")
        for d in surface_input.get("docs", [])
        if isinstance(d, dict) and d.get("id")
    }
    allowed_queue_items = {
        q.get("id")
        for q in surface_input.get("queueItems", [])
        if isinstance(q, dict) and q.get("id")
    }

    validated: List[Dict[str, Any]] = []
    for surface in surfaces:
        if not isinstance(surface, dict):
            continue
        kind = surface.get("kind")
        if kind not in {
            "what_next_v1",
            "today_schedule_v1",
            "priority_list_v1",
            "triage_table_v1",
        }:
            continue
        if kind in {"what_next_v1", "today_schedule_v1", "priority_list_v1", "triage_table_v1"}:
            if not _contains_only_known_ids(
                surface,
                tasks=allowed_tasks,
                events=allowed_events,
                docs=allowed_docs,
                queue_items=allowed_queue_items,
            ):
                continue
        validated.append(surface)
        if len(validated) >= limit:
            break

    return validated


