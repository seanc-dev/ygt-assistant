"""Utility modules for the calendar assistant."""

from .cli_output import (
    format_events,
    format_reminders,
    print_events_and_reminders,
    format_error_message,
    format_success_message,
    format_clarification_question,
)

# Import functions that don't cause circular imports
from .date_utils import parse_date_string

# Notion helper functions (optional - may not be available if env vars missing)
try:
    from .notion_helper import (
        update_item_status,
        get_items_by_status,
        find_item_by_name,
        query_database,
        update_page_status,
        update_page_property,
        get_page_content,
        get_database_id,
        create_task,
    )
    __all__ = [
        # CLI output functions
        "format_events",
        "format_reminders",
        "print_events_and_reminders",
        "format_error_message",
        "format_success_message",
        "format_clarification_question",
        # Command handling - imported separately to avoid circular imports
        # Date utilities
        "parse_date_string",
        # Notion helpers
        "update_item_status",
        "get_items_by_status",
        "find_item_by_name",
        "query_database",
        "update_page_status",
        "update_page_property",
        "get_page_content",
        "get_database_id",
        "create_task",
    ]
except Exception:
    # Notion helpers not available (missing env vars or dependencies)
    __all__ = [
        # CLI output functions
        "format_events",
        "format_reminders",
        "print_events_and_reminders",
        "format_error_message",
        "format_success_message",
        "format_clarification_question",
        # Command handling - imported separately to avoid circular imports
        # Date utilities
        "parse_date_string",
    ]
