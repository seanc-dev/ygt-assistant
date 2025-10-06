"""Core memory and conversation systems for the calendar assistant."""

from .conversation_manager import ConversationState
from .memory_manager import CoreMemory, MemoryType
from .embedding_manager import EmbeddingManager
from .narrative_memory import NarrativeMemory
from .nudge_engine import ContextualNudger
from .types import Turn, MemoryItem

__all__ = [
    # Conversation management
    "ConversationState",
    # Memory systems
    "CoreMemory",
    "MemoryType",
    "EmbeddingManager",
    "NarrativeMemory",
    # Proactive features
    "ContextualNudger",
    # Data types
    "Turn",
    "MemoryItem",
]
