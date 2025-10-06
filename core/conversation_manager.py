"""Conversation memory and session state management."""

from collections import deque
from datetime import datetime
from typing import List, Optional, Dict, Any
from .types import Turn


class ConversationState:
    """Manages ephemeral conversation context for the current session."""

    def __init__(self, max_context_size: int = 10):
        """
        Initialize conversation state.

        Args:
            max_context_size: Maximum number of turns to keep in context
        """
        self.max_context_size = max_context_size
        self.turns = deque(maxlen=max_context_size)
        self.turn_count = 0

    def append_turn(
        self,
        user_input: str,
        assistant_action: str,
        assistant_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a new turn to the conversation context.

        Args:
            user_input: The user's input text
            assistant_action: The action the assistant took
            assistant_details: Optional details about the assistant's action
        """
        turn = Turn(
            user_input=user_input,
            assistant_action=assistant_action,
            assistant_details=assistant_details or {},
        )
        self.turns.append(turn)
        self.turn_count += 1

    def get_context_window(self, limit: Optional[int] = None) -> List[Turn]:
        """
        Get the recent conversation context.

        Args:
            limit: Maximum number of turns to return (None for all available)

        Returns:
            List of recent turns
        """
        if limit is None:
            return list(self.turns)

        # Handle edge cases
        if limit <= 0:
            return []

        # Return the most recent turns up to the limit
        return list(self.turns)[-limit:]

    def resolve_reference(self, pronoun: str) -> Optional[str]:
        """
        Resolve a pronoun reference to the most recent relevant context.

        Args:
            pronoun: The pronoun to resolve ("it", "that", "this", etc.)

        Returns:
            The resolved reference text, or None if not found
        """
        if not self.turns:
            return None

        # Look for the most recent event that could be referenced
        # We need to find the most recent create_event action
        # Convert to list and reverse to get most recent first
        turns_list = list(self.turns)
        for turn in reversed(turns_list):
            if turn.assistant_action == "create_event":
                # Return a summary of the event
                details = turn.assistant_details
                if details:
                    title = details.get("title", "meeting")
                    date = details.get("date", "")
                    time = details.get("time", "")
                    result = f"{title} on {date} at {time}".strip()
                    # Clean up empty parts
                    result = result.replace(" on  at ", " ")
                    result = result.replace(" on ", " ")
                    result = result.replace(" at ", " ")
                    return result
                else:
                    # Return the user input for the create_event
                    return turn.user_input

        return None

    def clear_context(self) -> None:
        """Clear all conversation context."""
        self.turns.clear()
        self.turn_count = 0

    def get_recent_actions(self, limit: int = 5) -> List[str]:
        """
        Get the most recent assistant actions.

        Args:
            limit: Maximum number of actions to return

        Returns:
            List of recent action names
        """
        actions = [turn.assistant_action for turn in self.turns]
        return actions[-limit:] if limit > 0 else []

    def get_context_for_llm_prompt(self, limit: int = 5) -> str:
        """
        Format conversation context for inclusion in LLM prompts.

        Args:
            limit: Maximum number of turns to include

        Returns:
            Formatted context string
        """
        recent_turns = self.get_context_window(limit)

        if not recent_turns:
            return ""

        context_lines = []
        for turn in recent_turns:
            context_lines.append(f"User: {turn.user_input}")
            context_lines.append(f"Assistant: {turn.assistant_action}")
            if turn.assistant_details:
                context_lines.append(f"Details: {turn.assistant_details}")

        return "\n".join(context_lines)

    def get_turn_count(self) -> int:
        """Get the total number of turns in this session."""
        return self.turn_count

    def is_empty(self) -> bool:
        """Check if the conversation context is empty."""
        return len(self.turns) == 0
