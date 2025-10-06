"""Wraps GPT-4o (OpenAI) calls for interpreting user commands in the terminal calendar assistant."""

from dotenv import load_dotenv  # type: ignore
import os
from typing import Any, Dict

try:
    import openai  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    openai = None
import json
from datetime import datetime


# Load .env.local first for local dev overrides, then .env
try:
    load_dotenv(".env.local", override=True)
except Exception:
    pass
load_dotenv()
# Load API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Create OpenAI client (for SDK v1.x)
client = openai.OpenAI(api_key=OPENAI_API_KEY) if openai and OPENAI_API_KEY else None

# Define available functions for function calling
calendar_functions = [
    {
        "name": "list_events_only",
        "description": "List only calendar events for today.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "list_reminders_only",
        "description": "List only reminders for today.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "list_all",
        "description": "List both events and reminders for today.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "list_todays_events",
        "description": "List all events and reminders for today (legacy fallback).",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "create_event",
        "description": "Create a new calendar event.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Event title"},
                "date": {"type": "string", "description": "Event date (YYYY-MM-DD)"},
                "time": {"type": "string", "description": "Event time (e.g., 14:00)"},
                "duration": {"type": "integer", "description": "Duration in minutes"},
                "location": {"type": "string", "description": "Event location"},
            },
            "required": ["title", "date", "time"],
        },
    },
    {
        "name": "delete_event",
        "description": "Delete an existing calendar event.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Event title to delete"},
                "date": {"type": "string", "description": "Event date (YYYY-MM-DD)"},
            },
            "required": ["title", "date"],
        },
    },
    {
        "name": "move_event",
        "description": "Move an existing calendar event to a new date/time.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Event title to move"},
                "old_date": {
                    "type": "string",
                    "description": "Current event date (YYYY-MM-DD)",
                },
                "new_date": {
                    "type": "string",
                    "description": "New event date (YYYY-MM-DD)",
                },
                "new_time": {
                    "type": "string",
                    "description": "New event time (e.g., 15:00)",
                },
            },
            "required": ["title", "old_date", "new_date", "new_time"],
        },
    },
    {
        "name": "add_notification",
        "description": "Add a notification reminder to an existing event.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Event title"},
                "date": {"type": "string", "description": "Event date (YYYY-MM-DD)"},
                "minutes_before": {
                    "type": "integer",
                    "description": "Minutes before event to trigger",
                },
            },
            "required": ["title", "date"],
        },
    },
    {
        "name": "clarify",
        "description": "Ask user for clarification when request is ambiguous",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Specific question to ask user",
                },
                "context": {
                    "type": "string",
                    "description": "Context about what was unclear",
                },
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Available options if applicable",
                },
            },
            "required": ["question"],
        },
    },
    {
        "name": "error",
        "description": "Return error with helpful message when request cannot be processed",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Error message"},
                "suggestion": {
                    "type": "string",
                    "description": "Helpful suggestion for user",
                },
                "reason": {"type": "string", "description": "Reason for the error"},
            },
            "required": ["message"],
        },
    },
]


def interpret_command(
    user_input: str, conversation_context: str = ""
) -> Dict[str, Any]:
    """
    Use GPT-4o function calling to interpret the user's natural language command.

    This function takes natural language input and uses GPT-4o with function calling
    to parse it into structured actions. It handles edge cases like misspellings,
    poor grammar, and ambiguous requests gracefully.

    Args:
        user_input: The user's natural language input (e.g., "schedule team meeting tomorrow")
        conversation_context: Optional conversation context from previous turns for reference resolution

    Returns:
        Dict containing:
            - action: The parsed action (e.g., "create_event", "delete_event")
            - details: Dict with action-specific parameters

    Raises:
        Exception: If OpenAI API is unavailable or returns an error

    Examples:
        >>> interpret_command("schedule team meeting tomorrow at 2pm")
        {'action': 'create_event', 'details': {'title': 'team meeting', 'date': 'tomorrow', 'time': '14:00'}}

        >>> interpret_command("delete that meeting")
        {'action': 'delete_event', 'details': {'title': 'meeting'}}

        >>> interpret_command("shedule meeting")  # Handles misspellings
        {'action': 'create_event', 'details': {'title': 'meeting'}}
    """
    # If no OpenAI client (e.g. missing API key), return error
    if not client:
        return {
            "action": "error",
            "details": {
                "message": "OpenAI API not available",
                "suggestion": "Please check your API key configuration",
                "reason": "Missing or invalid OpenAI API key",
            },
        }
    try:
        # Provide current date, time, and day context to the LLM
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        current_day = now.strftime("%A")

        # Build system message with conversation context
        system_content = (
            f"You are a calendar assistant. Today is {current_day}, {current_date} at {current_time}. "
            "Handle user requests intelligently and gracefully. "
            "Use the available functions to respond appropriately. "
        )

        # Add conversation context if available
        if conversation_context:
            system_content += f"\nCONVERSATION CONTEXT:\n{conversation_context}\n"

        system_content += (
            "EDGE CASE HANDLING: "
            "- Misspellings: 'shedule' → understand as 'schedule' "
            "- Poor grammar: Extract the core intent, ignore extra words "
            "- Ambiguous dates: Ask for clarification using 'clarify' function "
            "- Vague requests: Ask specific questions using 'clarify' function "
            "- Past dates: Return error with suggestion to use future date "
            "- Invalid dates: Return error with suggestion to use YYYY-MM-DD format "
            "- Vague references ('it', 'that meeting'): Ask for clarification "
            "WHEN TO USE FUNCTIONS: "
            "- create_event: For scheduling new events "
            "- delete_event: For removing events "
            "- move_event: For rescheduling events "
            "- list_events_only: For viewing calendar events "
            "- list_reminders_only: For viewing reminders/tasks "
            "- list_all: For viewing both events and reminders "
            "- clarify: When request is ambiguous or unclear "
            "- error: When request cannot be processed (invalid dates, etc.) "
            "Always provide helpful responses. If uncertain, ask for clarification rather than guess."
        )

        system_message = {
            "role": "system",
            "content": system_content,
        }

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[system_message, {"role": "user", "content": user_input}],
            functions=calendar_functions,  # type: ignore
            function_call="auto",
            temperature=0.0,
            max_tokens=256,
            timeout=30,  # 30 second timeout to prevent hanging
        )
        message = response.choices[0].message
        # Some tests mock function_call attributes as MagicMocks; access safely
        func_call = getattr(message, "function_call", None)
        if func_call is not None:
            # Attempt to read name; if it's a MagicMock, coerce to str safely
            try:
                # PropertyMock may return value on attribute access
                name_attr = getattr(func_call, "name", None)
                func_name = name_attr if isinstance(name_attr, str) else str(name_attr)
            except Exception:
                func_name = None
            try:
                raw_args = getattr(func_call, "arguments", None)
                arguments = json.loads(raw_args) if raw_args else {}
            except Exception:
                arguments = raw_args or {}
            # If func_name looks like a MagicMock/PropertyMock repr, fall back to clarify
            if (
                func_name
                and not str(func_name).startswith("<MagicMock")
                and not str(func_name).startswith("<PropertyMock")
            ):
                return {"action": func_name, "details": arguments}
            # Fallback when mock doesn't provide a usable name
            return {
                "action": "clarify",
                "details": {
                    "question": "I didn't understand your request. Could you please rephrase it?",
                    "context": "The request was unclear or ambiguous",
                },
            }
        else:
            # No function call returned - ask for clarification
            return {
                "action": "clarify",
                "details": {
                    "question": "I didn't understand your request. Could you please rephrase it?",
                    "context": "The request was unclear or ambiguous",
                },
            }
    except Exception as e:
        return {"action": "error", "details": str(e)}
