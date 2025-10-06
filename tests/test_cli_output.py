"""Tests for CLI rendering behavior (JSON-first)."""

import os
import json
import pytest
from datetime import datetime
from utils.cli_output import (
    render,
    format_error_message,
    format_success_message,
    format_clarification_question,
)


class TestRenderJson:
    """Test JSON-first render behavior."""

    def test_render_empty_events_json(self):
        os.environ["CLI_OUTPUT_MODE"] = "json"
        payload = {"type": "find_events", "result": []}
        s = render(payload)
        assert json.loads(s) == payload


class TestMessages:
    """Test message formatting that remains human-oriented."""


class TestFormatMessages:
    """Test message formatting functionality."""

    def test_format_error_message(self):
        """Test error message formatting."""
        result = format_error_message("Invalid date format")
        assert result == "❌ Error: Invalid date format"

    def test_format_error_message_with_suggestion(self):
        """Test error message formatting with suggestion."""
        result = format_error_message("Invalid date format", "Use YYYY-MM-DD")
        assert "❌ Error: Invalid date format" in result
        assert "💡 Suggestion: Use YYYY-MM-DD" in result

    def test_format_success_message(self):
        """Test success message formatting."""
        result = format_success_message("Event created successfully")
        assert result == "✅ Event created successfully"

    def test_format_clarification_question(self):
        """Test clarification question formatting."""
        result = format_clarification_question("Which Monday?")
        assert result == "🤔 Which Monday?"

    def test_format_clarification_question_with_context(self):
        """Test clarification question formatting with context."""
        result = format_clarification_question(
            "Which Monday?", "There are multiple Mondays this month"
        )
        assert "🤔 Which Monday?" in result
        assert "📝 Context: There are multiple Mondays this month" in result


class TestPrettySnapshots:
    """Lightweight pretty-mode checks, not core assertions."""

    def test_pretty_no_events_contains_phrase(self):
        os.environ["CLI_OUTPUT_MODE"] = "pretty"
        from utils.cli_output import render as pretty_render

        s = pretty_render({"type": "find_events", "result": []})
        assert "No events" in s


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
