"""Task and action linking repositories for LLM ops protocol."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

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


def _select_one(table: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Select a single row from a table."""
    qp = dict(params)
    qp["limit"] = "1"
    rows = _select(table, qp)
    if not rows:
        raise ValueError(f"{table} not found for filters {params}")
    return rows[0]


def _insert(table: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a row and return the created record."""
    with client() as c:
        resp = c.post(
            f"/{table}",
            json=payload,
            headers={"Prefer": "return=representation"},
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            if not data:
                raise RuntimeError(f"Insert to {table} returned empty response")
            return data[0]
        return data


def _patch(
    table: str, filters: Dict[str, str], payload: Dict[str, Any]
) -> Dict[str, Any]:
    """Update rows matching filters."""
    with client() as c:
        resp = c.patch(
            f"/{table}",
            params=filters,
            json=payload,
            headers={"Prefer": "return=representation"},
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            raise ValueError(f"{table} not found for filters {filters}")
        return data[0] if isinstance(data, list) else data


def get_action_item(user_id: str, action_id: str) -> Dict[str, Any]:
    """Load a single action item for the caller's tenant."""
    tenant_id, _ = _resolve_identity(user_id)
    return _select_one(
        "action_items",
        {"tenant_id": f"eq.{tenant_id}", "id": f"eq.{action_id}"}
    )


def update_action_task_link(
    user_id: str, action_id: str, task_id: Optional[str]
) -> Dict[str, Any]:
    """Update action_items.task_id (primary link)."""
    tenant_id, _ = _resolve_identity(user_id)
    payload = {"task_id": task_id}
    return _patch(
        "action_items",
        {"tenant_id": f"eq.{tenant_id}", "id": f"eq.{action_id}"},
        payload,
    )


def update_action_state(
    user_id: str,
    action_id: str,
    state: Optional[str] = None,
    defer_until: Optional[str] = None,
    added_to_today: Optional[bool] = None,
) -> Dict[str, Any]:
    """Update action state, defer_until, or added_to_today."""
    tenant_id, _ = _resolve_identity(user_id)
    payload: Dict[str, Any] = {}
    if state is not None:
        payload["state"] = state
    if defer_until is not None:
        payload["defer_until"] = defer_until
    if added_to_today is not None:
        payload["added_to_today"] = added_to_today
    return _patch(
        "action_items",
        {"tenant_id": f"eq.{tenant_id}", "id": f"eq.{action_id}"},
        payload,
    )


def create_task_source(
    user_id: str,
    task_id: str,
    source_type: str,
    source_id: Optional[str] = None,
    doc_id: Optional[str] = None,
    action_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a task_sources row linking a task to a source."""
    tenant_id, _ = _resolve_identity(user_id)
    payload = {
        "tenant_id": tenant_id,
        "task_id": task_id,
        "source_type": source_type,
        "source_id": source_id,
        "doc_id": doc_id,
        "action_id": action_id,
        "metadata": metadata or {},
    }
    return _insert("task_sources", payload)


def create_task_action_link(
    user_id: str,
    task_id: str,
    action_id: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a task_action_links row (many-to-many join)."""
    tenant_id, _ = _resolve_identity(user_id)
    payload = {
        "tenant_id": tenant_id,
        "task_id": task_id,
        "action_id": action_id,
        "metadata": metadata or {},
    }
    try:
        return _insert("task_action_links", payload)
    except Exception as e:
        # Handle unique constraint violation gracefully
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            # Link already exists, return existing
            return _select_one(
                "task_action_links",
                {
                    "tenant_id": f"eq.{tenant_id}",
                    "task_id": f"eq.{task_id}",
                    "action_id": f"eq.{action_id}",
                },
            )
        raise


def get_task_sources(user_id: str, task_id: str) -> List[Dict[str, Any]]:
    """Get all sources for a task."""
    tenant_id, _ = _resolve_identity(user_id)
    return _select(
        "task_sources",
        {
            "tenant_id": f"eq.{tenant_id}",
            "task_id": f"eq.{task_id}",
            "order": "created_at.asc",
        },
    )


def get_task_action_links(user_id: str, task_id: str) -> List[Dict[str, Any]]:
    """Get all action links for a task."""
    tenant_id, _ = _resolve_identity(user_id)
    return _select(
        "task_action_links",
        {
            "tenant_id": f"eq.{tenant_id}",
            "task_id": f"eq.{task_id}",
            "order": "created_at.asc",
        },
    )


def get_action_task_links(user_id: str, action_id: str) -> List[Dict[str, Any]]:
    """Get all tasks linked to an action."""
    tenant_id, _ = _resolve_identity(user_id)
    return _select(
        "task_action_links",
        {
            "tenant_id": f"eq.{tenant_id}",
            "action_id": f"eq.{action_id}",
            "order": "created_at.asc",
        },
    )

