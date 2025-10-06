"""Tests for the Core memory manager functionality."""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from core.memory_manager import (
    CoreMemory,
    MemoryType,
    PastEvent,
    Intention,
    Commitment,
    Preference,
)


class TestCoreMemory:
    """Test the Core memory manager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_memory.db")

        # Create Core memory instance
        self.core_memory = CoreMemory(self.test_db_path)

    def teardown_method(self):
        """Clean up test fixtures."""
        # Remove temporary directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test Core memory initialization."""
        assert self.core_memory.memory_db_path == self.test_db_path
        assert isinstance(self.core_memory.memories, dict)
        assert len(self.core_memory.memories) == 0

    def test_add_past_event(self):
        """Test adding a past event to memory."""
        event_data = {
            "title": "Team Meeting",
            "description": "Weekly team sync",
            "start_date": "2024-01-15",
            "duration": 60,
            "attendees": ["Alice", "Bob"],
            "location": "Conference Room A",
            "is_recurring": True,
            "recurrence_pattern": "FREQ=WEEKLY",
            "text_for_embedding": "Team Meeting | Weekly team sync | Location: Conference Room A",
        }

        memory_id = self.core_memory.add_past_event(event_data)

        assert memory_id.startswith("past_event_")
        assert memory_id in self.core_memory.memories

        memory = self.core_memory.memories[memory_id]
        assert isinstance(memory, PastEvent)
        assert memory.title == "Team Meeting"
        assert memory.description == "Weekly team sync"
        assert memory.duration == 60
        assert memory.attendees == ["Alice", "Bob"]
        assert memory.location == "Conference Room A"
        assert memory.is_recurring is True
        assert memory.recurrence_pattern == "FREQ=WEEKLY"

    def test_add_intention(self):
        """Test adding an intention to memory."""
        memory_id = self.core_memory.add_intention(
            content="I want to get fitter",
            priority="high",
            related_events=["gym_sessions"],
        )

        assert memory_id.startswith("intention_")
        assert memory_id in self.core_memory.memories

        memory = self.core_memory.memories[memory_id]
        assert isinstance(memory, Intention)
        assert memory.content == "I want to get fitter"
        assert memory.priority == "high"
        assert memory.related_events == ["gym_sessions"]
        assert memory.progress_tracking is True

    def test_add_commitment(self):
        """Test adding a commitment to memory."""
        memory_id = self.core_memory.add_commitment(
            content="follow up with Anna about project status",
            due_date="2024-01-20",
            priority="medium",
        )

        assert memory_id.startswith("commitment_")
        assert memory_id in self.core_memory.memories

        memory = self.core_memory.memories[memory_id]
        assert isinstance(memory, Commitment)
        assert memory.content == "follow up with Anna about project status"
        assert memory.due_date == "2024-01-20"
        assert memory.priority == "medium"
        assert memory.status == "pending"

    def test_add_preference(self):
        """Test adding a preference to memory."""
        memory_id = self.core_memory.add_preference(
            content="no meetings before 11am",
            category="scheduling",
            strength=0.9,
            context="work_schedule",
        )

        assert memory_id.startswith("preference_")
        assert memory_id in self.core_memory.memories

        memory = self.core_memory.memories[memory_id]
        assert isinstance(memory, Preference)
        assert memory.content == "no meetings before 11am"
        assert memory.category == "scheduling"
        assert memory.strength == 0.9
        assert memory.context == "work_schedule"

    def test_get_memory(self):
        """Test getting a specific memory by ID."""
        # Add a memory
        memory_id = self.core_memory.add_intention("test intention", "medium")

        # Get the memory
        memory = self.core_memory.get_memory(memory_id)

        assert memory is not None
        assert isinstance(memory, Intention)
        assert memory.content == "test intention"

    def test_get_memory_not_found(self):
        """Test getting a memory that doesn't exist."""
        memory = self.core_memory.get_memory("nonexistent_id")
        assert memory is None

    def test_get_memories_by_type(self):
        """Test getting memories by type."""
        # Add different types of memories
        self.core_memory.add_intention("intention 1", "high")
        self.core_memory.add_intention("intention 2", "medium")
        self.core_memory.add_commitment("commitment 1", "2024-01-20", "high")

        # Get intentions
        intentions = self.core_memory.get_memories_by_type(MemoryType.INTENTION)
        assert len(intentions) == 2
        assert all(isinstance(memory, Intention) for memory in intentions)

        # Get commitments
        commitments = self.core_memory.get_memories_by_type(MemoryType.COMMITMENT)
        assert len(commitments) == 1
        assert all(isinstance(memory, Commitment) for memory in commitments)

    def test_delete_memory(self):
        """Test deleting a memory."""
        # Add a memory
        memory_id = self.core_memory.add_intention("test intention", "medium")

        # Verify it exists
        assert memory_id in self.core_memory.memories

        # Delete it
        result = self.core_memory.delete_memory(memory_id)
        assert result is True

        # Verify it's gone
        assert memory_id not in self.core_memory.memories

    def test_delete_memory_not_found(self):
        """Test deleting a memory that doesn't exist."""
        result = self.core_memory.delete_memory("nonexistent_id")
        assert result is False

    def test_get_patterns(self):
        """Test getting patterns from past events."""
        # Add some past events
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
            "title": "Team Standup",
            "description": "Daily standup",
            "start_date": "2024-01-16T09:00:00",
            "duration": 30,
            "attendees": ["Alice", "Bob", "Charlie"],
            "location": "Conference Room B",
            "is_recurring": True,
            "recurrence_pattern": "FREQ=DAILY",
            "text_for_embedding": "Team Standup",
        }

        self.core_memory.add_past_event(event_data_1)
        self.core_memory.add_past_event(event_data_2)

        # Get patterns for team events
        patterns = self.core_memory.get_patterns("team")

        assert patterns["total_events"] == 2
        assert patterns["average_duration"] == 45  # (60 + 30) / 2
        assert "common_times" in patterns
        assert "common_locations" in patterns
        assert "common_attendees" in patterns
        assert "recurring_patterns" in patterns

    def test_get_patterns_no_events(self):
        """Test getting patterns when no events exist."""
        patterns = self.core_memory.get_patterns("nonexistent")
        assert patterns == {}

    def test_suggest_similar(self):
        """Test suggesting similar events."""
        # Mock the embedding manager to return similar events
        mock_similar_events = [
            {
                "metadata": {
                    "type": "past_event",
                    "title": "Team Meeting",
                    "duration": 60,
                    "location": "Conference Room A",
                    "attendees": ["Alice", "Bob"],
                },
                "similarity": 0.85,
            }
        ]

        with patch.object(
            self.core_memory.embedding_manager,
            "search_similar",
            return_value=mock_similar_events,
        ):
            suggestions = self.core_memory.suggest_similar("team meeting")

            assert "suggestions" in suggestions
            assert len(suggestions["suggestions"]) == 1
            assert suggestions["total_found"] == 1

            suggestion = suggestions["suggestions"][0]
            assert suggestion["title"] == "Team Meeting"
            assert suggestion["duration"] == 60
            assert suggestion["location"] == "Conference Room A"
            assert suggestion["attendees"] == ["Alice", "Bob"]
            assert suggestion["similarity"] == 0.85

    def test_suggest_similar_no_results(self):
        """Test suggesting similar events when no results found."""
        with patch.object(
            self.core_memory.embedding_manager, "search_similar", return_value=[]
        ):
            suggestions = self.core_memory.suggest_similar("nonexistent event")
            assert suggestions == {}

    def test_recall(self):
        """Test the recall function."""
        # Mock the embedding manager
        mock_similar_events = [
            {"metadata": {"type": "past_event", "title": "Team Meeting"}}
        ]

        with patch.object(
            self.core_memory.embedding_manager,
            "search_similar",
            return_value=mock_similar_events,
        ):
            results = self.core_memory.recall("team meeting")

            assert len(results) == 1
            assert results[0]["metadata"]["title"] == "Team Meeting"

    def test_recall_filters_non_past_events(self):
        """Test that recall filters out non-past events."""
        # Mock the embedding manager to return mixed results
        mock_similar_events = [
            {"metadata": {"type": "past_event", "title": "Team Meeting"}},
            {"metadata": {"type": "intention", "content": "I want to exercise more"}},
        ]

        with patch.object(
            self.core_memory.embedding_manager,
            "search_similar",
            return_value=mock_similar_events,
        ):
            results = self.core_memory.recall("team meeting")

            # Should only return past events
            assert len(results) == 1
            assert results[0]["metadata"]["type"] == "past_event"

    def test_get_stats(self):
        """Test getting statistics."""
        # Add some memories
        self.core_memory.add_intention("intention 1", "high")
        self.core_memory.add_commitment("commitment 1", "2024-01-20", "medium")
        self.core_memory.add_preference("preference 1", "scheduling", 0.8)

        stats = self.core_memory.get_stats()

        assert stats["total_memories"] == 3
        assert "memory_types" in stats
        assert "embedding_stats" in stats

        memory_types = stats["memory_types"]
        assert memory_types["intention"] == 1
        assert memory_types["commitment"] == 1
        assert memory_types["preference"] == 1

    def test_clear_all_memories(self):
        """Test clearing all memories."""
        # Add some memories
        self.core_memory.add_intention("intention 1", "high")
        self.core_memory.add_commitment("commitment 1", "2024-01-20", "medium")

        # Verify they exist
        assert len(self.core_memory.memories) == 2

        # Clear all memories
        self.core_memory.clear_all_memories()

        # Verify they're gone
        assert len(self.core_memory.memories) == 0

    def test_persistence(self):
        """Test that memories persist between instances."""
        # Add a memory
        memory_id = self.core_memory.add_intention("test intention", "high")

        # Create a new instance (should load existing memories)
        new_core_memory = CoreMemory(self.test_db_path)

        # Verify the memory was loaded
        assert memory_id in new_core_memory.memories
        memory = new_core_memory.get_memory(memory_id)
        assert memory.content == "test intention"

    def test_analyze_timing_patterns(self):
        """Test timing pattern analysis."""
        # Create some past events with different times
        events = [
            PastEvent(
                id="1",
                type=MemoryType.PAST_EVENT,
                content="",
                created_date="",
                metadata={},
                title="Event 1",
                description="",
                date="2024-01-15T10:00:00",
                duration=60,
                attendees=[],
                location="",
                is_recurring=False,
                recurrence_pattern="",
            ),
            PastEvent(
                id="2",
                type=MemoryType.PAST_EVENT,
                content="",
                created_date="",
                metadata={},
                title="Event 2",
                description="",
                date="2024-01-15T14:00:00",
                duration=60,
                attendees=[],
                location="",
                is_recurring=False,
                recurrence_pattern="",
            ),
            PastEvent(
                id="3",
                type=MemoryType.PAST_EVENT,
                content="",
                created_date="",
                metadata={},
                title="Event 3",
                description="",
                date="2024-01-15T10:00:00",
                duration=60,
                attendees=[],
                location="",
                is_recurring=False,
                recurrence_pattern="",
            ),
        ]

        patterns = self.core_memory._analyze_timing_patterns(events)

        assert "most_common_hours" in patterns
        assert "average_hour" in patterns
        assert 10 in patterns["most_common_hours"]  # Most common hour
        assert (
            abs(patterns["average_hour"] - 11.33) < 0.01
        )  # (10 + 14 + 10) / 3 ≈ 11.33


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
