from __future__ import annotations
from typing import Any, Dict, List

# In-memory stores for POC
approvals_store: Dict[str, Dict[str, Any]] = {}
drafts_store: Dict[str, Dict[str, Any]] = {}
history_log: List[Dict[str, Any]] = []
created_events_store: Dict[str, Dict[str, Any]] = {}

