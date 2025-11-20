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

