from typing import Any, Dict, List

from calendar_agent_eventkit import EventKitAgent
from core.ports.calendar import CalendarPort


class EventKitCalendarAdapter(CalendarPort):
    """Adapter that exposes the EventKitAgent via the CalendarPort interface."""

    def __init__(self) -> None:
        self.agent = EventKitAgent()

    def create_event(self, details: Dict[str, Any]) -> Dict[str, Any]:
        return self.agent.create_event(details)

    def move_event(self, details: Dict[str, Any]) -> Dict[str, Any]:
        return self.agent.move_event(details)

    def delete_event(self, details: Dict[str, Any]) -> Dict[str, Any]:
        return self.agent.delete_event(details)

    def find_events(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        # EventKitAgent currently lists events via list_events_and_reminders; a more
        # detailed adapter can be added later. For now, return an empty list to
        # keep behavior unchanged until ports are wired in.
        _ = query
        return []


