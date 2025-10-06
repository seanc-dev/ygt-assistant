"""Tests for the narrative memory layer."""

import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any

from core.narrative_memory import (
    ThemeEntry,
    DynamicPattern,
    NarrativeMemory,
    NarrativeType,
)


class TestThemeEntry:
    """Test ThemeEntry data structure."""

    def test_theme_entry_creation(self):
        """Test creating a theme entry with all required fields."""
        theme = ThemeEntry(
            topic="Italy Trip",
            summary="User wants a quiet Tuscany stay, avoiding big cities. Interested in cooking school.",
            last_updated="2025-01-27",
            source_refs=["msg_1422", "event_2391"],
        )

        assert theme.topic == "Italy Trip"
        assert "Tuscany" in theme.summary
        assert theme.last_updated == "2025-01-27"
        assert len(theme.source_refs) == 2
        assert "msg_1422" in theme.source_refs

    def test_theme_entry_optional_fields(self):
        """Test creating a theme entry with optional fields."""
        theme = ThemeEntry(
            topic="Fitness",
            summary="Regular gym sessions",
            last_updated="2025-01-27",
            source_refs=[],
            confidence=0.8,
            tags=["health", "routine"],
        )

        assert theme.confidence == 0.8
        assert "health" in theme.tags
        assert len(theme.tags) == 2

    def test_theme_entry_serialization(self):
        """Test JSON serialization of theme entry."""
        theme = ThemeEntry(
            topic="Work Projects",
            summary="Focus on AI and automation",
            last_updated="2025-01-27",
            source_refs=["event_123", "msg_456"],
            confidence=0.9,
            tags=["work", "ai"],
        )

        data = theme.to_dict()
        assert data["topic"] == "Work Projects"
        assert data["confidence"] == 0.9
        assert "work" in data["tags"]

        # Test deserialization
        theme_from_dict = ThemeEntry.from_dict(data)
        assert theme_from_dict.topic == theme.topic
        assert theme_from_dict.confidence == theme.confidence


class TestDynamicPattern:
    """Test DynamicPattern data structure."""

    def test_dynamic_pattern_creation(self):
        """Test creating a dynamic pattern with all required fields."""
        pattern = DynamicPattern(
            pattern="Check-ins with B",
            datetime="Tuesdays at 7pm",
            recurrence="weekly",
            last_seen="2025-01-23",
        )

        assert pattern.pattern == "Check-ins with B"
        assert pattern.datetime == "Tuesdays at 7pm"
        assert pattern.recurrence == "weekly"
        assert pattern.last_seen == "2025-01-23"

    def test_dynamic_pattern_optional_fields(self):
        """Test creating a dynamic pattern with optional fields."""
        pattern = DynamicPattern(
            pattern="Morning workout",
            datetime="6:30am",
            recurrence="daily",
            last_seen="2025-01-27",
            confidence=0.7,
            context="weekdays",
        )

        assert pattern.confidence == 0.7
        assert pattern.context == "weekdays"

    def test_dynamic_pattern_serialization(self):
        """Test JSON serialization of dynamic pattern."""
        pattern = DynamicPattern(
            pattern="Team standup",
            datetime="9:00am",
            recurrence="daily",
            last_seen="2025-01-27",
            confidence=0.8,
            context="work",
        )

        data = pattern.to_dict()
        assert data["pattern"] == "Team standup"
        assert data["confidence"] == 0.8
        assert data["context"] == "work"

        # Test deserialization
        pattern_from_dict = DynamicPattern.from_dict(data)
        assert pattern_from_dict.pattern == pattern.pattern
        assert pattern_from_dict.confidence == pattern.confidence


class TestNarrativeMemory:
    """Test NarrativeMemory manager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.narrative_memory = NarrativeMemory()
        # Clear any existing data to ensure clean test state
        self.narrative_memory.themes.clear()
        self.narrative_memory.patterns.clear()

    def test_narrative_memory_initialization(self):
        """Test NarrativeMemory initialization."""
        assert self.narrative_memory.themes == {}
        assert self.narrative_memory.patterns == {}
        assert self.narrative_memory.storage_path is not None

    def test_add_theme(self):
        """Test adding a theme to narrative memory."""
        theme_id = self.narrative_memory.add_theme(
            topic="Travel Planning",
            summary="User frequently plans international trips",
            source_refs=["event_123", "msg_456"],
        )

        assert theme_id in self.narrative_memory.themes
        theme = self.narrative_memory.themes[theme_id]
        assert theme.topic == "Travel Planning"
        assert "international trips" in theme.summary

    def test_add_pattern(self):
        """Test adding a pattern to narrative memory."""
        pattern_id = self.narrative_memory.add_pattern(
            pattern="Weekly review",
            datetime_str="Fridays at 5pm",
            recurrence="weekly",
        )

        assert pattern_id in self.narrative_memory.patterns
        pattern = self.narrative_memory.patterns[pattern_id]
        assert pattern.pattern == "Weekly review"
        assert pattern.recurrence == "weekly"

    def test_get_theme(self):
        """Test retrieving a theme by ID."""
        theme_id = self.narrative_memory.add_theme(
            topic="Health Goals",
            summary="Focus on fitness and nutrition",
            source_refs=["event_789"],
        )

        theme = self.narrative_memory.get_theme(theme_id)
        assert theme is not None
        assert theme.topic == "Health Goals"

    def test_get_pattern(self):
        """Test retrieving a pattern by ID."""
        pattern_id = self.narrative_memory.add_pattern(
            pattern="Evening walk",
            datetime_str="7:00pm",
            recurrence="daily",
        )

        pattern = self.narrative_memory.get_pattern(pattern_id)
        assert pattern is not None
        assert pattern.pattern == "Evening walk"

    def test_update_theme(self):
        """Test updating an existing theme."""
        theme_id = self.narrative_memory.add_theme(
            topic="Work Projects",
            summary="Initial summary",
            source_refs=["event_1"],
        )

        self.narrative_memory.update_theme(
            theme_id,
            summary="Updated summary with more details",
            source_refs=["event_1", "event_2"],
        )

        theme = self.narrative_memory.get_theme(theme_id)
        assert "Updated summary" in theme.summary
        assert len(theme.source_refs) == 2

    def test_update_pattern(self):
        """Test updating an existing pattern."""
        pattern_id = self.narrative_memory.add_pattern(
            pattern="Morning routine",
            datetime_str="7:00am",
            recurrence="daily",
        )

        self.narrative_memory.update_pattern(
            pattern_id,
            datetime="6:30am",
            confidence=0.9,
        )

        pattern = self.narrative_memory.get_pattern(pattern_id)
        assert pattern.datetime == "6:30am"
        assert pattern.confidence == 0.9

    def test_delete_theme(self):
        """Test deleting a theme."""
        theme_id = self.narrative_memory.add_theme(
            topic="Test Theme",
            summary="Test summary",
            source_refs=[],
        )

        assert theme_id in self.narrative_memory.themes
        self.narrative_memory.delete_theme(theme_id)
        assert theme_id not in self.narrative_memory.themes

    def test_delete_pattern(self):
        """Test deleting a pattern."""
        pattern_id = self.narrative_memory.add_pattern(
            pattern="Test Pattern",
            datetime_str="test time",
            recurrence="daily",
        )

        assert pattern_id in self.narrative_memory.patterns
        self.narrative_memory.delete_pattern(pattern_id)
        assert pattern_id not in self.narrative_memory.patterns

    def test_search_themes(self):
        """Test searching themes by various criteria."""
        # Add multiple themes
        self.narrative_memory.add_theme(
            topic="Travel Planning",
            summary="International trips and local adventures",
            source_refs=["event_1"],
        )
        self.narrative_memory.add_theme(
            topic="Work Projects",
            summary="AI and automation focus",
            source_refs=["event_2"],
        )
        self.narrative_memory.add_theme(
            topic="Health Goals",
            summary="Fitness and nutrition focus",
            source_refs=["event_3"],
        )

        # Search by topic
        travel_themes = self.narrative_memory.search_themes(topic="Travel")
        assert len(travel_themes) == 1
        assert "Travel" in travel_themes[0].topic

        # Search by content
        health_themes = self.narrative_memory.search_themes(content="fitness")
        assert len(health_themes) == 1
        assert "Health" in health_themes[0].topic

    def test_search_patterns(self):
        """Test searching patterns by various criteria."""
        # Add multiple patterns
        self.narrative_memory.add_pattern(
            pattern="Morning routine",
            datetime_str="7:00am",
            recurrence="daily",
        )
        self.narrative_memory.add_pattern(
            pattern="Weekly review",
            datetime_str="5:00pm",
            recurrence="weekly",
        )
        self.narrative_memory.add_pattern(
            pattern="Evening walk",
            datetime_str="7:00pm",
            recurrence="daily",
        )

        # Search by pattern name
        routine_patterns = self.narrative_memory.search_patterns(pattern="routine")
        assert len(routine_patterns) == 1
        assert "routine" in routine_patterns[0].pattern

        # Search by recurrence
        daily_patterns = self.narrative_memory.search_patterns(recurrence="daily")
        assert len(daily_patterns) == 2

    def test_persistence(self):
        """Test saving and loading narrative data."""
        # Add some data
        theme_id = self.narrative_memory.add_theme(
            topic="Test Theme",
            summary="Test summary",
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

    def test_analyze_themes_from_events(self):
        """Test extracting themes from past events."""
        events = [
            {
                "title": "Italy Planning Meeting",
                "description": "Discuss Tuscany itinerary",
                "date": "2025-01-15",
                "tags": ["travel", "italy"],
            },
            {
                "title": "Cooking Class Research",
                "description": "Look up cooking schools in Tuscany",
                "date": "2025-01-16",
                "tags": ["travel", "cooking"],
            },
            {
                "title": "Flight Booking",
                "description": "Book flights to Florence",
                "date": "2025-01-17",
                "tags": ["travel", "italy"],
            },
        ]

        themes = self.narrative_memory.analyze_themes_from_events(events)
        assert len(themes) > 0

        # Should identify Italy trip theme
        italy_theme = next(
            (
                t
                for t in themes
                if "italy" in t.topic.lower() or "tuscany" in t.summary.lower()
            ),
            None,
        )
        assert italy_theme is not None

    def test_analyze_patterns_from_events(self):
        """Test extracting patterns from past events."""
        events = [
            {
                "title": "Team Standup",
                "date": "2025-01-20",
                "time": "09:00",
            },
            {
                "title": "Team Standup",
                "date": "2025-01-21",
                "time": "09:00",
            },
            {
                "title": "Team Standup",
                "date": "2025-01-22",
                "time": "09:00",
            },
        ]

        patterns = self.narrative_memory.analyze_patterns_from_events(events)
        assert len(patterns) > 0

        # Should identify daily standup pattern
        standup_pattern = next(
            (p for p in patterns if "standup" in p.pattern.lower()), None
        )
        assert standup_pattern is not None
        assert standup_pattern.recurrence == "daily"

    def test_get_stats(self):
        """Test getting narrative memory statistics."""
        # Add some data
        self.narrative_memory.add_theme(
            topic="Theme 1",
            summary="Summary 1",
            source_refs=[],
        )
        self.narrative_memory.add_theme(
            topic="Theme 2",
            summary="Summary 2",
            source_refs=[],
        )
        self.narrative_memory.add_pattern(
            pattern="Pattern 1",
            datetime_str="9:00am",
            recurrence="daily",
        )

        stats = self.narrative_memory.get_stats()
        assert stats["total_themes"] == 2
        assert stats["total_patterns"] == 1
        assert "storage_path" in stats

    def test_integration_with_core_memory(self):
        """Test integration with CoreMemory system."""
        # Mock CoreMemory
        with patch("core.memory_manager.CoreMemory") as mock_core_memory:
            mock_core = mock_core_memory.return_value
            mock_core.get_memories_by_type.return_value = [
                MagicMock(
                    id="event_1",
                    content="Team meeting",
                    metadata={"tags": ["work", "team"]},
                ),
                MagicMock(
                    id="event_2",
                    content="Team standup",
                    metadata={"tags": ["work", "team"]},
                ),
                MagicMock(
                    id="event_3",
                    content="Gym session",
                    metadata={"tags": ["health", "fitness"]},
                ),
                MagicMock(
                    id="event_4",
                    content="Workout",
                    metadata={"tags": ["health", "fitness"]},
                ),
            ]

            # Test theme extraction from core memory
            themes = self.narrative_memory.extract_themes_from_core_memory(mock_core)
            assert len(themes) > 0

            # Verify core memory was queried
            mock_core.get_memories_by_type.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
