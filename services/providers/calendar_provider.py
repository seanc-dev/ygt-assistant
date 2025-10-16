from __future__ import annotations
from typing import Any, Dict, List


class CalendarProvider:
    """Abstract calendar provider interface.

    Implementations must avoid logging sensitive event details or tokens.
    """

    def list_events(self, time_min: str, time_max: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def freebusy(self, time_min: str, time_max: str) -> Dict[str, Any]:
        raise NotImplementedError

    def create_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def update_event(self, event_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def delete_event(self, event_id: str) -> Dict[str, Any]:
        raise NotImplementedError
