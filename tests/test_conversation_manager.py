"""Tests for conversation memory and session state management."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from core.conversation_manager import ConversationState, Turn


class TestConversationState:
    """Test the ConversationState class for session memory management."""

    def test_conversation_state_initialization(self):
        """Test ConversationState initializes with empty context."""
        state = ConversationState()
        assert state.get_context_window() == []
        assert state.turn_count == 0

    def test_append_turn_basic(self):
        """Test basic turn appending functionality."""
        state = ConversationState()

        # Add a turn
        state.append_turn("schedule meeting tomorrow", "create_event")

        context = state.get_context_window()
        assert len(context) == 1
        assert context[0].user_input == "schedule meeting tomorrow"
        assert context[0].assistant_action == "create_event"
        assert state.turn_count == 1

    def test_context_window_limits(self):
        """Test that context window respects maximum size."""
        state = ConversationState(max_context_size=3)

        # Add more turns than the limit
        state.append_turn("first turn", "action1")
        state.append_turn("second turn", "action2")
        state.append_turn("third turn", "action3")
        state.append_turn("fourth turn", "action4")

        context = state.get_context_window()
        assert len(context) == 3  # Should only keep last 3
        assert context[0].user_input == "second turn"  # Oldest should be dropped
        assert context[2].user_input == "fourth turn"  # Newest should be last

    def test_get_context_window_with_limit(self):
        """Test getting context window with custom limit."""
        state = ConversationState()

        # Add 5 turns
        for i in range(5):
            state.append_turn(f"turn {i}", f"action {i}")

        # Get last 3 turns
        context = state.get_context_window(3)
        assert len(context) == 3
        assert context[0].user_input == "turn 2"
        assert context[2].user_input == "turn 4"

    def test_resolve_reference_basic(self):
        """Test basic reference resolution."""
        state = ConversationState()

        # Add some context
        state.append_turn("schedule team meeting tomorrow", "create_event")
        state.append_turn("move it to Friday", "move_event")

        # Resolve "it" - should refer to the team meeting
        reference = state.resolve_reference("it")
        assert reference is not None
        assert "team meeting" in reference.lower()

    def test_resolve_reference_not_found(self):
        """Test reference resolution when reference not found."""
        state = ConversationState()

        # Try to resolve "it" with no context
        reference = state.resolve_reference("it")
        assert reference is None

    def test_resolve_reference_ambiguous(self):
        """Test reference resolution with ambiguous context."""
        state = ConversationState()

        # Add multiple events
        state.append_turn("schedule team meeting tomorrow", "create_event")
        state.append_turn("schedule project review on Friday", "create_event")
        state.append_turn("move it to Monday", "move_event")

        # "it" could refer to either meeting
        reference = state.resolve_reference("it")
        # Should return the most recent event (project review)
        assert "project review" in reference.lower()

    def test_resolve_reference_with_pronouns(self):
        """Test resolution of various pronouns."""
        state = ConversationState()

        state.append_turn("schedule meeting with John", "create_event")
        state.append_turn("delete that meeting", "delete_event")

        # Test different pronouns
        assert state.resolve_reference("that") is not None
        assert state.resolve_reference("it") is not None
        assert state.resolve_reference("this") is not None

    def test_clear_context(self):
        """Test clearing the conversation context."""
        state = ConversationState()

        # Add some turns
        state.append_turn("first turn", "action1")
        state.append_turn("second turn", "action2")

        # Clear context
        state.clear_context()

        assert state.get_context_window() == []
        assert state.turn_count == 0

    def test_get_recent_actions(self):
        """Test getting recent actions for context."""
        state = ConversationState()

        # Add turns with different actions
        state.append_turn("schedule meeting", "create_event")
        state.append_turn("delete meeting", "delete_event")
        state.append_turn("move meeting", "move_event")

        recent_actions = state.get_recent_actions(2)
        assert len(recent_actions) == 2
        assert recent_actions[0] == "delete_event"
        assert recent_actions[1] == "move_event"

    def test_context_for_llm_prompt(self):
        """Test formatting context for LLM prompt."""
        state = ConversationState()

        # Add some conversation turns
        state.append_turn("schedule team meeting", "create_event")
        state.append_turn("what time?", "clarify")
        state.append_turn("2pm", "create_event")

        # Get formatted context for LLM
        context = state.get_context_for_llm_prompt()

        assert "schedule team meeting" in context
        assert "what time?" in context
        assert "2pm" in context
        assert "create_event" in context
        assert "clarify" in context

    def test_context_with_metadata(self):
        """Test that turns include metadata like timestamps."""
        state = ConversationState()

        state.append_turn("schedule meeting", "create_event")

        context = state.get_context_window()
        assert len(context) == 1

        turn = context[0]
        assert hasattr(turn, "timestamp")
        assert hasattr(turn, "user_input")
        assert hasattr(turn, "assistant_action")
        assert hasattr(turn, "assistant_details")

    def test_context_persistence_across_sessions(self):
        """Test that context is ephemeral (not persisted)."""
        state1 = ConversationState()
        state1.append_turn("schedule meeting", "create_event")

        # Create new state (simulating new session)
        state2 = ConversationState()

        assert state2.get_context_window() == []
        assert state2.turn_count == 0

    def test_reference_resolution_with_details(self):
        """Test reference resolution includes action details."""
        state = ConversationState()

        # Add turn with detailed action
        state.append_turn(
            "schedule team meeting tomorrow at 2pm",
            "create_event",
            {"title": "Team Meeting", "date": "2024-01-15", "time": "14:00"},
        )

        reference = state.resolve_reference("it")
        assert reference is not None
        assert "Team Meeting" in reference
        assert "2024-01-15" in reference

    def test_context_window_edge_cases(self):
        """Test edge cases for context window."""
        state = ConversationState(max_context_size=5)

        # Test with zero turns
        assert state.get_context_window(0) == []

        # Test with negative limit
        state.append_turn("test", "action")
        context = state.get_context_window(-1)
        assert len(context) == 0

        # Test with limit larger than available turns
        context = state.get_context_window(10)
        assert len(context) == 1  # Should return all available turns


class TestTurn:
    """Test the Turn data class."""

    def test_turn_creation(self):
        """Test creating a Turn object."""
        timestamp = datetime.now()
        turn = Turn(
            user_input="schedule meeting",
            assistant_action="create_event",
            assistant_details={"title": "Meeting"},
            timestamp=timestamp,
        )

        assert turn.user_input == "schedule meeting"
        assert turn.assistant_action == "create_event"
        assert turn.assistant_details == {"title": "Meeting"}
        assert turn.timestamp == timestamp

    def test_turn_default_timestamp(self):
        """Test Turn creation with default timestamp."""
        turn = Turn("schedule meeting", "create_event")

        assert turn.user_input == "schedule meeting"
        assert turn.assistant_action == "create_event"
        assert turn.timestamp is not None
        assert isinstance(turn.timestamp, datetime)

    def test_turn_optional_details(self):
        """Test Turn creation with optional details."""
        turn = Turn("schedule meeting", "create_event")

        assert turn.assistant_details == {}

        turn_with_details = Turn(
            "schedule meeting", "create_event", {"title": "Meeting", "duration": 60}
        )

        assert turn_with_details.assistant_details == {
            "title": "Meeting",
            "duration": 60,
        }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
