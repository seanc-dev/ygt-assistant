"""Queue (action_items) repository for LLM ops protocol."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

from archive.infra.supabase.client import client
from settings import TENANT_DEFAULT

logger = logging.getLogger(__name__)


def _resolve_identity(user_id: Optional[str]) -> Tuple[str, str]:
    """Map incoming user identifier to a Supabase user + tenant."""
    # Import helpers from workroom module
    import presentation.api.repos.workroom as workroom_module
    _fetch_user = workroom_module._fetch_user
    _looks_like_uuid = workroom_module._looks_like_uuid
    
    row: Optional[Dict[str, Any]] = None
    if user_id:
        if _looks_like_uuid(user_id):
            row = _fetch_user({"id": f"eq.{user_id}"})
        elif "@" in user_id:
            row = _fetch_user({"email": f"eq.{user_id}"})
    if not row:
        row = _fetch_user({})
    if not row:
        raise RuntimeError("No workroom users provisioned in Supabase.")
    tenant_id = row.get("tenant_id") or TENANT_DEFAULT
    return tenant_id, row["id"]


def _select(
    table: str, params: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Select rows from a table."""
    qp = dict(params or {})
    qp.setdefault("select", "*")
    with client() as c:
        resp = c.get(f"/{table}", params=qp)
        resp.raise_for_status()
        return resp.json()


def get_queue_items(
    user_id: str,
    limit: int = 20,
    state: Optional[str] = None,
    priority: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get action items for the user's queue.
    
    Args:
        user_id: User identifier
        limit: Maximum number of items to return
        state: Optional filter by state (e.g., 'queued', 'deferred')
        priority: Optional filter by priority
    """
    tenant_id, resolved_user_id = _resolve_identity(user_id)
    params: Dict[str, Any] = {
        "tenant_id": f"eq.{tenant_id}",
        "owner_id": f"eq.{resolved_user_id}",
        "order": "priority.asc,created_at.desc",
        "limit": str(limit),
    }
    if state:
        params["state"] = f"eq.{state}"
    if priority:
        params["priority"] = f"eq.{priority}"
    return _select("action_items", params)


def get_action_item(user_id: str, action_id: str) -> Dict[str, Any]:
    """Get a single action item."""
    tenant_id, _ = _resolve_identity(user_id)
    rows = _select(
        "action_items",
        {
            "tenant_id": f"eq.{tenant_id}",
            "id": f"eq.{action_id}",
            "limit": "1",
        },
    )
    if not rows:
        raise ValueError(f"Action item {action_id} not found")
    return rows[0]

