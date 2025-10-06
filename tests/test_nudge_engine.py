"""Tests for the contextual nudging engine functionality."""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from core.nudge_engine import ContextualNudger, NudgeType, Nudge
from core.memory_manager import CoreMemory, MemoryType


class TestContextualNudger:
    """Test the contextual nudging engine functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_memory.db")

        # Create Core memory instance
        self.core_memory = CoreMemory(self.test_db_path)

        # Create nudger instance
        self.nudger = ContextualNudger(self.core_memory)

    def teardown_method(self):
        """Clean up test fixtures."""
        # Remove temporary directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test nudger initialization."""
        assert self.nudger.core_memory == self.core_memory
        assert isinstance(self.nudger.nudges, dict)
        assert isinstance(self.nudger.user_preferences, dict)
        assert isinstance(self.nudger.nudge_history, list)

    def test_analyze_time_patterns(self):
        """Test time pattern analysis."""
        # Add some past events with different times
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

        event_data_3 = {
            "title": "Gym Session",
            "description": "Workout",
            "start_date": "2024-01-15T18:00:00",
            "duration": 90,
            "attendees": [],
            "location": "Gym",
            "is_recurring": False,
            "recurrence_pattern": "",
            "text_for_embedding": "Gym Session",
        }

        self.core_memory.add_past_event(event_data_1)
        self.core_memory.add_past_event(event_data_2)
        self.core_memory.add_past_event(event_data_3)

        patterns = self.nudger.analyze_time_patterns()

        assert "meeting_times" in patterns
        assert "break_times" in patterns
        assert "health_activities" in patterns

        # Check that patterns were correctly categorized
        meeting_times = patterns["meeting_times"]
        assert len(meeting_times) == 1
        assert meeting_times[0]["hour"] == 10
        assert meeting_times[0]["title"] == "Team Meeting"

        break_times = patterns["break_times"]
        assert len(break_times) == 1
        assert break_times[0]["hour"] == 12
        assert break_times[0]["title"] == "Lunch Break"

        health_activities = patterns["health_activities"]
        assert len(health_activities) == 1
        assert health_activities[0]["hour"] == 18
        assert health_activities[0]["title"] == "Gym Session"

    def test_generate_time_based_suggestions(self):
        """Test time-based suggestion generation."""
        # Add events with regular patterns
        for i in range(3):  # Add 3 meetings at 10am
            event_data = {
                "title": f"Team Meeting {i+1}",
                "description": "Regular meeting",
                "start_date": f"2024-01-{15+i}T10:00:00",
                "duration": 60,
                "attendees": ["Alice", "Bob"],
                "location": "Conference Room A",
                "is_recurring": False,
                "recurrence_pattern": "",
                "text_for_embedding": f"Team Meeting {i+1}",
            }
            self.core_memory.add_past_event(event_data)

        # Mock current time to be around 10am
        with patch("core.nudge_engine.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 20, 9, 30)  # 9:30am

            # Also mock the datetime.fromisoformat to return proper hour values
            def mock_fromisoformat(date_str):
                mock_date = Mock()
                mock_date.hour = 10  # All meetings at 10am
                return mock_date

            mock_datetime.fromisoformat = mock_fromisoformat

            patterns = self.nudger.analyze_time_patterns()
            suggestions = self.nudger._generate_time_based_suggestions(
                patterns, 9, "Monday"
            )

            assert len(suggestions) == 1
            suggestion = suggestions[0]
            assert suggestion.type == NudgeType.TIME_PATTERN
            assert "Regular meeting time approaching" in suggestion.title
            assert "10:00" in suggestion.description

    def test_generate_habit_suggestions(self):
        """Test habit reinforcement suggestion generation."""
        # Add a fitness intention
        self.core_memory.add_intention("I want to exercise more", "high")

        # Mock current time to be evening (good time for exercise)
        with patch("core.nudge_engine.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 20, 18, 0)  # 6pm

            current_context = {"current_time": "18:00"}
            suggestions = self.nudger._generate_habit_suggestions(current_context)

            assert len(suggestions) == 1
            suggestion = suggestions[0]
            assert suggestion.type == NudgeType.HABIT_REINFORCEMENT
            assert "fitness goal" in suggestion.title
            assert "exercise" in suggestion.description

    def test_generate_productivity_suggestions(self):
        """Test productivity optimization suggestion generation."""
        # Test back-to-back meetings suggestion
        current_context = {"back_to_back_meetings": 4}
        suggestions = self.nudger._generate_productivity_suggestions(current_context)

        assert len(suggestions) == 1
        suggestion = suggestions[0]
        assert suggestion.type == NudgeType.PRODUCTIVITY_OPTIMIZATION
        assert "Heavy meeting day" in suggestion.title
        assert "buffer time" in suggestion.description

        # Test focus time suggestion
        current_context = {"available_slots": 3}
        suggestions = self.nudger._generate_productivity_suggestions(current_context)

        assert len(suggestions) == 1
        suggestion = suggestions[0]
        assert suggestion.type == NudgeType.PRODUCTIVITY_OPTIMIZATION
        assert "Focus time available" in suggestion.title

    def test_filter_suggestions(self):
        """Test suggestion filtering."""
        # Create some test suggestions
        suggestions = [
            Nudge(
                id="test1",
                type=NudgeType.TIME_PATTERN,
                title="Test 1",
                description="Test description 1",
                priority=0.8,
                confidence=0.9,
                context={},
                created_at=datetime.now().isoformat(),
            ),
            Nudge(
                id="test2",
                type=NudgeType.HABIT_REINFORCEMENT,
                title="Test 2",
                description="Test description 2",
                priority=0.6,
                confidence=0.7,
                context={},
                created_at=datetime.now().isoformat(),
            ),
            Nudge(
                id="test3",
                type=NudgeType.PRODUCTIVITY_OPTIMIZATION,
                title="Test 3",
                description="Test description 3",
                priority=0.9,
                confidence=0.8,
                context={},
                created_at=datetime.now().isoformat(),
            ),
        ]

        current_context = {}
        filtered = self.nudger._filter_suggestions(suggestions, current_context)

        # Should return top 3 suggestions sorted by priority and confidence
        assert len(filtered) == 3
        assert filtered[0].priority == 0.9  # Highest priority first
        assert filtered[1].priority == 0.8
        assert filtered[2].priority == 0.6

    def test_learn_preferences(self):
        """Test learning from user feedback."""
        # Create a test nudge
        nudge = Nudge(
            id="test_nudge",
            type=NudgeType.TIME_PATTERN,
            title="Test Nudge",
            description="Test description",
            priority=0.8,
            confidence=0.8,
            context={},
            created_at=datetime.now().isoformat(),
        )

        self.nudger.nudges["test_nudge"] = nudge

        # Test accepting a nudge
        feedback = {
            "nudge_id": "test_nudge",
            "action": "accepted",
            "context": {"test": "data"},
        }

        self.nudger.learn_preferences(feedback)

        # Check that feedback was recorded
        assert len(self.nudger.nudge_history) == 1
        feedback_record = self.nudger.nudge_history[0]
        assert feedback_record["nudge_id"] == "test_nudge"
        assert feedback_record["action"] == "accepted"

        # Check that confidence was increased for this type
        confidence_key = f"confidence_{NudgeType.TIME_PATTERN.value}"
        assert self.nudger.user_preferences[confidence_key] > 0.8

    def test_should_nudge(self):
        """Test nudging decision logic."""
        # Clear existing nudges to start fresh
        self.nudger.nudges.clear()

        # Test with default preferences (should allow nudging)
        context = {}
        # Ensure nudging is enabled by default
        self.nudger.user_preferences["nudging_enabled"] = True

        # Mock current time to be during normal hours (not quiet hours)
        with patch("core.nudge_engine.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 20, 14, 0)  # 2pm

            result = self.nudger.should_nudge(context)
            assert result is True

        # Test with nudging disabled
        self.nudger.user_preferences["nudging_enabled"] = False
        assert self.nudger.should_nudge(context) is False

        # Reset and test quiet hours
        self.nudger.user_preferences["nudging_enabled"] = True
        with patch("core.nudge_engine.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 20, 23, 0)  # 11pm
            assert self.nudger.should_nudge(context) is False

    def test_get_stats(self):
        """Test statistics generation."""
        # Clear existing nudges to start fresh
        self.nudger.nudges.clear()
        self.nudger.nudge_history.clear()

        # Add some test nudges
        nudge1 = Nudge(
            id="test1",
            type=NudgeType.TIME_PATTERN,
            title="Test 1",
            description="Test description 1",
            priority=0.8,
            confidence=0.8,
            context={},
            created_at=datetime.now().isoformat(),
        )

        nudge2 = Nudge(
            id="test2",
            type=NudgeType.HABIT_REINFORCEMENT,
            title="Test 2",
            description="Test description 2",
            priority=0.6,
            confidence=0.7,
            context={},
            created_at=datetime.now().isoformat(),
            dismissed=True,
        )

        self.nudger.nudges["test1"] = nudge1
        self.nudger.nudges["test2"] = nudge2

        # Add some feedback
        self.nudger.nudge_history = [
            {"action": "accepted", "type": "time_pattern"},
            {"action": "dismissed", "type": "habit_reinforcement"},
            {"action": "accepted", "type": "time_pattern"},
        ]

        stats = self.nudger.get_stats()

        assert stats["total_nudges"] == 2
        assert stats["active_nudges"] == 1
        assert stats["dismissed_nudges"] == 1
        assert stats["acceptance_rate"] == 2 / 3  # 2 accepted out of 3 total
        assert "user_preferences" in stats
        assert stats["nudge_history_count"] == 3

    def test_clear_expired_nudges(self):
        """Test clearing expired nudges."""
        # Create a nudge with expiration
        expired_nudge = Nudge(
            id="expired",
            type=NudgeType.TIME_PATTERN,
            title="Expired Nudge",
            description="This nudge has expired",
            priority=0.8,
            confidence=0.8,
            context={},
            created_at=datetime.now().isoformat(),
            expires_at=(
                datetime.now() - timedelta(hours=1)
            ).isoformat(),  # Expired 1 hour ago
        )

        active_nudge = Nudge(
            id="active",
            type=NudgeType.TIME_PATTERN,
            title="Active Nudge",
            description="This nudge is still active",
            priority=0.8,
            confidence=0.8,
            context={},
            created_at=datetime.now().isoformat(),
            expires_at=(
                datetime.now() + timedelta(hours=1)
            ).isoformat(),  # Expires in 1 hour
        )

        self.nudger.nudges["expired"] = expired_nudge
        self.nudger.nudges["active"] = active_nudge

        # Clear expired nudges
        self.nudger.clear_expired_nudges()

        # Check that only expired nudge was removed
        assert "expired" not in self.nudger.nudges
        assert "active" in self.nudger.nudges

    def test_generate_suggestions_integration(self):
        """Test full suggestion generation integration."""
        # Add some past events
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

        # Add a fitness intention
        self.core_memory.add_intention("I want to exercise more", "high")

        # Mock current time
        with patch("core.nudge_engine.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 20, 9, 30)  # 9:30am

            current_context = {"back_to_back_meetings": 4, "available_slots": 3}

            suggestions = self.nudger.generate_suggestions(current_context)

            # Should generate multiple types of suggestions
            assert len(suggestions) > 0

            # Check that suggestions are properly filtered and sorted
            if suggestions:
                # Should be sorted by priority and confidence
                priorities = [s.priority for s in suggestions]
                assert priorities == sorted(priorities, reverse=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
