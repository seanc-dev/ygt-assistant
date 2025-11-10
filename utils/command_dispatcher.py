"""Command dispatcher for main loop actions.

Legacy CLI handlers have been removed. This module now provides a minimal stub
for API compatibility.
"""

from typing import Callable

# Empty HANDLERS dict for backward compatibility with existing imports
# Legacy handlers are no longer supported - use modern API endpoints instead
HANDLERS: dict[str, Callable] = {}


def dispatch(action: str, details: dict):
    """Dispatch the given action to the appropriate handler.
    
    Legacy CLI handlers have been removed. This function now raises
    NotImplementedError for all actions as they are no longer supported.
    
    For calendar actions, use the modern calendar endpoints in presentation/api/routes/calendar.py
    instead.
    """
    raise NotImplementedError(
        f"Legacy calendar action '{action}' is no longer supported. "
        "Please use the modern calendar API endpoints instead."
    )
