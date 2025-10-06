"""Integration tests for Core memory system with calendar operations."""

import pytest
import tempfile
import os
from unittest.mock import patch, Mock
from datetime import datetime

from core.memory_manager import CoreMemory, MemoryType
from calendar_agent_eventkit import EventKitAgent


class TestCoreIntegration:
    """Test Core memory integration with calendar operations."""

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

    def teardown_method(self):
        """Clean up test fixtures."""
        # Remove temporary directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_event_with_core_memory(self):
        """Test that creating an event adds it to Core memory."""
        # Mock the store to return success
        with patch.object(self.agent.store, "saveEvent_span_error_", return_value=True):
            # Create an event
            details = {
                "title": "Team Meeting",
                "date": "2024-01-15",
                "time": "14:00",
                "duration": 60,
                "location": "Conference Room A",
                "description": "Weekly team sync",
            }

            result = self.agent.create_event(details)

            assert result["success"] is True

            # Check that the event was added to Core memory
            past_events = self.core_memory.get_memories_by_type(MemoryType.PAST_EVENT)
            assert len(past_events) == 1

            event = past_events[0]
            assert event.title == "Team Meeting"
            assert event.location == "Conference Room A"
            assert event.duration == 60

    def test_delete_event_with_core_memory(self):
        """Test that deleting an event removes it from Core memory."""
        # First create an event
        with patch.object(self.agent.store, "saveEvent_span_error_", return_value=True):
            details = {
                "title": "Team Meeting",
                "date": "2024-01-15",
                "time": "14:00",
                "duration": 60,
            }

            self.agent.create_event(details)

            # Verify event was added
            past_events = self.core_memory.get_memories_by_type(MemoryType.PAST_EVENT)
            assert len(past_events) == 1

        # Now delete the event
        with patch.object(
            self.agent.store, "removeEvent_span_error_", return_value=True
        ):
            delete_details = {"title": "Team Meeting", "date": "2024-01-15"}

            result = self.agent.delete_event(delete_details)

            assert result["success"] is True

            # Check that the event was removed from Core memory
            past_events = self.core_memory.get_memories_by_type(MemoryType.PAST_EVENT)
            assert len(past_events) == 0

    def test_move_event_with_core_memory(self):
        """Test that moving an event updates it in Core memory."""
        # First create an event
        with patch.object(self.agent.store, "saveEvent_span_error_", return_value=True):
            details = {
                "title": "Team Meeting",
                "date": "2024-01-15",
                "time": "14:00",
                "duration": 60,
            }

            self.agent.create_event(details)

        # Now move the event
        with patch.object(self.agent.store, "saveEvent_span_error_", return_value=True):
            move_details = {
                "title": "Team Meeting",
                "old_date": "2024-01-15",
                "new_date": "2024-01-16",
                "new_time": "15:00",
            }

            result = self.agent.move_event(move_details)

            assert result["success"] is True

            # Check that the event was updated in Core memory
            past_events = self.core_memory.get_memories_by_type(MemoryType.PAST_EVENT)
            assert len(past_events) == 1

            event = past_events[0]
            assert event.title == "Team Meeting"
            assert event.date == "2024-01-16"  # Should be updated

    def test_recall_similar_events(self):
        """Test that recall can find similar events."""
        # Add some events to Core memory
        event_data_1 = {
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

        event_data_2 = {
            "title": "Lunch with Client",
            "description": "Business lunch",
            "start_date": "2024-01-16",
            "duration": 90,
            "attendees": ["Client"],
            "location": "Restaurant",
            "is_recurring": False,
            "recurrence_pattern": "",
            "text_for_embedding": "Lunch with Client | Business lunch | Location: Restaurant",
        }

        self.core_memory.add_past_event(event_data_1)
        self.core_memory.add_past_event(event_data_2)

        # Mock the embedding manager to return similar events
        mock_similar_events = [
            {
                "metadata": {
                    "type": "past_event",
                    "title": "Team Meeting",
                    "duration": 60,
                    "location": "Conference Room A",
                },
                "similarity": 0.85,
            }
        ]

        with patch.object(
            self.core_memory.embedding_manager,
            "search_similar",
            return_value=mock_similar_events,
        ):
            # Search for similar events
            results = self.core_memory.recall("team meeting")

            assert len(results) == 1
            assert results[0]["metadata"]["title"] == "Team Meeting"

    def test_get_patterns_from_events(self):
        """Test that pattern analysis works with events."""
        # Add some events with patterns
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

    def test_suggest_similar_events(self):
        """Test that suggestion system works with events."""
        # Add some events
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

        self.core_memory.add_past_event(event_data)

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

    def test_core_memory_stats(self):
        """Test that Core memory statistics work correctly."""
        # Add some different types of memories
        self.core_memory.add_intention("I want to exercise more", "high")
        self.core_memory.add_commitment("follow up with Anna", "2024-01-20", "medium")
        self.core_memory.add_preference("no meetings before 11am", "scheduling", 0.9)

        # Add an event
        event_data = {
            "title": "Team Meeting",
            "description": "Weekly team sync",
            "start_date": "2024-01-15",
            "duration": 60,
            "attendees": ["Alice", "Bob"],
            "location": "Conference Room A",
            "is_recurring": True,
            "recurrence_pattern": "FREQ=WEEKLY",
            "text_for_embedding": "Team Meeting",
        }
        self.core_memory.add_past_event(event_data)

        # Get stats
        stats = self.core_memory.get_stats()

        assert stats["total_memories"] == 4
        assert "memory_types" in stats
        assert "embedding_stats" in stats

        memory_types = stats["memory_types"]
        assert memory_types["intention"] == 1
        assert memory_types["commitment"] == 1
        assert memory_types["preference"] == 1
        assert memory_types["past_event"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
