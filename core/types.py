"""Shared data types for conversations and memory."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class Turn:
    """Represents a single turn in a conversation."""

    user_input: str
    assistant_action: str
    assistant_details: Dict[str, Any] = None
    timestamp: datetime = None

    def __post_init__(self):
        """Set default values after initialization."""
        if self.assistant_details is None:
            self.assistant_details = {}
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class MemoryItem:
    """Represents a memory item for long-term storage."""

    type: str  # "past_event", "intention", "commitment", "preference"
    content: str
    metadata: Dict[str, Any] = None
    embedding: Optional[list] = None
    timestamp: datetime = None

    def __post_init__(self):
        """Set default values after initialization."""
        if self.metadata is None:
            self.metadata = {}
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ConversationContext:
    """Represents the current conversation context for LLM prompts."""

    recent_turns: list[Turn]
    current_time: datetime
    user_preferences: Dict[str, Any] = None

    def __post_init__(self):
        """Set default values after initialization."""
        if self.user_preferences is None:
            self.user_preferences = {}
