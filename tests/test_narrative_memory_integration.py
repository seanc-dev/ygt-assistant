"""Integration tests for narrative memory with calendar agent."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from core.narrative_memory import NarrativeMemory
from calendar_agent_eventkit import EventKitAgent


class TestNarrativeMemoryIntegration:
    """Test narrative memory integration with calendar agent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.narrative_memory = NarrativeMemory()
        # Clear any existing data
        self.narrative_memory.themes.clear()
        self.narrative_memory.patterns.clear()

    def test_narrative_memory_with_event_creation(self):
        """Test that creating events can trigger narrative memory updates."""
        # Create a theme before adding events
        theme_id = self.narrative_memory.add_theme(
            topic="Work Meetings",
            summary="Regular work meetings and team coordination",
            source_refs=[],
            tags=["work", "meetings"],
        )

        # Simulate creating events that match the theme
        events = [
            {
                "title": "Team Standup",
                "description": "Daily team coordination",
                "date": "2025-01-27",
                "time": "09:00",
                "tags": ["work", "meetings"],
            },
            {
                "title": "Project Review",
                "description": "Weekly project status review",
                "date": "2025-01-28",
                "time": "14:00",
                "tags": ["work", "meetings"],
            },
        ]

        # Analyze themes from these events
        themes = self.narrative_memory.analyze_themes_from_events(events)
        assert len(themes) > 0

        # Should find work-related themes
        work_themes = self.narrative_memory.search_themes(content="work")
        assert len(work_themes) >= 1

    def test_narrative_memory_pattern_detection(self):
        """Test that narrative memory can detect patterns from calendar events."""
        # Create recurring events
        events = [
            {
                "title": "Morning Standup",
                "date": "2025-01-20",
                "time": "09:00",
            },
            {
                "title": "Morning Standup",
                "date": "2025-01-21",
                "time": "09:00",
            },
            {
                "title": "Morning Standup",
                "date": "2025-01-22",
                "time": "09:00",
            },
            {
                "title": "Weekly Review",
                "date": "2025-01-20",
                "time": "17:00",
            },
            {
                "title": "Weekly Review",
                "date": "2025-01-27",
                "time": "17:00",
            },
        ]

        # Analyze patterns from events
        patterns = self.narrative_memory.analyze_patterns_from_events(events)
        assert len(patterns) > 0

        # Add the detected patterns to narrative memory
        for pattern in patterns:
            self.narrative_memory.add_pattern(
                pattern=pattern.pattern,
                datetime_str=pattern.datetime,
                recurrence=pattern.recurrence,
                confidence=pattern.confidence,
                context=pattern.context,
            )

        # Should detect daily standup pattern
        standup_patterns = self.narrative_memory.search_patterns(pattern="standup")
        assert len(standup_patterns) > 0

        # Should detect weekly review pattern
        review_patterns = self.narrative_memory.search_patterns(pattern="review")
        assert len(review_patterns) > 0

    def test_narrative_memory_theme_evolution(self):
        """Test that themes can evolve as new data is added."""
        # Initial theme
        theme_id = self.narrative_memory.add_theme(
            topic="Travel Planning",
            summary="User occasionally plans trips",
            source_refs=["event_1"],
            confidence=0.5,
        )

        # Add more travel-related events
        travel_events = [
            {
                "title": "Italy Research",
                "description": "Looking up Tuscany hotels",
                "date": "2025-01-15",
                "tags": ["travel", "italy"],
            },
            {
                "title": "Flight Booking",
                "description": "Book flights to Florence",
                "date": "2025-01-16",
                "tags": ["travel", "italy"],
            },
            {
                "title": "Cooking Class",
                "description": "Research cooking schools in Tuscany",
                "date": "2025-01-17",
                "tags": ["travel", "cooking"],
            },
        ]

        # Analyze themes from new events
        new_themes = self.narrative_memory.analyze_themes_from_events(travel_events)

        # Should find travel-related themes
        travel_themes = [
            t
            for t in new_themes
            if "travel" in t.topic.lower() or "italy" in t.summary.lower()
        ]
        assert len(travel_themes) > 0

        # Update existing theme with new information
        self.narrative_memory.update_theme(
            theme_id,
            summary="User is planning a detailed Italy trip with cooking classes",
            confidence=0.8,
            source_refs=["event_1", "event_2", "event_3"],
        )

        updated_theme = self.narrative_memory.get_theme(theme_id)
        assert "cooking classes" in updated_theme.summary
        assert updated_theme.confidence == 0.8

    def test_narrative_memory_context_awareness(self):
        """Test that narrative memory provides context-aware information."""
        # Create themes for different life areas
        self.narrative_memory.add_theme(
            topic="Health & Fitness",
            summary="Regular gym sessions and healthy eating",
            source_refs=["event_1", "event_2"],
            tags=["health", "fitness"],
        )

        self.narrative_memory.add_theme(
            topic="Work Projects",
            summary="Focus on AI and automation projects",
            source_refs=["event_3", "event_4"],
            tags=["work", "ai"],
        )

        self.narrative_memory.add_theme(
            topic="Social Life",
            summary="Regular meetups with friends and family",
            source_refs=["event_5", "event_6"],
            tags=["social", "family"],
        )

        # Test context-aware theme retrieval
        health_themes = self.narrative_memory.search_themes(content="gym")
        assert len(health_themes) == 1
        assert "Health" in health_themes[0].topic

        work_themes = self.narrative_memory.search_themes(content="automation")
        assert len(work_themes) == 1
        assert "Work" in work_themes[0].topic

        social_themes = self.narrative_memory.search_themes(content="friends")
        assert len(social_themes) == 1
        assert "Social" in social_themes[0].topic

    def test_narrative_memory_persistence_integration(self):
        """Test that narrative memory persists data correctly in integration."""
        # Add themes and patterns
        theme_id = self.narrative_memory.add_theme(
            topic="Test Theme",
            summary="Test summary for integration",
            source_refs=["test_ref"],
        )

        pattern_id = self.narrative_memory.add_pattern(
            pattern="Test Pattern",
            datetime_str="test time",
            recurrence="daily",
        )

        # Save data
        self.narrative_memory.save()

        # Create new instance to test loading
        new_narrative_memory = NarrativeMemory()

        # Verify data was loaded
        theme = new_narrative_memory.get_theme(theme_id)
        pattern = new_narrative_memory.get_pattern(pattern_id)

        assert theme is not None
        assert theme.topic == "Test Theme"
        assert pattern is not None
        assert pattern.pattern == "Test Pattern"

    def test_narrative_memory_stats_integration(self):
        """Test narrative memory statistics in integration context."""
        # Add various types of data
        self.narrative_memory.add_theme(
            topic="High Confidence Theme",
            summary="High confidence theme",
            confidence=0.9,
        )

        self.narrative_memory.add_theme(
            topic="Medium Confidence Theme",
            summary="Medium confidence theme",
            confidence=0.6,
        )

        self.narrative_memory.add_pattern(
            pattern="Daily Pattern",
            datetime_str="9:00am",
            recurrence="daily",
        )

        self.narrative_memory.add_pattern(
            pattern="Weekly Pattern",
            datetime_str="5:00pm",
            recurrence="weekly",
        )

        # Get statistics
        stats = self.narrative_memory.get_stats()

        assert stats["total_themes"] == 2
        assert stats["total_patterns"] == 2
        assert stats["themes_by_confidence"]["high"] == 1
        assert stats["themes_by_confidence"]["medium"] == 1
        assert stats["patterns_by_recurrence"]["daily"] == 1
        assert stats["patterns_by_recurrence"]["weekly"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
