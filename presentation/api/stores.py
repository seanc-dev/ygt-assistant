"""Shared in-memory stores for LucidWork."""
from __future__ import annotations
from typing import Any, Dict, List

# Store for proposed blocks (from "Add to Today" actions)
# This will be moved to DB in Phase 3+
proposed_blocks_store: List[Dict[str, Any]] = []

