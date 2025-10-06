from typing import Dict, Any, List, Optional

from adapters.notion_adapter import NotionTasksAdapter, NotionCRMAdapter
from infra.repos import factory
from settings import DRY_RUN_DEFAULT, TENANT_DEFAULT

_tasks = NotionTasksAdapter()
_crm = NotionCRMAdapter()
_idem = factory.idempotency_repo()
_audit = factory.audit_repo()


def _external_id(payload: Dict[str, Any]) -> str:
    """Derive an external id for idempotency from payload.

    Prefers email message id via payload['source_ids']['email_message_id'] or an explicit 'external_id'.
    """

    src = payload.get("source_ids") or {}
    return payload.get("external_id") or src.get("email_message_id") or "none"


def execute_actions(
    actions: List[Dict[str, Any]],
    *,
    dry_run: Optional[bool] = None,
    tenant_id: str = TENANT_DEFAULT
) -> Dict[str, Any]:
    """Execute or plan a list of ProposedAction dicts.

    Returns a dict with request_id, dry_run flag, and per-action results.
    """

    dr = DRY_RUN_DEFAULT if dry_run is None else dry_run
    # Resolve repos at call time to respect test-time env (memory vs db)
    idem_repo = factory.idempotency_repo()
    audit_repo = factory.audit_repo()
    results: List[Dict[str, Any]] = []
    for a in actions:
        a_type = a.get("type")
        payload = a.get("payload", {})
        ext = _external_id(payload)
        key_kind = a_type or "unknown"
        if ext != "none" and idem_repo.seen(tenant_id, key_kind, ext):
            results.append(
                {"action": a_type, "status": "skipped_duplicate", "external_id": ext}
            )
            continue

        if a_type == "create_task":
            payload["tenant_id"] = tenant_id
            res = _tasks.create_task(payload, dry_run=dr)
        elif a_type == "upsert_contact":
            payload["tenant_id"] = tenant_id
            res = _crm.upsert_contact(payload, dry_run=dr)
        else:
            res = {"unsupported": True, "action": a_type}

        if ext != "none":
            idem_repo.record(tenant_id, key_kind, ext)

        results.append({"action": a_type, "result": res})

    rid = audit_repo.write(
        {
            "request_id": None,
            "tenant_id": tenant_id,
            "dry_run": dr,
            "actions": actions,
            "results": results,
        }
    )
    return {"request_id": rid, "dry_run": dr, "results": results}
