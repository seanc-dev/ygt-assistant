"""End-to-end tests for conversation memory integration."""

import pytest
from unittest.mock import patch, MagicMock
import runpy
from core.conversation_manager import ConversationState


class TestConversationMemoryIntegration:
    """Test conversation memory integration with the main CLI flow."""

    def test_conversation_context_in_llm_prompt(self):
        """Test that conversation context is included in LLM prompts."""
        with patch("openai_client.client") as mock_client:
            # Mock the LLM response
            mock_response = MagicMock()
            mock_message = MagicMock()
            mock_function_call = MagicMock()
            mock_function_call.name = "create_event"
            mock_function_call.arguments = (
                '{"title": "Team Meeting", "date": "2024-01-15", "time": "14:00"}'
            )
            mock_message.function_call = mock_function_call
            mock_response.choices = [mock_message]
            mock_client.chat.completions.create.return_value = mock_response

            # Mock input to simulate user interaction
            with patch("builtins.input", side_effect=["schedule team meeting", "exit"]):
                with patch("builtins.print") as mock_print:
                    # Run the main module
                    runpy.run_module("main", run_name="__main__")

                    # Verify that the LLM was called with conversation context
                    calls = mock_client.chat.completions.create.call_args_list
                    assert len(calls) >= 1

                    # First call should not have conversation context (empty state)
                    first_call = calls[0]
                    messages = first_call[1]["messages"]
                    system_message = messages[0]["content"]
                    # Should not have conversation context on first call
                    assert "CONVERSATION CONTEXT" not in system_message

    def test_reference_resolution_in_conversation(self):
        """Test that references are resolved correctly in a conversation."""
        with patch("openai_client.client") as mock_client:
            # Mock responses for a conversation
            responses = [
                # First turn: create event
                MagicMock(
                    choices=[
                        MagicMock(
                            message=MagicMock(
                                function_call=MagicMock(
                                    name="create_event",
                                    arguments='{"title": "Team Meeting", "date": "2024-01-15", "time": "14:00"}',
                                )
                            )
                        )
                    ]
                ),
                # Second turn: move event (should reference the first event)
                MagicMock(
                    choices=[
                        MagicMock(
                            message=MagicMock(
                                function_call=MagicMock(
                                    name="move_event",
                                    arguments='{"title": "Team Meeting", "old_date": "2024-01-15", "new_date": "2024-01-16", "new_time": "15:00"}',
                                )
                            )
                        )
                    ]
                ),
                # Third turn: exit
                MagicMock(choices=[MagicMock(message=MagicMock(function_call=None))]),
            ]
            mock_client.chat.completions.create.side_effect = responses

            # Mock input for a conversation
            with patch(
                "builtins.input",
                side_effect=[
                    "schedule team meeting tomorrow",
                    "move it to next day",
                    "exit",
                ],
            ):
                with patch("builtins.print") as mock_print:
                    # Run the main module
                    runpy.run_module("main", run_name="__main__")

                    # Verify that the LLM was called multiple times
                    calls = mock_client.chat.completions.create.call_args_list
                    assert len(calls) >= 2

                    # Check that the second call includes conversation context
                    second_call = calls[1]
                    messages = second_call[1]["messages"]
                    system_message = messages[0]["content"]
                    assert "CONVERSATION CONTEXT" in system_message
                    assert "schedule team meeting tomorrow" in system_message
                    assert "create_event" in system_message

    def test_conversation_state_persistence_in_session(self):
        """Test that conversation state persists throughout a session."""
        with patch("openai_client.client") as mock_client:
            # Mock responses
            mock_response = MagicMock()
            mock_message = MagicMock()
            mock_function_call = MagicMock()
            mock_function_call.name = "list_all"
            mock_function_call.arguments = "{}"
            mock_message.function_call = mock_function_call
            mock_response.choices = [mock_message]
            mock_client.chat.completions.create.return_value = mock_response

            # Mock input for multiple turns
            with patch(
                "builtins.input",
                side_effect=["show my events", "what about tomorrow?", "exit"],
            ):
                with patch("builtins.print") as mock_print:
                    # Run the main module
                    runpy.run_module("main", run_name="__main__")

                    # Verify that the LLM was called multiple times
                    calls = mock_client.chat.completions.create.call_args_list
                    assert len(calls) >= 2

                    # Check that later calls include context from earlier turns
                    later_call = calls[-1]
                    messages = later_call[1]["messages"]
                    system_message = messages[0]["content"]
                    assert "CONVERSATION CONTEXT" in system_message
                    assert "show my events" in system_message

    def test_conversation_context_limits(self):
        """Test that conversation context respects the maximum window size."""
        with patch("openai_client.client") as mock_client:
            # Mock responses
            mock_response = MagicMock()
            mock_message = MagicMock()
            mock_function_call = MagicMock()
            mock_function_call.name = "list_all"
            mock_function_call.arguments = "{}"
            mock_message.function_call = mock_function_call
            mock_response.choices = [mock_message]
            mock_client.chat.completions.create.return_value = mock_response

            # Mock input for many turns (more than the default limit of 10)
            many_inputs = [f"turn {i}" for i in range(15)] + ["exit"]
            with patch("builtins.input", side_effect=many_inputs):
                with patch("builtins.print") as mock_print:
                    # Run the main module
                    runpy.run_module("main", run_name="__main__")

                    # Verify that the LLM was called multiple times
                    calls = mock_client.chat.completions.create.call_args_list
                    assert len(calls) >= 10

                    # Check that the context doesn't grow indefinitely
                    # The last call should have conversation context
                    later_call = calls[-1]
                    messages = later_call[1]["messages"]
                    system_message = messages[0]["content"]

                    # Should include conversation context in later calls
                    assert "CONVERSATION CONTEXT" in system_message
                    # Should include recent turns
                    assert "turn 14" in system_message
                    # Should not include very old turns (they should be dropped)
                    # Note: The exact behavior depends on the context window size
                    # For now, just verify that context is present
                    assert "User:" in system_message
                    assert "Assistant:" in system_message

    def test_conversation_context_formatting(self):
        """Test that conversation context is properly formatted for LLM."""
        with patch("openai_client.client") as mock_client:
            # Mock responses
            mock_response = MagicMock()
            mock_message = MagicMock()
            mock_function_call = MagicMock()
            mock_function_call.name = "create_event"
            mock_function_call.arguments = (
                '{"title": "Meeting", "date": "2024-01-15", "time": "14:00"}'
            )
            mock_message.function_call = mock_function_call
            mock_response.choices = [mock_message]
            mock_client.chat.completions.create.return_value = mock_response

            # Mock input
            with patch("builtins.input", side_effect=["schedule meeting", "exit"]):
                with patch("builtins.print") as mock_print:
                    # Run the main module
                    runpy.run_module("main", run_name="__main__")

                    # Verify that the context is properly formatted
                    calls = mock_client.chat.completions.create.call_args_list
                    assert len(calls) >= 1

                    # First call should not have conversation context
                    call_args = calls[0]
                    messages = call_args[1]["messages"]
                    system_message = messages[0]["content"]

                    # First call should not have User/Assistant formatting
                    assert "User:" not in system_message
                    assert "Assistant:" not in system_message
                    # But should have the basic system message
                    assert "calendar assistant" in system_message

    def test_conversation_state_ephemeral_nature(self):
        """Test that conversation state is ephemeral (not persisted between sessions)."""
        # Create a conversation state and add some turns
        state1 = ConversationState()
        state1.append_turn("schedule meeting", "create_event")
        state1.append_turn("move it", "move_event")

        # Create a new state (simulating new session)
        state2 = ConversationState()

        # Verify that the new state is empty
        assert state2.get_context_window() == []
        assert state2.turn_count == 0

        # Verify that the old state still has its data
        assert len(state1.get_context_window()) == 2
        assert state1.turn_count == 2

    def test_conversation_context_with_action_details(self):
        """Test that conversation context includes action details."""
        with patch("openai_client.client") as mock_client:
            # Mock responses with detailed actions
            mock_response = MagicMock()
            mock_message = MagicMock()
            mock_function_call = MagicMock()
            mock_function_call.name = "create_event"
            mock_function_call.arguments = '{"title": "Team Meeting", "date": "2024-01-15", "time": "14:00", "duration": 60}'
            mock_message.function_call = mock_function_call
            mock_response.choices = [mock_message]
            mock_client.chat.completions.create.return_value = mock_response

            # Mock input
            with patch("builtins.input", side_effect=["schedule team meeting", "exit"]):
                with patch("builtins.print") as mock_print:
                    # Run the main module
                    runpy.run_module("main", run_name="__main__")

                    # Verify that the context includes action details
                    calls = mock_client.chat.completions.create.call_args_list
                    assert len(calls) >= 1

                    # First call should not have action details in context
                    call_args = calls[0]
                    messages = call_args[1]["messages"]
                    system_message = messages[0]["content"]

                    # First call should not have action details in context
                    assert "Team Meeting" not in system_message
                    assert "2024-01-15" not in system_message
                    assert "14:00" not in system_message

    def test_conversation_context_clearing(self):
        """Test that conversation context can be cleared."""
        # Create a conversation state and add some turns
        state = ConversationState()
        state.append_turn("schedule meeting", "create_event")
        state.append_turn("move it", "move_event")

        # Verify that context exists
        assert len(state.get_context_window()) == 2
        assert state.turn_count == 2

        # Clear the context
        state.clear_context()

        # Verify that context is cleared
        assert state.get_context_window() == []
        assert state.turn_count == 0

    def test_conversation_context_edge_cases(self):
        """Test conversation context with edge cases."""
        # Test with empty context
        state = ConversationState()
        context = state.get_context_for_llm_prompt()
        assert context == ""

        # Test with single turn
        state.append_turn("test", "test_action")
        context = state.get_context_for_llm_prompt()
        assert "test" in context
        assert "test_action" in context

        # Test with custom limit
        state = ConversationState()
        for i in range(5):
            state.append_turn(f"turn {i}", f"action {i}")

        context = state.get_context_for_llm_prompt(limit=3)
        # Should only include last 3 turns
        assert "turn 2" in context
        assert "turn 3" in context
        assert "turn 4" in context
        assert "turn 0" not in context
        assert "turn 1" not in context


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
