"""Core memory manager for intelligent calendar assistance."""

import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from .embedding_manager import EmbeddingManager


class MemoryType(Enum):
    """Types of memory that Core can store."""

    PAST_EVENT = "past_event"
    INTENTION = "intention"
    COMMITMENT = "commitment"
    PREFERENCE = "preference"


@dataclass
class Memory:
    """Base memory structure."""

    id: str
    type: MemoryType
    content: str
    created_date: str
    metadata: Dict[str, Any]


@dataclass
class PastEvent(Memory):
    """Memory for past calendar events."""

    title: str
    description: str
    date: str
    duration: int
    attendees: List[str]
    location: str
    is_recurring: bool
    recurrence_pattern: str
    embedding: Optional[List[float]] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.attendees is None:
            self.attendees = []


@dataclass
class Intention(Memory):
    """Memory for user intentions."""

    priority: str
    related_events: List[str]
    progress_tracking: bool


@dataclass
class Commitment(Memory):
    """Memory for user commitments."""

    due_date: str
    status: str
    priority: str


@dataclass
class Preference(Memory):
    """Memory for user preferences."""

    category: str
    strength: float
    context: str


class CoreMemory:
    """Core memory system for intelligent calendar assistance."""

    def __init__(self, memory_db_path: str = "core/memory.db"):
        """
        Initialize Core memory system.

        Args:
            memory_db_path: Path to the memory database
        """
        self.memory_db_path = memory_db_path
        self.embedding_manager = EmbeddingManager(memory_db_path)
        self.memories: Dict[str, Memory] = {}

        # Load existing memories
        self._load_memories()

    def _load_memories(self):
        """Load memories from storage."""
        json_path = self.memory_db_path.replace(".db", "_memories.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r") as f:
                    data = json.load(f)

                for memory_data in data.get("memories", []):
                    memory_type = MemoryType(memory_data["type"])

                    if memory_type == MemoryType.PAST_EVENT:
                        memory = PastEvent(**memory_data)
                    elif memory_type == MemoryType.INTENTION:
                        memory = Intention(**memory_data)
                    elif memory_type == MemoryType.COMMITMENT:
                        memory = Commitment(**memory_data)
                    elif memory_type == MemoryType.PREFERENCE:
                        memory = Preference(**memory_data)
                    else:
                        continue

                    self.memories[memory.id] = memory

            except Exception as e:
                print(f"Warning: Could not load memories: {e}")

    def _save_memories(self):
        """Save memories to storage."""
        json_path = self.memory_db_path.replace(".db", "_memories.json")
        try:
            # Convert memories to serializable format
            memories_data = []
            for memory in self.memories.values():
                memory_dict = asdict(memory)
                # Convert enum to string for JSON serialization
                memory_dict["type"] = memory_dict["type"].value
                memories_data.append(memory_dict)

            data = {
                "memories": memories_data,
                "last_updated": datetime.now().isoformat(),
            }

            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            with open(json_path, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not save memories: {e}")

    def recall(
        self, query: str, context: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for similar past events using embeddings.

        This function performs semantic search through stored calendar events
        to find events similar to the query. It uses the embedding manager
        to find the most relevant past events based on semantic similarity.

        Args:
            query: Natural language search query (e.g., "my usual Tuesday meeting")
            context: Additional context for the search (optional)

        Returns:
            List of dictionaries containing similar events with metadata:
                - title: Event title
                - description: Event description
                - date: Event date
                - duration: Event duration in minutes
                - attendees: List of attendees
                - location: Event location
                - similarity_score: Semantic similarity score

        Examples:
            >>> memory.recall("team meeting")
            [{'title': 'Team Standup', 'date': '2024-01-15', 'similarity_score': 0.85}]

            >>> memory.recall("my usual Tuesday check-in")
            [{'title': 'Weekly Check-in with Boss', 'date': '2024-01-16', 'similarity_score': 0.92}]
        """
        # Search for similar events using embedding manager
        similar_events = self.embedding_manager.search_similar(query, top_k=5)

        # Filter to only past events
        past_events = []
        for event in similar_events:
            if "metadata" in event:
                metadata = event["metadata"]
                if metadata.get("type") == MemoryType.PAST_EVENT.value:
                    past_events.append(event)

        return past_events

    def get_patterns(self, event_type: str) -> Dict:
        """
        Extract patterns from past events.

        Args:
            event_type: Type of event to analyze (e.g., "meeting", "lunch")

        Returns:
            Dictionary with pattern information
        """
        # Get all past events
        past_events = [
            memory for memory in self.memories.values() if isinstance(memory, PastEvent)
        ]

        # Filter by event type
        relevant_events = []
        for event in past_events:
            if (
                event_type.lower() in event.title.lower()
                or event_type.lower() in event.description.lower()
            ):
                relevant_events.append(event)

        if not relevant_events:
            return {}

        # Analyze patterns
        patterns = {
            "total_events": len(relevant_events),
            "average_duration": sum(e.duration for e in relevant_events)
            / len(relevant_events),
            "common_times": self._analyze_timing_patterns(relevant_events),
            "common_locations": self._analyze_location_patterns(relevant_events),
            "common_attendees": self._analyze_attendee_patterns(relevant_events),
            "recurring_patterns": self._analyze_recurrence_patterns(relevant_events),
        }

        return patterns

    def _analyze_timing_patterns(self, events: List[PastEvent]) -> Dict:
        """Analyze timing patterns in events."""
        times = []
        for event in events:
            try:
                event_date = datetime.fromisoformat(event.date)
                times.append(event_date.hour)
            except:
                continue

        if not times:
            return {}

        # Find most common times
        from collections import Counter

        time_counts = Counter(times)
        most_common_times = time_counts.most_common(3)

        return {
            "most_common_hours": [hour for hour, count in most_common_times],
            "average_hour": sum(times) / len(times),
        }

    def _analyze_location_patterns(self, events: List[PastEvent]) -> Dict:
        """Analyze location patterns in events."""
        locations = [event.location for event in events if event.location]

        if not locations:
            return {}

        from collections import Counter

        location_counts = Counter(locations)
        most_common_locations = location_counts.most_common(3)

        return {
            "most_common_locations": [loc for loc, count in most_common_locations],
            "total_unique_locations": len(set(locations)),
        }

    def _analyze_attendee_patterns(self, events: List[PastEvent]) -> Dict:
        """Analyze attendee patterns in events."""
        all_attendees = []
        for event in events:
            all_attendees.extend(event.attendees)

        if not all_attendees:
            return {}

        from collections import Counter

        attendee_counts = Counter(all_attendees)
        most_common_attendees = attendee_counts.most_common(5)

        return {
            "most_common_attendees": [
                attendee for attendee, count in most_common_attendees
            ],
            "total_unique_attendees": len(set(all_attendees)),
        }

    def _analyze_recurrence_patterns(self, events: List[PastEvent]) -> Dict:
        """Analyze recurrence patterns in events."""
        recurring_events = [event for event in events if event.is_recurring]

        if not recurring_events:
            return {}

        patterns = {}
        for event in recurring_events:
            pattern = event.recurrence_pattern
            if pattern not in patterns:
                patterns[pattern] = 0
            patterns[pattern] += 1

        return {
            "recurring_events_count": len(recurring_events),
            "recurrence_patterns": patterns,
        }

    def suggest_similar(self, current_request: str) -> Dict:
        """
        Suggest similar past events for current request.

        Args:
            current_request: Current user request

        Returns:
            Dictionary with suggestions
        """
        # Search for similar events
        similar_events = self.recall(current_request)

        if not similar_events:
            return {}

        # Extract suggestions from similar events
        suggestions = []
        for event in similar_events:
            metadata = event.get("metadata", {})

            suggestion = {
                "title": metadata.get("title", ""),
                "duration": metadata.get("duration", 60),
                "location": metadata.get("location", ""),
                "attendees": metadata.get("attendees", []),
                "similarity": event.get("similarity", 0.0),
                "reason": f"Similar to past event: {metadata.get('title', '')}",
            }

            suggestions.append(suggestion)

        return {"suggestions": suggestions, "total_found": len(suggestions)}

    def add_past_event(self, event_data: Dict) -> str:
        """
        Add a past event to memory.

        Args:
            event_data: Event data dictionary

        Returns:
            ID of the created memory
        """
        memory_id = f"past_event_{datetime.now().timestamp()}"

        # Create past event memory
        past_event = PastEvent(
            id=memory_id,
            type=MemoryType.PAST_EVENT,
            content=event_data.get("text_for_embedding", ""),
            created_date=datetime.now().isoformat(),
            metadata={},
            title=event_data.get("title", ""),
            description=event_data.get("description", ""),
            date=event_data.get("start_date", ""),
            duration=event_data.get("duration", 60),
            attendees=event_data.get("attendees", []),
            location=event_data.get("location", ""),
            is_recurring=event_data.get("is_recurring", False),
            recurrence_pattern=event_data.get("recurrence_pattern", ""),
            tags=event_data.get("tags", []),
        )

        # Add to embedding manager
        self.embedding_manager.add_event_embedding(event_data)

        # Store in memory
        self.memories[memory_id] = past_event
        self._save_memories()

        return memory_id

    def add_intention(
        self, content: str, priority: str = "medium", related_events: List[str] = None
    ) -> str:
        """
        Add a user intention to memory.

        Args:
            content: Intention content
            priority: Priority level
            related_events: List of related event IDs

        Returns:
            ID of the created memory
        """
        memory_id = f"intention_{datetime.now().timestamp()}"

        intention = Intention(
            id=memory_id,
            type=MemoryType.INTENTION,
            content=content,
            created_date=datetime.now().isoformat(),
            metadata={},
            priority=priority,
            related_events=related_events or [],
            progress_tracking=True,
        )

        self.memories[memory_id] = intention
        self._save_memories()

        return memory_id

    def add_commitment(
        self, content: str, due_date: str, priority: str = "medium"
    ) -> str:
        """
        Add a user commitment to memory.

        Args:
            content: Commitment content
            due_date: Due date
            priority: Priority level

        Returns:
            ID of the created memory
        """
        memory_id = f"commitment_{datetime.now().timestamp()}"

        commitment = Commitment(
            id=memory_id,
            type=MemoryType.COMMITMENT,
            content=content,
            created_date=datetime.now().isoformat(),
            metadata={},
            due_date=due_date,
            status="pending",
            priority=priority,
        )

        self.memories[memory_id] = commitment
        self._save_memories()

        return memory_id

    def add_preference(
        self, content: str, category: str, strength: float = 0.8, context: str = ""
    ) -> str:
        """
        Add a user preference to memory.

        Args:
            content: Preference content
            category: Preference category
            strength: Preference strength (0.0 to 1.0)
            context: Context for the preference

        Returns:
            ID of the created memory
        """
        memory_id = f"preference_{datetime.now().timestamp()}"

        preference = Preference(
            id=memory_id,
            type=MemoryType.PREFERENCE,
            content=content,
            created_date=datetime.now().isoformat(),
            metadata={},
            category=category,
            strength=strength,
            context=context,
        )

        self.memories[memory_id] = preference
        self._save_memories()

        return memory_id

    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """
        Get a specific memory by ID.

        Args:
            memory_id: Memory ID

        Returns:
            Memory object or None if not found
        """
        return self.memories.get(memory_id)

    def get_memories_by_type(self, memory_type: MemoryType) -> List[Memory]:
        """
        Get all memories of a specific type.

        Args:
            memory_type: Type of memories to retrieve

        Returns:
            List of memories of the specified type
        """
        return [
            memory for memory in self.memories.values() if memory.type == memory_type
        ]

    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory by ID.

        Args:
            memory_id: Memory ID

        Returns:
            True if successful, False otherwise
        """
        if memory_id in self.memories:
            del self.memories[memory_id]
            self._save_memories()
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory system.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_memories": len(self.memories),
            "memory_types": {},
            "embedding_stats": self.embedding_manager.get_stats(),
        }

        # Count by type
        for memory in self.memories.values():
            memory_type = memory.type.value
            if memory_type not in stats["memory_types"]:
                stats["memory_types"][memory_type] = 0
            stats["memory_types"][memory_type] += 1

        return stats

    def clear_all_memories(self):
        """Clear all memories (use with caution)."""
        self.memories.clear()
        self._save_memories()

        # Also clear embedding data
        json_path = self.memory_db_path.replace(".db", ".json")
        if os.path.exists(json_path):
            os.remove(json_path)
