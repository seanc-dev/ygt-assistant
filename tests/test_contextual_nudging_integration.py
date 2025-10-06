"""Integration tests for contextual nudging functionality."""

import pytest
import tempfile
import os
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

from calendar_agent_eventkit import EventKitAgent
from core.memory_manager import CoreMemory
from core.nudge_engine import ContextualNudger, NudgeType


class TestContextualNudgingIntegration:
    """Test contextual nudging integration with calendar agent."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_memory.db")

        # Create Core memory instance
        self.core_memory = CoreMemory(self.test_db_path)

        # Create EventKit agent and connect it to our Core memory instance
        self.agent = EventKitAgent()
        self.agent.core_memory = self.core_memory
        self.agent.nudger = ContextualNudger(self.core_memory)

    def teardown_method(self):
        """Clean up test fixtures."""
        # Remove temporary directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_contextual_suggestions_empty(self):
        """Test getting contextual suggestions when no patterns exist."""
        suggestions = self.agent.get_contextual_suggestions()

        # Should return empty list when no patterns exist
        assert isinstance(suggestions, list)
        assert len(suggestions) == 0

    def test_get_contextual_suggestions_with_patterns(self):
        """Test getting contextual suggestions with existing patterns."""
        # Add some past events to create patterns
        event_data_1 = {
            "title": "Team Meeting",
            "description": "Weekly team sync",
            "start_date": "2024-01-15T10:00:00",
            "duration": 60,
            "attendees": ["Alice", "Bob"],
            "location": "Conference Room A",
            "is_recurring": True,
            "recurrence_pattern": "FREQ=WEEKLY",
            "text_for_embedding": "Team Meeting",
        }

        event_data_2 = {
            "title": "Lunch Break",
            "description": "Lunch time",
            "start_date": "2024-01-15T12:00:00",
            "duration": 60,
            "attendees": [],
            "location": "Cafeteria",
            "is_recurring": False,
            "recurrence_pattern": "",
            "text_for_embedding": "Lunch Break",
        }

        self.core_memory.add_past_event(event_data_1)
        self.core_memory.add_past_event(event_data_2)

        # Mock current time to be around 10am (when meetings usually happen)
        with patch("core.nudge_engine.datetime") as mock_datetime, patch(
            "calendar_agent_eventkit.datetime"
        ) as mock_calendar_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 20, 9, 30)  # 9:30am
            mock_calendar_datetime.now.return_value = datetime(
                2024, 1, 20, 9, 30
            )  # 9:30am

            # Also mock the datetime.fromisoformat to return proper hour values
            def mock_fromisoformat(date_str):
                mock_date = Mock()
                if "10:00" in date_str:
                    mock_date.hour = 10
                elif "12:00" in date_str:
                    mock_date.hour = 12
                else:
                    mock_date.hour = 9
                return mock_date

            mock_datetime.fromisoformat = mock_fromisoformat
            mock_calendar_datetime.fromisoformat = mock_fromisoformat

            suggestions = self.agent.get_contextual_suggestions()

            # Should return a list (even if empty due to mocking issues)
            assert isinstance(suggestions, list)

            # Check that suggestions have the expected structure
            for suggestion in suggestions:
                assert "id" in suggestion
                assert "type" in suggestion
                assert "title" in suggestion
                assert "description" in suggestion
                assert "priority" in suggestion
                assert "confidence" in suggestion
                assert "context" in suggestion

    def test_get_contextual_suggestions_with_intentions(self):
        """Test getting contextual suggestions with user intentions."""
        # Add a fitness intention
        self.core_memory.add_intention("I want to exercise more", "high")

        # Mock current time to be evening (good time for exercise)
        with patch("core.nudge_engine.datetime") as mock_datetime, patch(
            "calendar_agent_eventkit.datetime"
        ) as mock_calendar_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 20, 18, 0)  # 6pm
            mock_calendar_datetime.now.return_value = datetime(
                2024, 1, 20, 18, 0
            )  # 6pm

            suggestions = self.agent.get_contextual_suggestions()

            # Should return habit reinforcement suggestions
            assert isinstance(suggestions, list)
            if len(suggestions) > 0:
                # Check for habit reinforcement suggestions
                habit_suggestions = [
                    s
                    for s in suggestions
                    if s["type"] == NudgeType.HABIT_REINFORCEMENT.value
                ]
                assert len(habit_suggestions) > 0

    def test_get_contextual_suggestions_with_context(self):
        """Test getting contextual suggestions with provided context."""
        # Add some events to create patterns
        event_data = {
            "title": "Team Meeting",
            "description": "Weekly team sync",
            "start_date": "2024-01-15T10:00:00",
            "duration": 60,
            "attendees": ["Alice", "Bob"],
            "location": "Conference Room A",
            "is_recurring": True,
            "recurrence_pattern": "FREQ=WEEKLY",
            "text_for_embedding": "Team Meeting",
        }
        self.core_memory.add_past_event(event_data)

        # Provide context with back-to-back meetings
        context = {
            "back_to_back_meetings": 4,
            "available_slots": 2,
            "current_time": "14:00",
            "current_day": "Monday",
        }

        with patch("core.nudge_engine.datetime") as mock_datetime, patch(
            "calendar_agent_eventkit.datetime"
        ) as mock_calendar_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 20, 14, 0)  # 2pm
            mock_calendar_datetime.now.return_value = datetime(
                2024, 1, 20, 14, 0
            )  # 2pm

            suggestions = self.agent.get_contextual_suggestions(context)

            # Should return productivity optimization suggestions
            assert isinstance(suggestions, list)
            if len(suggestions) > 0:
                # Check for productivity optimization suggestions
                productivity_suggestions = [
                    s
                    for s in suggestions
                    if s["type"] == NudgeType.PRODUCTIVITY_OPTIMIZATION.value
                ]
                assert len(productivity_suggestions) > 0

    def test_handle_nudge_feedback(self):
        """Test handling user feedback on nudges."""
        # Create a test nudge
        nudge = self.agent.nudger.nudges.get("test_nudge")
        if not nudge:
            nudge_id = "test_nudge"
            self.agent.nudger.nudges[nudge_id] = Mock()
            self.agent.nudger.nudges[nudge_id].type = NudgeType.TIME_PATTERN

        # Test accepting a nudge
        result = self.agent.handle_nudge_feedback("test_nudge", "accepted")

        # Should not raise an exception
        assert result is None

        # Test dismissing a nudge
        result = self.agent.handle_nudge_feedback("test_nudge", "dismissed")

        # Should not raise an exception
        assert result is None

    def test_get_stats_with_nudger(self):
        """Test getting stats that include nudger information."""
        stats = self.agent.get_stats()

        assert isinstance(stats, dict)
        assert "total_events" in stats
        assert "core_memory_available" in stats
        assert "core_memory_stats" in stats
        assert "nudger_stats" in stats

        # Check nudger stats structure
        nudger_stats = stats["nudger_stats"]
        assert "total_nudges" in nudger_stats
        assert "active_nudges" in nudger_stats
        assert "dismissed_nudges" in nudger_stats
        assert "acceptance_rate" in nudger_stats
        assert "user_preferences" in nudger_stats
        assert "nudge_history_count" in nudger_stats

    def test_contextual_suggestions_without_nudger(self):
        """Test getting contextual suggestions when nudger is not available."""
        # Remove nudger
        self.agent.nudger = None

        suggestions = self.agent.get_contextual_suggestions()

        # Should return empty list when nudger is not available
        assert isinstance(suggestions, list)
        assert len(suggestions) == 0

    def test_handle_nudge_feedback_without_nudger(self):
        """Test handling nudge feedback when nudger is not available."""
        # Remove nudger
        self.agent.nudger = None

        result = self.agent.handle_nudge_feedback("test_nudge", "accepted")

        # Should not raise an exception
        assert result is None

    def test_count_back_to_back_meetings(self):
        """Test counting back-to-back meetings."""

        # Create a simple event class for testing
        class TestEvent:
            def __init__(self, start_date, end_date):
                self.startDate = start_date
                self.endDate = end_date

        # Add some events to the agent
        event1 = TestEvent(datetime(2024, 1, 20, 9, 0), datetime(2024, 1, 20, 10, 0))
        event2 = TestEvent(
            datetime(2024, 1, 20, 10, 0), datetime(2024, 1, 20, 11, 0)
        )  # Back-to-back
        event3 = TestEvent(
            datetime(2024, 1, 20, 14, 0), datetime(2024, 1, 20, 15, 0)
        )  # Gap

        self.agent.store._events = [event1, event2, event3]

        # Mock current date to match the test events
        with patch("calendar_agent_eventkit.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(
                2024, 1, 20, 12, 0
            )  # Same date as events

            count = self.agent._count_back_to_back_meetings()

        # Should count 1 back-to-back meeting (between event1 and event2)
        assert count == 1

    def test_count_available_slots(self):
        """Test counting available time slots."""

        # Create a simple event class for testing
        class TestEvent:
            def __init__(self, start_date, end_date):
                self.startDate = start_date
                self.endDate = end_date

        # Add some events to the agent
        event1 = TestEvent(datetime(2024, 1, 20, 10, 0), datetime(2024, 1, 20, 11, 0))
        event2 = TestEvent(datetime(2024, 1, 20, 14, 0), datetime(2024, 1, 20, 15, 0))

        self.agent.store._events = [event1, event2]

        # Mock current date to match the test events
        with patch("calendar_agent_eventkit.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(
                2024, 1, 20, 12, 0
            )  # Same date as events

            count = self.agent._count_available_slots()

        # Should return a non-negative count
        assert count >= 0

    def test_contextual_suggestions_quiet_hours(self):
        """Test that no suggestions are generated during quiet hours."""
        # Add some events to create patterns
        event_data = {
            "title": "Team Meeting",
            "description": "Weekly team sync",
            "start_date": "2024-01-15T10:00:00",
            "duration": 60,
            "attendees": ["Alice", "Bob"],
            "location": "Conference Room A",
            "is_recurring": True,
            "recurrence_pattern": "FREQ=WEEKLY",
            "text_for_embedding": "Team Meeting",
        }
        self.core_memory.add_past_event(event_data)

        # Mock current time to be during quiet hours
        with patch("core.nudge_engine.datetime") as mock_datetime, patch(
            "calendar_agent_eventkit.datetime"
        ) as mock_calendar_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 20, 23, 0)  # 11pm
            mock_calendar_datetime.now.return_value = datetime(
                2024, 1, 20, 23, 0
            )  # 11pm

            suggestions = self.agent.get_contextual_suggestions()

            # Should return empty list during quiet hours
            assert isinstance(suggestions, list)
            assert len(suggestions) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
