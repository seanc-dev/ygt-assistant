from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
from core.store import get_store


def _audit_repo():
    try:
        from infra.repos.factory import audit_repo  # type: ignore

        return audit_repo()
    except Exception:

        class _Stub:
            def write(self, entry):
                return entry.get("request_id", "")

        return _Stub()


from settings import TENANT_DEFAULT
from presentation.api.state import approvals_store, history_log
from services import llm as llm_service

router = APIRouter()


@router.get("/approvals")
async def approvals_list(
    filter: Optional[str] = Query(default="all"),
) -> List[Dict[str, Any]]:
    items = list(approvals_store.values())
    if filter in {"email", "calendar"}:
        items = [a for a in items if a.get("kind") == filter]
    try:
        items.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    except Exception:
        pass
    return items


@router.post("/actions/scan")
async def actions_scan(body: Dict[str, Any]) -> List[Dict[str, Any]]:
    try:
        store = get_store()
        core_ctx = {
            "episodic": [m.__dict__ for m in store.list_by_level("episodic")][:5],
            "semantic": [m.__dict__ for m in store.list_by_level("semantic")][:5],
            "procedural": [m.__dict__ for m in store.list_by_level("procedural")][:5],
            "narrative": [m.__dict__ for m in store.list_by_level("narrative")][:5],
        }
        context = {"domains": body.get("domains") or []}
        approvals = llm_service.summarise_and_propose(context, core_ctx)
        for a in approvals:
            a.setdefault("status", "proposed")
            approvals_store[a["id"]] = a
        rid = "scan"
        _audit_repo().write(
            {
                "request_id": rid,
                "tenant_id": TENANT_DEFAULT,
                "dry_run": True,
                "actions": approvals,
                "results": {"source": "actions_scan"},
            }
        )
        return approvals
    except Exception as e:
        # Return an empty list in dev to avoid UI hangs; attach error via header is not possible here
        return [{"id": "err", "kind": "error", "title": type(e).__name__, "summary": str(e), "status": "error"}]


@router.post("/actions/approve/{approval_id}")
async def actions_approve(approval_id: str) -> Dict[str, Any]:
    a = approvals_store.get(approval_id)
    if not a:
        return {"error": "not_found"}
    a["status"] = "approved"
    history_log.append(
        {"ts": "now", "verb": "approve", "object": "approval", "id": approval_id}
    )
    return a


@router.post("/actions/edit/{approval_id}")
async def actions_edit(approval_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    a = approvals_store.get(approval_id)
    if not a:
        return {"error": "not_found"}
    a["status"] = "edited"
    a["edit_instructions"] = body.get("instructions")
    history_log.append(
        {
            "ts": "now",
            "verb": "edit",
            "object": "approval",
            "id": approval_id,
            "instructions": body.get("instructions"),
        }
    )
    return a


@router.post("/actions/skip/{approval_id}")
async def actions_skip(approval_id: str) -> Dict[str, Any]:
    a = approvals_store.get(approval_id)
    if not a:
        return {"error": "not_found"}
    a["status"] = "skipped"
    history_log.append(
        {"ts": "now", "verb": "skip", "object": "approval", "id": approval_id}
    )
    return a


@router.post("/actions/undo/{approval_id}")
async def actions_undo(approval_id: str) -> Dict[str, Any]:
    a = approvals_store.get(approval_id)
    if not a:
        return {"error": "not_found"}
    a["status"] = "proposed"
    history_log.append(
        {"ts": "now", "verb": "undo", "object": "approval", "id": approval_id}
    )
    return a


@router.get("/history")
async def history(limit: int = 100) -> List[Dict[str, Any]]:
    return list(reversed(history_log))[: max(0, min(limit, 1000))]
