from typing import Any, Dict, List, Protocol


class CalendarPort(Protocol):
    """Port interface for calendar operations.

    Implementations should adapt provider-specific behavior to this interface
    to enable decoupled domain logic and testability.
    """

    def create_event(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Create an event given provider-specific details."""

        ...

    def move_event(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Move/reschedule an existing event."""

        ...

    def delete_event(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Delete an event by identifier or matching details."""

        ...

    def find_events(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find events matching a query expression."""

        ...


