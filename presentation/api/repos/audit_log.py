"""Audit logging repository."""
from __future__ import annotations
from typing import Any, Dict, List
from datetime import datetime
import uuid

# In-memory audit log (will be replaced with DB)
_audit_log: List[Dict[str, Any]] = []


def write_audit(action: str, details: Dict[str, Any], request_id: str | None = None) -> str:
    """Write audit entry.
    
    Args:
        action: Action type (e.g., "defer", "add_to_today", "schedule_alternatives")
        details: Action-specific details
        request_id: Request ID from middleware (defaults to generating new UUID)
    
    Returns:
        Audit entry ID
    """
    entry_id = str(uuid.uuid4())
    entry = {
        "id": entry_id,
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id or str(uuid.uuid4()),
        "action": action,
        "details": details,
    }
    _audit_log.append(entry)
    return entry_id


def get_audit_log(limit: int = 100) -> List[Dict[str, Any]]:
    """Get recent audit log entries."""
    return _audit_log[-limit:][::-1]  # Return newest first

