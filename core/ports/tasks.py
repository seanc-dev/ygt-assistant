from typing import Protocol, Dict, Any


class TasksPort(Protocol):
    """Port interface for task management providers."""

    def create_task(self, details: Dict[str, Any], *, dry_run: bool = True) -> Dict[str, Any]:
        """Create a task with the given details."""

        ...


