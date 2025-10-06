from __future__ import annotations
from typing import Any, Dict, List


class CalendarService:
    def list_today(self) -> List[Dict[str, Any]]:
        return []

    def create_or_update(self, event: Dict[str, Any]) -> Dict[str, Any]:
        return {"id": "local-event", **event}

    def freebusy(self, when: Dict[str, Any]) -> Dict[str, Any]:
        return {"busy": []}
