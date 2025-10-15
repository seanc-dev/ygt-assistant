from typing import Dict, Any
import uuid
import time
from infra.repos.interfaces import AuditRepo

_log: Dict[str, Dict[str, Any]] = {}


class MemoryAuditRepo(AuditRepo):
    def write(self, entry: Dict[str, Any]) -> str:
        rid = entry.get("request_id") or str(uuid.uuid4())
        entry = dict(entry)
        entry["request_id"] = rid
        entry["ts"] = time.time()
        _log[rid] = entry
        return rid

    def get(self, request_id: str) -> Dict[str, Any]:
        return _log.get(request_id, {})


