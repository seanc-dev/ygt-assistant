"""Tests for the embedding manager functionality."""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import numpy as np

from core.embedding_manager import EmbeddingManager


class TestEmbeddingManager:
    """Test the embedding manager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_memory.db")

        # Create a mock event for testing
        self.mock_event = Mock()
        self.mock_event.title = "Team Meeting"
        self.mock_event.notes = "Weekly team sync"
        self.mock_event.location = "Conference Room A"
        self.mock_event.startDate = datetime.now()
        self.mock_event.endDate = datetime.now() + timedelta(hours=1)
        self.mock_event.attendees = []
        self.mock_event.recurrenceRules = []

    def teardown_method(self):
        """Clean up test fixtures."""
        # Remove temporary directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_without_dependencies(self):
        """Test initialization without optional dependencies."""
        with patch.dict("sys.modules", {"openai": None, "chromadb": None}):
            manager = EmbeddingManager(self.test_db_path)
            assert manager.client is None
            assert manager.collection is None
            assert manager.openai_client is None

    def test_extract_event_data(self):
        """Test event data extraction."""
        manager = EmbeddingManager(self.test_db_path)

        events = [self.mock_event]
        event_data = manager.extract_event_data(events)

        assert len(event_data) == 1
        event = event_data[0]

        assert event["title"] == "Team Meeting"
        assert event["description"] == "Weekly team sync"
        assert event["location"] == "Conference Room A"
        assert event["duration"] == 60  # 1 hour
        assert event["is_recurring"] is False
        assert "text_for_embedding" in event

    def test_extract_event_data_with_attendees(self):
        """Test event data extraction with attendees."""
        manager = EmbeddingManager(self.test_db_path)

        # Create mock attendees
        attendee1 = Mock()
        attendee1.name = "Alice"
        attendee2 = Mock()
        attendee2.name = "Bob"

        self.mock_event.attendees = [attendee1, attendee2]

        events = [self.mock_event]
        event_data = manager.extract_event_data(events)

        assert event_data[0]["attendees"] == ["Alice", "Bob"]

    def test_extract_event_data_recurring(self):
        """Test event data extraction for recurring events."""
        manager = EmbeddingManager(self.test_db_path)

        # Make it a recurring event
        self.mock_event.recurrenceRules = ["FREQ=WEEKLY"]

        events = [self.mock_event]
        event_data = manager.extract_event_data(events)

        assert event_data[0]["is_recurring"] is True
        assert event_data[0]["recurrence_pattern"] == "FREQ=WEEKLY"

    def test_create_embedding_text(self):
        """Test embedding text creation."""
        manager = EmbeddingManager(self.test_db_path)

        event_dict = {
            "title": "Team Meeting",
            "description": "Weekly sync",
            "location": "Room A",
            "attendees": ["Alice", "Bob"],
            "is_recurring": True,
            "recurrence_pattern": "FREQ=WEEKLY",
            "duration": 60,
        }

        text = manager._create_embedding_text(event_dict)

        assert "Title: Team Meeting" in text
        assert "Description: Weekly sync" in text
        assert "Location: Room A" in text
        assert "Attendees: Alice, Bob" in text
        assert "Recurring event" in text
        assert "Pattern: FREQ=WEEKLY" in text
        assert "Duration: 60 minutes" in text

    @patch("core.embedding_manager.openai")
    def test_create_embeddings_with_openai(self, mock_openai):
        """Test embedding creation with OpenAI."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3] * 512  # 1536 dimensions
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.OpenAI.return_value = mock_client

        manager = EmbeddingManager(self.test_db_path)
        manager.openai_client = mock_client

        event_data = [
            {"title": "Test Event", "text_for_embedding": "Test event description"}
        ]
        embeddings = manager.create_embeddings(event_data)

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 1536
        mock_client.embeddings.create.assert_called_once()

    def test_create_embeddings_without_openai(self):
        """Test embedding creation without OpenAI (fallback)."""
        manager = EmbeddingManager(self.test_db_path)
        manager.openai_client = None

        event_data = [
            {"title": "Test Event", "text_for_embedding": "Test event description"}
        ]
        embeddings = manager.create_embeddings(event_data)

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 1536
        # Should be random embeddings
        assert isinstance(embeddings[0][0], float)

    def test_store_embeddings_json_fallback(self):
        """Test storing embeddings in JSON when ChromaDB is not available."""
        manager = EmbeddingManager(self.test_db_path)
        manager.collection = None

        embeddings = [[0.1, 0.2, 0.3] * 512]  # 1536 dimensions
        metadata = [{"title": "Test Event", "text_for_embedding": "Test description"}]

        result = manager.store_embeddings(embeddings, metadata)

        assert result is True

        # Check that JSON file was created
        json_path = self.test_db_path.replace(".db", ".json")
        assert os.path.exists(json_path)

        # Check file contents
        with open(json_path, "r") as f:
            data = json.load(f)

        assert "embeddings" in data
        assert "metadata" in data
        assert len(data["embeddings"]) == 1
        assert len(data["metadata"]) == 1

    def test_search_similar_json_fallback(self):
        """Test searching similar events using JSON fallback."""
        manager = EmbeddingManager(self.test_db_path)
        manager.openai_client = None
        manager.collection = None

        # Create some test data
        embeddings = [
            [0.1, 0.2, 0.3] * 512,  # Event 1
            [0.4, 0.5, 0.6] * 512,  # Event 2
            [0.7, 0.8, 0.9] * 512,  # Event 3
        ]
        metadata = [
            {"title": "Team Meeting", "text_for_embedding": "Team sync"},
            {"title": "Lunch", "text_for_embedding": "Lunch break"},
            {"title": "Gym", "text_for_embedding": "Workout session"},
        ]

        # Store the data
        manager.store_embeddings(embeddings, metadata)

        # Mock OpenAI for search
        with patch("core.embedding_manager.openai") as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = [Mock()]
            mock_response.data[0].embedding = [
                0.1,
                0.2,
                0.3,
            ] * 512  # Similar to first event
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.OpenAI.return_value = mock_client

            manager.openai_client = mock_client

            # Search for similar events
            results = manager.search_similar("team meeting", top_k=2)

            assert len(results) == 2
            # Should find the team meeting as most similar
            assert results[0]["metadata"]["title"] == "Team Meeting"

    def test_add_event_embedding(self):
        """Test adding a single event embedding."""
        manager = EmbeddingManager(self.test_db_path)

        # Mock OpenAI
        with patch("core.embedding_manager.openai") as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = [Mock()]
            mock_response.data[0].embedding = [0.1, 0.2, 0.3] * 512
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.OpenAI.return_value = mock_client

            manager.openai_client = mock_client

            event_data = {
                "title": "New Event",
                "text_for_embedding": "New event description",
            }
            result = manager.add_event_embedding(event_data)

            assert result is True

    def test_get_stats_empty(self):
        """Test getting stats for empty database."""
        manager = EmbeddingManager(self.test_db_path)
        stats = manager.get_stats()

        assert stats["total_events"] == 0
        assert stats["storage_type"] == "none"

    def test_get_stats_with_data(self):
        """Test getting stats for database with data."""
        manager = EmbeddingManager(self.test_db_path)

        # Add some data
        embeddings = [[0.1, 0.2, 0.3] * 512]
        metadata = [{"title": "Test Event"}]
        manager.store_embeddings(embeddings, metadata)

        stats = manager.get_stats()

        assert stats["total_events"] == 1
        assert stats["storage_type"] == "json"

    def test_calculate_duration(self):
        """Test duration calculation."""
        manager = EmbeddingManager(self.test_db_path)

        # Test with valid start and end dates
        self.mock_event.startDate = datetime(2024, 1, 1, 10, 0)
        self.mock_event.endDate = datetime(2024, 1, 1, 11, 30)

        duration = manager._calculate_duration(self.mock_event)
        assert duration == 90  # 1.5 hours = 90 minutes

    def test_extract_attendees(self):
        """Test attendee extraction."""
        manager = EmbeddingManager(self.test_db_path)

        # Create mock attendees
        attendee1 = Mock()
        attendee1.name = "Alice"
        attendee2 = Mock()
        attendee2.name = "Bob"

        self.mock_event.attendees = [attendee1, attendee2]

        attendees = manager._extract_attendees(self.mock_event)
        assert attendees == ["Alice", "Bob"]

    def test_extract_recurrence_pattern(self):
        """Test recurrence pattern extraction."""
        manager = EmbeddingManager(self.test_db_path)

        # Test with recurrence rules
        self.mock_event.recurrenceRules = ["FREQ=WEEKLY;INTERVAL=2"]

        pattern = manager._extract_recurrence_pattern(self.mock_event)
        assert pattern == "FREQ=WEEKLY;INTERVAL=2"

    def test_error_handling_in_create_embeddings(self):
        """Test error handling in embedding creation."""
        manager = EmbeddingManager(self.test_db_path)

        # Mock OpenAI to raise an exception
        with patch("core.embedding_manager.openai") as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.side_effect = Exception("API Error")
            mock_openai.OpenAI.return_value = mock_client

            manager.openai_client = mock_client

            event_data = [
                {"title": "Test Event", "text_for_embedding": "Test description"}
            ]
            embeddings = manager.create_embeddings(event_data)

            # Should fall back to random embeddings
            assert len(embeddings) == 1
            assert len(embeddings[0]) == 1536

    def test_error_handling_in_search(self):
        """Test error handling in search."""
        manager = EmbeddingManager(self.test_db_path)
        manager.openai_client = None

        # Search without OpenAI client
        results = manager.search_similar("test query")
        assert results == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
