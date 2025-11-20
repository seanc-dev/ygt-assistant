from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query, Request
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
from presentation.api.deps.providers import get_email_provider_for
from settings import FEATURE_GRAPH_LIVE, FEATURE_LIVE_LIST_INBOX

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
async def actions_scan(body: Dict[str, Any], request: Request) -> List[Dict[str, Any]]:
    try:
        store = get_store()
        core_ctx = {
            "episodic": [m.__dict__ for m in store.list_by_level("episodic")][:5],
            "semantic": [m.__dict__ for m in store.list_by_level("semantic")][:5],
            "procedural": [m.__dict__ for m in store.list_by_level("procedural")][:5],
            "narrative": [m.__dict__ for m in store.list_by_level("narrative")][:5],
        }
        context = {"domains": body.get("domains") or []}
        # If live inbox is enabled, pull a small slice and feed into the LLM proposer
        try:
            if FEATURE_GRAPH_LIVE and FEATURE_LIVE_LIST_INBOX:
                uid = request.cookies.get("ygt_user") or "default"
                p = get_email_provider_for("list_inbox", uid)
                if hasattr(p, "list_inbox_async"):
                    context["inbox"] = await p.list_inbox_async(5)  # type: ignore[attr-defined]
                elif hasattr(p, "list_inbox"):
                    context["inbox"] = p.list_inbox(5)
        except Exception:
            # Non-fatal; fall back to pure LLM proposals
            pass
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
        return [
            {
                "id": "err",
                "kind": "error",
                "title": type(e).__name__,
                "summary": str(e),
                "status": "error",
            }
        ]


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
    return history_log.list(max(0, min(limit, 1000)))


# Actions v2 (mock-only; deterministic)
@router.post("/actions/plan-today-v2")
async def plan_today_v2(body: Dict[str, Any]) -> Dict[str, Any]:
    # Deterministic plan with buffers and focus blocks
    plan = [
        {"time": "09:00", "title": "Standup", "kind": "meeting"},
        {"time": "09:15", "title": "Buffer", "kind": "buffer"},
        {"time": "10:00", "title": "Client prep notes", "kind": "prep"},
        {"time": "11:00", "title": "Focus block (energy: high)", "kind": "focus"},
        {"time": "12:30", "title": "Buffer", "kind": "buffer"},
    ]
    history_log.append(
        {
            "ts": "now",
            "verb": "plan",
            "object": "day",
            "rationale": "Added travel buffers and energy-based focus.",
            "plan": plan,
        }
    )
    return {"plan": plan}


@router.post("/actions/triage-v2")
async def triage_v2(body: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = [
        {
            "id": "t1",
            "title": "Invoice due",
            "priority": "high",
            "sla": "<24h",
            "rationale": "Finance-critical",
        },
        {
            "id": "t2",
            "title": "Schedule meeting",
            "priority": "medium",
            "sla": "<72h",
            "rationale": "Client scheduling",
        },
        {
            "id": "t3",
            "title": "Thanks",
            "priority": "low",
            "sla": "<72h",
            "rationale": "No action required",
        },
    ]
    for it in items:
        approvals_store[it["id"]] = {**it, "status": "proposed", "kind": "email"}
    history_log.append(
        {
            "ts": "now",
            "verb": "scan",
            "object": "inbox",
            "rationale": "Batch approvals with priorities and SLAs.",
        }
    )
    return items


@router.post("/actions/draft-v2")
async def draft_v2(body: Dict[str, Any]) -> Dict[str, Any]:
    tone = (body.get("tone") or "calm").lower()
    schedule_send = body.get("schedule_send") or "tomorrow 09:00"
    follow_up_note = body.get("follow_up_note") or "Add to follow-up list"
    draft = {
        "id": "draft-v2-1",
        "to": body.get("to") or ["user@example.com"],
        "subject": body.get("subject") or "Quick, calm update",
        "body": f"Hi there, just a {tone} follow-up.",
        "tone": tone,
        "schedule_send": schedule_send,
        "follow_up_note": follow_up_note,
        "status": "proposed",
    }
    history_log.append(
        {
            "ts": "now",
            "verb": "draft",
            "object": "email",
            "id": draft["id"],
            "rationale": f"Tone preset {tone}",
        }
    )
    return draft


@router.post("/actions/reschedule-v2")
async def reschedule_v2(body: Dict[str, Any]) -> Dict[str, Any]:
    options = [
        {
            "rank": 1,
            "start": "2025-10-24T10:00:00Z",
            "end": "2025-10-24T10:30:00Z",
            "rationale": "No conflicts; within working hours",
        },
        {
            "rank": 2,
            "start": "2025-10-24T15:00:00Z",
            "end": "2025-10-24T15:30:00Z",
            "rationale": "Minor conflict; resolvable",
        },
        {
            "rank": 3,
            "start": "2025-10-25T09:00:00Z",
            "end": "2025-10-25T09:30:00Z",
            "rationale": "Alternative next day",
        },
    ]
    history_log.append(
        {
            "ts": "now",
            "verb": "reschedule",
            "object": "event",
            "rationale": "Ranked options with rationale",
        }
    )
    return {"options": options}


@router.post("/actions/reconnect-v2")
async def reconnect_v2(body: Dict[str, Any]) -> Dict[str, Any]:
    # Provide retry window suggestions and CTA when tokens are absent/expired (mocked)
    return {
        "retry": ["now", "in 15 minutes", "this afternoon"],
        "cta": "Reconnect Microsoft",
        "degraded": True,
        "message": "Connection inactive. Showing mock suggestions until reconnected.",
    }
