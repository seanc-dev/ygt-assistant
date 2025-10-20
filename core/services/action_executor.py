from typing import Dict, Any, List, Optional

# Optional Notion adapters; provide stubs if not present (post-trim POC)
try:  # pragma: no cover - import guard
    from adapters.notion_adapter import NotionTasksAdapter, NotionCRMAdapter  # type: ignore
except Exception:  # pragma: no cover
    class NotionTasksAdapter:  # type: ignore
        def create_task(self, payload: Dict[str, Any], *, dry_run: bool = True) -> Dict[str, Any]:
            return {"ok": True, "dry_run": dry_run, "task": {"title": payload.get("title")}}

    class NotionCRMAdapter:  # type: ignore
        def upsert_contact(self, payload: Dict[str, Any], *, dry_run: bool = True) -> Dict[str, Any]:
            return {"ok": True, "dry_run": dry_run, "contact": {"email": payload.get("email")}}

# Optional repos; provide in-memory stubs when infra is absent
try:  # pragma: no cover - import guard
    from infra.repos import factory as _factory  # type: ignore
except Exception:  # pragma: no cover
    class _IdemRepo:
        _seen: Dict[str, Dict[str, Dict[str, bool]]] = {}

        def seen(self, tenant_id: str, kind: str, ext: str) -> bool:
            return bool(self._seen.get(tenant_id, {}).get(kind, {}).get(ext))

        def record(self, tenant_id: str, kind: str, ext: str) -> None:
            self._seen.setdefault(tenant_id, {}).setdefault(kind, {})[ext] = True

    class _AuditRepo:
        def write(self, entry: Dict[str, Any]) -> str:
            return entry.get("request_id") or "req_local"

    class _factory:  # type: ignore
        @staticmethod
        def idempotency_repo() -> _IdemRepo:
            return _IdemRepo()

        @staticmethod
        def audit_repo() -> _AuditRepo:
            return _AuditRepo()

from settings import DRY_RUN_DEFAULT, TENANT_DEFAULT

_tasks = NotionTasksAdapter()
_crm = NotionCRMAdapter()
_idem = _factory.idempotency_repo()
_audit = _factory.audit_repo()


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
