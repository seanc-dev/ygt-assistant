"""Narrative memory layer for high-level story arcs and user behavior patterns."""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class NarrativeType(Enum):
    """Types of narrative entries."""

    THEME = "theme"
    PATTERN = "pattern"


@dataclass
class ThemeEntry:
    """Represents a high-level theme or story arc."""

    topic: str
    summary: str
    last_updated: str
    source_refs: List[str]
    confidence: float = 0.5
    tags: List[str] = None

    def __post_init__(self):
        """Set default values after initialization."""
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThemeEntry":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class DynamicPattern:
    """Represents a dynamic behavioral pattern."""

    pattern: str
    datetime: str
    recurrence: str
    last_seen: str
    confidence: float = 0.5
    context: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DynamicPattern":
        """Create from dictionary."""
        return cls(**data)


class NarrativeMemory:
    """Manages high-level narrative memory for story arcs and patterns."""

    def __init__(self, storage_path: str = "core/narrative_memory.json"):
        """
        Initialize narrative memory system.

        Args:
            storage_path: Path to the narrative memory storage file
        """
        self.storage_path = storage_path
        self.themes: Dict[str, ThemeEntry] = {}
        self.patterns: Dict[str, DynamicPattern] = {}

        # Load existing narrative data
        self._load_narrative_data()

    def _load_narrative_data(self):
        """Load narrative data from storage."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    self.themes = {
                        theme_id: ThemeEntry.from_dict(theme_data)
                        for theme_id, theme_data in data.get("themes", {}).items()
                    }
                    self.patterns = {
                        pattern_id: DynamicPattern.from_dict(pattern_data)
                        for pattern_id, pattern_data in data.get("patterns", {}).items()
                    }
        except Exception as e:
            print(f"Warning: Could not load narrative data: {e}")
            self.themes = {}
            self.patterns = {}

    def _save_narrative_data(self):
        """Save narrative data to storage."""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            data = {
                "themes": {
                    theme_id: theme.to_dict() for theme_id, theme in self.themes.items()
                },
                "patterns": {
                    pattern_id: pattern.to_dict()
                    for pattern_id, pattern in self.patterns.items()
                },
            }
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save narrative data: {e}")

    def add_theme(
        self,
        topic: str,
        summary: str,
        source_refs: List[str] = None,
        confidence: float = 0.5,
        tags: List[str] = None,
    ) -> str:
        """
        Add a new theme to narrative memory.

        Args:
            topic: The theme topic
            summary: Summary of the theme
            source_refs: List of source references
            confidence: Confidence score (0.0 to 1.0)
            tags: List of tags

        Returns:
            Theme ID
        """
        if source_refs is None:
            source_refs = []
        if tags is None:
            tags = []

        theme_id = f"theme_{uuid.uuid4().hex[:8]}"
        theme = ThemeEntry(
            topic=topic,
            summary=summary,
            last_updated=datetime.now().strftime("%Y-%m-%d"),
            source_refs=source_refs,
            confidence=confidence,
            tags=tags,
        )

        self.themes[theme_id] = theme
        self._save_narrative_data()
        return theme_id

    def add_pattern(
        self,
        pattern: str,
        datetime_str: str,
        recurrence: str,
        confidence: float = 0.5,
        context: str = "",
    ) -> str:
        """
        Add a new dynamic pattern to narrative memory.

        Args:
            pattern: Pattern description
            datetime_str: When the pattern occurs
            recurrence: How often it recurs
            confidence: Confidence score (0.0 to 1.0)
            context: Context for the pattern

        Returns:
            Pattern ID
        """
        pattern_id = f"pattern_{uuid.uuid4().hex[:8]}"
        pattern_entry = DynamicPattern(
            pattern=pattern,
            datetime=datetime_str,
            recurrence=recurrence,
            last_seen=datetime.now().strftime("%Y-%m-%d"),
            confidence=confidence,
            context=context,
        )

        self.patterns[pattern_id] = pattern_entry
        self._save_narrative_data()
        return pattern_id

    def get_theme(self, theme_id: str) -> Optional[ThemeEntry]:
        """Get a theme by ID."""
        return self.themes.get(theme_id)

    def get_pattern(self, pattern_id: str) -> Optional[DynamicPattern]:
        """Get a pattern by ID."""
        return self.patterns.get(pattern_id)

    def update_theme(self, theme_id: str, **kwargs) -> bool:
        """Update an existing theme."""
        if theme_id not in self.themes:
            return False

        theme = self.themes[theme_id]
        for key, value in kwargs.items():
            if hasattr(theme, key):
                setattr(theme, key, value)

        theme.last_updated = datetime.now().strftime("%Y-%m-%d")
        self._save_narrative_data()
        return True

    def update_pattern(self, pattern_id: str, **kwargs) -> bool:
        """Update an existing pattern."""
        if pattern_id not in self.patterns:
            return False

        pattern = self.patterns[pattern_id]
        for key, value in kwargs.items():
            if hasattr(pattern, key):
                setattr(pattern, key, value)

        pattern.last_seen = datetime.now().strftime("%Y-%m-%d")
        self._save_narrative_data()
        return True

    def delete_theme(self, theme_id: str) -> bool:
        """Delete a theme."""
        if theme_id in self.themes:
            del self.themes[theme_id]
            self._save_narrative_data()
            return True
        return False

    def delete_pattern(self, pattern_id: str) -> bool:
        """Delete a pattern."""
        if pattern_id in self.patterns:
            del self.patterns[pattern_id]
            self._save_narrative_data()
            return True
        return False

    def search_themes(self, topic: str = None, content: str = None) -> List[ThemeEntry]:
        """Search themes by criteria."""
        results = []

        for theme in self.themes.values():
            if topic and topic.lower() not in theme.topic.lower():
                continue
            if content and content.lower() not in theme.summary.lower():
                continue
            results.append(theme)

        return results

    def search_patterns(
        self, pattern: str = None, recurrence: str = None
    ) -> List[DynamicPattern]:
        """Search patterns by criteria."""
        results = []

        for pattern_entry in self.patterns.values():
            if pattern and pattern.lower() not in pattern_entry.pattern.lower():
                continue
            if (
                recurrence
                and recurrence.lower() not in pattern_entry.recurrence.lower()
            ):
                continue
            results.append(pattern_entry)

        return results

    def save(self):
        """Save narrative data to storage."""
        self._save_narrative_data()

    def analyze_themes_from_events(self, events: List[Dict]) -> List[ThemeEntry]:
        """Analyze events to extract themes."""
        # Simple theme extraction based on event titles and tags
        themes = []

        # Group events by common tags
        tag_groups = {}
        for event in events:
            tags = event.get("tags", [])
            for tag in tags:
                if tag not in tag_groups:
                    tag_groups[tag] = []
                tag_groups[tag].append(event)

        # Create themes for significant tag groups
        for tag, tag_events in tag_groups.items():
            if len(tag_events) >= 2:  # At least 2 events to form a theme
                titles = [event.get("title", "") for event in tag_events]
                descriptions = [event.get("description", "") for event in tag_events]

                summary = f"User has {len(tag_events)} events related to {tag}: {', '.join(titles[:3])}"
                if len(titles) > 3:
                    summary += f" and {len(titles) - 3} more"

                theme = ThemeEntry(
                    topic=f"{tag.title()} Activities",
                    summary=summary,
                    last_updated=datetime.now().strftime("%Y-%m-%d"),
                    source_refs=[f"event_{i}" for i in range(len(tag_events))],
                    confidence=0.6,
                    tags=[tag],
                )
                themes.append(theme)

        return themes

    def analyze_patterns_from_events(self, events: List[Dict]) -> List[DynamicPattern]:
        """Analyze events to extract patterns."""
        # Simple pattern detection based on recurring titles
        patterns = []

        # Group events by title
        title_groups = {}
        for event in events:
            title = event.get("title", "")
            if title not in title_groups:
                title_groups[title] = []
            title_groups[title].append(event)

        # Create patterns for recurring events
        for title, title_events in title_groups.items():
            if len(title_events) >= 2:  # At least 2 events to form a pattern
                # Simple pattern detection
                if len(title_events) >= 3:
                    recurrence = "daily"
                elif len(title_events) >= 2:
                    recurrence = "weekly"
                else:
                    continue

                pattern = DynamicPattern(
                    pattern=title,
                    datetime="various times",
                    recurrence=recurrence,
                    last_seen=datetime.now().strftime("%Y-%m-%d"),
                    confidence=0.5,
                    context="detected from events",
                )
                patterns.append(pattern)

        return patterns

    def get_stats(self) -> Dict[str, Any]:
        """Get narrative memory statistics."""
        return {
            "total_themes": len(self.themes),
            "total_patterns": len(self.patterns),
            "storage_path": self.storage_path,
            "themes_by_confidence": {
                "high": len([t for t in self.themes.values() if t.confidence >= 0.8]),
                "medium": len(
                    [t for t in self.themes.values() if 0.5 <= t.confidence < 0.8]
                ),
                "low": len([t for t in self.themes.values() if t.confidence < 0.5]),
            },
            "patterns_by_recurrence": {
                "daily": len(
                    [p for p in self.patterns.values() if p.recurrence == "daily"]
                ),
                "weekly": len(
                    [p for p in self.patterns.values() if p.recurrence == "weekly"]
                ),
                "monthly": len(
                    [p for p in self.patterns.values() if p.recurrence == "monthly"]
                ),
            },
        }

    def extract_themes_from_core_memory(self, core_memory) -> List[ThemeEntry]:
        """Extract themes from CoreMemory system."""
        # This is a placeholder for integration with CoreMemory
        # In a real implementation, this would analyze CoreMemory data
        themes = []

        try:
            # Get past events from core memory
            past_events = core_memory.get_memories_by_type("past_event")

            # Group by tags or categories
            categories = {}
            for event in past_events:
                tags = event.metadata.get("tags", [])
                for tag in tags:
                    if tag not in categories:
                        categories[tag] = []
                    categories[tag].append(event)

            # Create themes for significant categories
            for category, events in categories.items():
                if len(events) >= 2:
                    theme = ThemeEntry(
                        topic=f"{category.title()} Activities",
                        summary=f"User has {len(events)} {category} related activities",
                        last_updated=datetime.now().strftime("%Y-%m-%d"),
                        source_refs=[event.id for event in events],
                        confidence=0.6,
                        tags=[category],
                    )
                    themes.append(theme)

        except Exception as e:
            print(f"Warning: Could not extract themes from core memory: {e}")

        return themes
