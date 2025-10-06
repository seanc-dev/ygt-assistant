"""Integration tests for narrative memory with calendar agent."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from calendar_agent_eventkit import EventKitAgent


class TestNarrativeMemoryCalendarIntegration:
    """Test narrative memory integration with calendar agent."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("calendar_agent_eventkit.EKEventStore") as mock_store:
            mock_store_instance = MagicMock()
            mock_store.return_value = mock_store_instance
            self.agent = EventKitAgent()

    def test_narrative_memory_initialization(self):
        """Test that narrative memory is properly initialized."""
        assert hasattr(self.agent, "narrative_memory")
        # Should be available since we have the module
        assert self.agent.narrative_memory is not None

    def test_create_event_with_narrative_memory(self):
        """Test that creating events updates narrative memory."""
        # Create multiple events with work-related descriptions to trigger theme creation
        events = [
            {
                "title": "Team Standup",
                "description": "Daily team coordination meeting",
                "date": "2025-01-27",
                "time": "09:00",
                "duration": 30,
                "location": "Conference Room A",
            },
            {
                "title": "Project Review",
                "description": "Weekly project status review",
                "date": "2025-01-28",
                "time": "14:00",
                "duration": 60,
                "location": "Conference Room B",
            },
        ]

        for event in events:
            result = self.agent.create_event(event)
            assert result["success"] is True

        # Check that narrative memory was updated
        insights = self.agent.get_narrative_insights()
        assert "themes" in insights
        assert "patterns" in insights
        assert "insights" in insights

        # Should have detected work theme
        work_themes = [t for t in insights["themes"] if "work" in t["topic"].lower()]
        assert len(work_themes) > 0

    def test_create_recurring_event_with_pattern_detection(self):
        """Test that recurring events create patterns in narrative memory."""
        # Create multiple recurring events to trigger pattern detection
        events = [
            {
                "title": "Daily Workout",
                "description": "Daily fitness routine",
                "date": "2025-01-27",
                "time": "07:00",
                "duration": 60,
                "recurrence_rule": "daily",
            },
            {
                "title": "Daily Workout",
                "description": "Evening fitness routine",
                "date": "2025-01-28",
                "time": "18:00",
                "duration": 45,
                "recurrence_rule": "daily",
            },
        ]

        for event in events:
            result = self.agent.create_event(event)
            assert result["success"] is True

        # Check that patterns were detected
        insights = self.agent.get_narrative_insights()
        patterns = insights["patterns"]

        # Should have detected the recurring pattern
        workout_patterns = [p for p in patterns if "workout" in p["pattern"].lower()]
        assert len(workout_patterns) > 0

    def test_narrative_theme_search(self):
        """Test searching narrative themes."""
        # Create events with different themes
        events = [
            {
                "title": "Gym Session",
                "description": "Cardio workout",
                "date": "2025-01-27",
                "time": "18:00",
                "duration": 45,
            },
            {
                "title": "Project Review",
                "description": "Weekly project status review",
                "date": "2025-01-28",
                "time": "14:00",
                "duration": 60,
            },
        ]

        for event in events:
            self.agent.create_event(event)

        # Search for health-related themes
        health_themes = self.agent.search_narrative_themes("gym")
        assert len(health_themes) > 0

        # Search for work-related themes
        work_themes = self.agent.search_narrative_themes("project")
        assert len(work_themes) > 0

    def test_narrative_stats(self):
        """Test getting narrative memory statistics."""
        # Create some events
        events = [
            {
                "title": "Daily Standup",
                "description": "Team coordination",
                "date": "2025-01-27",
                "time": "09:00",
                "duration": 15,
            },
            {
                "title": "Weekly Review",
                "description": "Project review meeting",
                "date": "2025-01-28",
                "time": "16:00",
                "duration": 60,
            },
        ]

        for event in events:
            self.agent.create_event(event)

        # Get statistics
        stats = self.agent.get_narrative_stats()
        assert "narrative_memory_available" in stats
        assert stats["narrative_memory_available"] is True
        assert "total_themes" in stats
        assert "total_patterns" in stats

    def test_narrative_insights_generation(self):
        """Test that narrative insights are generated correctly."""
        # Create events with high confidence themes
        events = [
            {
                "title": "Team Meeting",
                "description": "Weekly team coordination",
                "date": "2025-01-27",
                "time": "10:00",
                "duration": 60,
            },
            {
                "title": "Project Planning",
                "description": "Strategic planning session",
                "date": "2025-01-28",
                "time": "14:00",
                "duration": 90,
            },
            {
                "title": "Code Review",
                "description": "Technical code review",
                "date": "2025-01-29",
                "time": "15:00",
                "duration": 45,
            },
        ]

        for event in events:
            self.agent.create_event(event)

        # Get insights
        insights = self.agent.get_narrative_insights()
        assert "insights" in insights

        # Should have generated insights about work patterns
        work_insights = [
            i for i in insights["insights"] if "work" in i["content"].lower()
        ]
        assert len(work_insights) > 0

    def test_narrative_memory_persistence(self):
        """Test that narrative memory persists across agent instances."""
        # Create an event
        event_details = {
            "title": "Test Event",
            "description": "Test event for persistence",
            "date": "2025-01-27",
            "time": "12:00",
            "duration": 30,
        }

        self.agent.create_event(event_details)

        # Get initial stats
        initial_stats = self.agent.get_narrative_stats()
        initial_theme_count = initial_stats.get("total_themes", 0)

        # Create new agent instance (should load existing narrative data)
        with patch("calendar_agent_eventkit.EKEventStore") as mock_store:
            mock_store_instance = MagicMock()
            mock_store.return_value = mock_store_instance
            new_agent = EventKitAgent()

        # Check that narrative memory was loaded
        new_stats = new_agent.get_narrative_stats()
        new_theme_count = new_stats.get("total_themes", 0)

        # Should have the same number of themes (or more if new ones were created)
        assert new_theme_count >= initial_theme_count

    def test_narrative_memory_error_handling(self):
        """Test that narrative memory errors don't break the agent."""
        # Mock narrative memory to raise an exception
        with patch.object(self.agent, "narrative_memory") as mock_narrative:
            mock_narrative.analyze_themes_from_events.side_effect = Exception(
                "Test error"
            )

            # Create an event - should not fail
            event_details = {
                "title": "Test Event",
                "description": "Test event with error",
                "date": "2025-01-27",
                "time": "12:00",
                "duration": 30,
            }

            result = self.agent.create_event(event_details)
            assert result["success"] is True

    def test_narrative_memory_tag_extraction(self):
        """Test that tags are properly extracted from event descriptions."""
        # Create events with different types of descriptions
        events = [
            {
                "title": "Work Meeting",
                "description": "Team project planning meeting",
                "date": "2025-01-27",
                "time": "10:00",
                "duration": 60,
            },
            {
                "title": "Gym Session",
                "description": "Cardio and strength training workout",
                "date": "2025-01-27",
                "time": "18:00",
                "duration": 45,
            },
            {
                "title": "Coffee with Friends",
                "description": "Social coffee meetup",
                "date": "2025-01-28",
                "time": "15:00",
                "duration": 60,
            },
        ]

        for event in events:
            self.agent.create_event(event)

        # Check that appropriate themes were created
        insights = self.agent.get_narrative_insights()
        themes = insights["themes"]

        # Should have work, health, and social themes
        work_themes = [t for t in themes if "work" in t["topic"].lower()]
        health_themes = [t for t in themes if "health" in t["topic"].lower()]
        social_themes = [t for t in themes if "social" in t["topic"].lower()]

        assert len(work_themes) > 0
        assert len(health_themes) > 0
        assert len(social_themes) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
