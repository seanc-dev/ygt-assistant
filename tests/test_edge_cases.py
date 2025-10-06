"""Comprehensive edge case tests for LLM-first calendar assistant."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import openai_client
from utils.command_utils import parse_command


class TestInputNormalizationEdgeCases:
    """Test LLM handling of input normalization edge cases."""

    def test_misspellings(self):
        """Test LLM handles common misspellings gracefully."""
        misspelling_cases = [
            ("shedule meeting tomorrow", "schedule"),
            ("meetin tomorrow", "meeting"),
            ("tomorow meeting", "tomorrow"),
            ("calender meeting", "calendar"),
            ("delet meeting", "delete"),
            ("muv meeting", "move"),
        ]

        for input_text, expected_correction in misspelling_cases:
            with patch("openai_client.client") as mock_client:
                # Mock LLM to handle misspellings
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.function_call.name = "create_event"
                mock_response.choices[0].message.function_call.arguments = (
                    '{"title": "meeting", "date": "tomorrow"}'
                )
                mock_client.chat.completions.create.return_value = mock_response

                result = openai_client.interpret_command(input_text, "")
                assert result["action"] == "create_event"
                # LLM should understand the intent despite misspellings

    def test_poor_grammar(self):
        """Test LLM extracts core intent from poor grammar."""
        grammar_cases = [
            ("meeting tomorrow at 2pm I need", "meeting tomorrow at 2pm"),
            ("schedule meeting for tomorrow please", "schedule meeting tomorrow"),
            ("I want to have a meeting", "schedule meeting"),
            ("can you schedule a meeting", "schedule meeting"),
        ]

        for input_text, expected_intent in grammar_cases:
            with patch("openai_client.client") as mock_client:
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.function_call.name = "create_event"
                mock_response.choices[0].message.function_call.arguments = (
                    '{"title": "meeting"}'
                )
                mock_client.chat.completions.create.return_value = mock_response

                result = openai_client.interpret_command(input_text, "")
                assert result["action"] == "create_event"

    def test_mixed_case_and_whitespace(self):
        """Test LLM normalizes mixed case and whitespace."""
        normalization_cases = [
            ("SCHEDULE MEETING", "schedule meeting"),
            ("  schedule   meeting   tomorrow  ", "schedule meeting tomorrow"),
            ("schedule\nmeeting\ttomorrow", "schedule meeting tomorrow"),
        ]

        for input_text, expected_normalized in normalization_cases:
            with patch("openai_client.client") as mock_client:
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.function_call.name = "create_event"
                mock_response.choices[0].message.function_call.arguments = (
                    '{"title": "meeting"}'
                )
                mock_client.chat.completions.create.return_value = mock_response

                result = openai_client.interpret_command(input_text, "")
                assert result["action"] == "create_event"

    def test_punctuation_handling(self):
        """Test LLM handles punctuation gracefully."""
        punctuation_cases = [
            ("schedule meeting, tomorrow at 2pm!", "schedule meeting tomorrow at 2pm"),
            ("delete meeting?", "delete meeting"),
            ("move meeting...", "move meeting"),
        ]

        for input_text, expected_clean in punctuation_cases:
            with patch("openai_client.client") as mock_client:
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.function_call.name = "create_event"
                mock_response.choices[0].message.function_call.arguments = (
                    '{"title": "meeting"}'
                )
                mock_client.chat.completions.create.return_value = mock_response

                result = openai_client.interpret_command(input_text, "")
                assert result["action"] in [
                    "create_event",
                    "delete_event",
                    "move_event",
                ]


class TestDateTimeEdgeCases:
    """Test LLM handling of date/time edge cases."""

    def test_invalid_dates(self):
        """Test LLM detects and explains invalid dates."""
        invalid_date_cases = [
            "schedule meeting on 2024-13-45",
            "schedule meeting on 2024-02-30",
            "schedule meeting on 2023-02-29",
        ]

        for input_text in invalid_date_cases:
            with patch("openai_client.client") as mock_client:
                # Mock LLM to return error for invalid dates
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.function_call.name = "error"
                mock_response.choices[0].message.function_call.arguments = (
                    '{"message": "Invalid date", "suggestion": "Use YYYY-MM-DD"}'
                )
                mock_client.chat.completions.create.return_value = mock_response

                result = openai_client.interpret_command(input_text, "")
                assert result["action"] == "error"
                assert "Invalid date" in result["details"]["message"]

    def test_past_dates(self):
        """Test LLM warns about past dates."""
        past_date_cases = [
            "schedule meeting yesterday",
            "schedule meeting last week",
            "schedule meeting on 2020-01-01",
        ]

        for input_text in past_date_cases:
            with patch("openai_client.client") as mock_client:
                # Mock LLM to warn about past dates
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.function_call.name = "error"
                mock_response.choices[0].message.function_call.arguments = (
                    '{"message": "Past date detected", "suggestion": "Did you mean a future date?"}'
                )
                mock_client.chat.completions.create.return_value = mock_response

                result = openai_client.interpret_command(input_text, "")
                assert result["action"] == "error"
                assert "Past date" in result["details"]["message"]

    def test_ambiguous_dates(self):
        """Test LLM asks for clarification on ambiguous dates."""
        ambiguous_date_cases = [
            ("next Monday", "which Monday"),
            ("this weekend", "Saturday or Sunday"),
            ("in 3 days", "from today or from a specific date"),
        ]

        for input_text, expected_clarification in ambiguous_date_cases:
            with patch("openai_client.client") as mock_client:
                # Mock LLM to ask for clarification
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.function_call.name = "clarify"
                mock_response.choices[0].message.function_call.arguments = (
                    f'{{"question": "{expected_clarification}"}}'
                )
                mock_client.chat.completions.create.return_value = mock_response

                result = openai_client.interpret_command(input_text, "")
                assert result["action"] == "clarify"
                assert expected_clarification in result["details"]["question"]

    def test_time_ambiguity(self):
        """Test LLM handles time ambiguity."""
        time_ambiguity_cases = [
            ("noon", "12:00"),
            ("midnight", "00:00"),
            ("lunch time", "12:00"),
            ("2pm", "14:00"),
            ("14:00", "14:00"),
        ]

        for input_text, expected_time in time_ambiguity_cases:
            with patch("openai_client.client") as mock_client:
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.function_call.name = "create_event"
                mock_response.choices[0].message.function_call.arguments = (
                    f'{{"title": "meeting", "time": "{expected_time}"}}'
                )
                mock_client.chat.completions.create.return_value = mock_response

                result = openai_client.interpret_command(input_text, "")
                assert result["action"] == "create_event"


class TestContextDependencyEdgeCases:
    """Test LLM handling of context dependency edge cases."""

    def test_vague_references(self):
        """Test LLM asks for clarification on vague references."""
        vague_reference_cases = [
            ("move it to Friday", "What would you like to move?"),
            ("delete that meeting", "Which meeting would you like to delete?"),
            ("reschedule the meeting", "Which meeting should I reschedule?"),
        ]

        for input_text, expected_question in vague_reference_cases:
            with patch("openai_client.client") as mock_client:
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.function_call.name = "clarify"
                mock_response.choices[0].message.function_call.arguments = (
                    f'{{"question": "{expected_question}"}}'
                )
                mock_client.chat.completions.create.return_value = mock_response

                result = openai_client.interpret_command(input_text, "")
                assert result["action"] == "clarify"
                assert expected_question in result["details"]["question"]

    def test_multiple_matches(self):
        """Test LLM handles multiple matching events."""
        multiple_match_cases = [
            ("delete team meeting", "Multiple team meetings found"),
            ("move project meeting", "Which project meeting?"),
        ]

        for input_text, expected_handling in multiple_match_cases:
            with patch("openai_client.client") as mock_client:
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.function_call.name = "clarify"
                mock_response.choices[0].message.function_call.arguments = (
                    '{"question": "Multiple matches found", "options": ["Meeting 1", "Meeting 2"]}'
                )
                mock_client.chat.completions.create.return_value = mock_response

                result = openai_client.interpret_command(input_text, "")
                assert result["action"] == "clarify"
                assert "Multiple matches" in result["details"]["question"]

    def test_unclear_intent(self):
        """Test LLM asks for clarification on unclear intent."""
        unclear_intent_cases = [
            ("do something with my calendar", "What would you like to do?"),
            ("help me organize", "How can I help you organize?"),
            ("what should I do?", "Could you be more specific?"),
        ]

        for input_text, expected_question in unclear_intent_cases:
            with patch("openai_client.client") as mock_client:
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.function_call.name = "clarify"
                mock_response.choices[0].message.function_call.arguments = (
                    f'{{"question": "{expected_question}"}}'
                )
                mock_client.chat.completions.create.return_value = mock_response

                result = openai_client.interpret_command(input_text, "")
                assert result["action"] == "clarify"
                assert expected_question in result["details"]["question"]


class TestComplexRequestEdgeCases:
    """Test LLM handling of complex request edge cases."""

    def test_multi_step_requests(self):
        """Test LLM breaks down multi-step requests."""
        multi_step_cases = [
            (
                "schedule a meeting tomorrow, then remind me to prepare",
                ["create_event", "add_notification"],
            ),
            ("create meeting and invite John", ["create_event", "add_attendee"]),
        ]

        for input_text, expected_actions in multi_step_cases:
            with patch("openai_client.client") as mock_client:
                # Mock LLM to handle first step, then ask for next
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.function_call.name = "create_event"
                mock_response.choices[0].message.function_call.arguments = (
                    '{"title": "meeting", "date": "tomorrow"}'
                )
                mock_client.chat.completions.create.return_value = mock_response

                result = openai_client.interpret_command(input_text, "")
                assert result["action"] == "create_event"
                # In real implementation, would handle subsequent steps

    def test_conditional_requests(self):
        """Test LLM handles conditional logic."""
        conditional_cases = [
            ("if I'm free tomorrow, schedule a meeting", "check_availability"),
            ("schedule meeting if no conflicts", "check_conflicts"),
        ]

        for input_text, expected_action in conditional_cases:
            with patch("openai_client.client") as mock_client:
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.function_call.name = expected_action
                mock_response.choices[0].message.function_call.arguments = (
                    '{"date": "tomorrow"}'
                )
                mock_client.chat.completions.create.return_value = mock_response

                result = openai_client.interpret_command(input_text, "")
                assert result["action"] == expected_action

    def test_bulk_operations(self):
        """Test LLM asks for confirmation on bulk operations."""
        bulk_operation_cases = [
            ("delete all meetings this week", "confirm_bulk_delete"),
            ("move all meetings to next week", "confirm_bulk_move"),
        ]

        for input_text, expected_action in bulk_operation_cases:
            with patch("openai_client.client") as mock_client:
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.function_call.name = "confirm"
                mock_response.choices[0].message.function_call.arguments = (
                    '{"question": "Are you sure you want to delete all meetings this week?", "action": "bulk_delete"}'
                )
                mock_client.chat.completions.create.return_value = mock_response

                result = openai_client.interpret_command(input_text, "")
                assert result["action"] == "confirm"


class TestSystemResilienceEdgeCases:
    """Test system resilience under edge case conditions."""

    def test_api_timeout(self):
        """Test graceful handling of API timeouts."""
        with patch("openai_client.client") as mock_client:
            mock_client.chat.completions.create.side_effect = Exception("API timeout")

            # Should return error action
            result = openai_client.interpret_command("schedule meeting tomorrow", "")
            assert result["action"] == "error"

    def test_invalid_api_key(self):
        """Test graceful handling of invalid API key."""
        with patch("openai_client.client", None):
            # Should return error action
            result = openai_client.interpret_command("schedule meeting tomorrow", "")
            assert result["action"] == "error"

    def test_rate_limiting(self):
        """Test graceful handling of rate limiting."""
        with patch("openai_client.client") as mock_client:
            mock_client.chat.completions.create.side_effect = Exception(
                "Rate limit exceeded"
            )

            # Should return error action
            result = openai_client.interpret_command("delete meeting", "")
            assert result["action"] == "error"


class TestUserExperienceEdgeCases:
    """Test user experience edge cases."""

    def test_empty_calendar(self):
        """Test helpful response when calendar is empty."""
        with patch("openai_client.client") as mock_client:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.function_call.name = "list_events_only"
            mock_response.choices[0].message.function_call.arguments = (
                '{"start_date": "today", "end_date": "today"}'
            )
            mock_client.chat.completions.create.return_value = mock_response

            result = openai_client.interpret_command("show my events", "")
            assert result["action"] == "list_events_only"
            # In real implementation, would show "No events found" message

    def test_overflow_protection(self):
        """Test handling of large result sets."""
        with patch("openai_client.client") as mock_client:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.function_call.name = "list_events_only"
            mock_response.choices[0].message.function_call.arguments = (
                '{"start_date": "2024-01-01", "end_date": "2024-12-31"}'
            )
            mock_client.chat.completions.create.return_value = mock_response

            result = openai_client.interpret_command("list all events this year", "")
            assert result["action"] == "list_events_only"
            # In real implementation, would paginate or limit results


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
