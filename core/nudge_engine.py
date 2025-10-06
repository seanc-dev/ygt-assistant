"""Contextual nudging engine for proactive calendar assistance."""

import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .memory_manager import CoreMemory, MemoryType


class NudgeType(Enum):
    """Types of contextual nudges."""

    TIME_PATTERN = "time_pattern"
    CONFLICT_RESOLUTION = "conflict_resolution"
    HABIT_REINFORCEMENT = "habit_reinforcement"
    PRODUCTIVITY_OPTIMIZATION = "productivity_optimization"
    SOCIAL_PATTERN = "social_pattern"
    HEALTH_WELLNESS = "health_wellness"


@dataclass
class Nudge:
    """A contextual suggestion for the user."""

    id: str
    type: NudgeType
    title: str
    description: str
    priority: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    context: Dict[str, Any]
    created_at: str
    expires_at: Optional[str] = None
    dismissed: bool = False


class ContextualNudger:
    """Provides contextual suggestions based on user patterns and current context."""

    def __init__(self, core_memory: CoreMemory):
        """
        Initialize the contextual nudger.

        Args:
            core_memory: Core memory system for pattern analysis
        """
        self.core_memory = core_memory
        self.nudges: Dict[str, Nudge] = {}
        self.user_preferences = {}
        self.nudge_history = []

        # Load existing nudges and preferences
        self._load_nudges()
        self._load_preferences()

    def _load_nudges(self):
        """Load existing nudges from storage."""
        nudge_path = "core/nudges.json"
        if os.path.exists(nudge_path):
            try:
                with open(nudge_path, "r") as f:
                    data = json.load(f)

                for nudge_data in data.get("nudges", []):
                    nudge = Nudge(
                        id=nudge_data["id"],
                        type=NudgeType(nudge_data["type"]),
                        title=nudge_data["title"],
                        description=nudge_data["description"],
                        priority=nudge_data["priority"],
                        confidence=nudge_data["confidence"],
                        context=nudge_data["context"],
                        created_at=nudge_data["created_at"],
                        expires_at=nudge_data.get("expires_at"),
                        dismissed=nudge_data.get("dismissed", False),
                    )
                    self.nudges[nudge.id] = nudge
            except Exception as e:
                print(f"Warning: Could not load nudges: {e}")

    def _save_nudges(self):
        """Save nudges to storage."""
        nudge_path = "core/nudges.json"
        try:
            data = {
                "nudges": [
                    {
                        "id": nudge.id,
                        "type": nudge.type.value,
                        "title": nudge.title,
                        "description": nudge.description,
                        "priority": nudge.priority,
                        "confidence": nudge.confidence,
                        "context": nudge.context,
                        "created_at": nudge.created_at,
                        "expires_at": nudge.expires_at,
                        "dismissed": nudge.dismissed,
                    }
                    for nudge in self.nudges.values()
                ],
                "last_updated": datetime.now().isoformat(),
            }

            os.makedirs(os.path.dirname(nudge_path), exist_ok=True)
            with open(nudge_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save nudges: {e}")

    def _load_preferences(self):
        """Load user preferences for nudging."""
        pref_path = "core/nudge_preferences.json"
        # Avoid persisting test-run side effects to keep tests deterministic
        if os.path.exists(pref_path) and "PYTEST_CURRENT_TEST" not in os.environ:
            try:
                with open(pref_path, "r") as f:
                    self.user_preferences = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load nudge preferences: {e}")

    def _save_preferences(self):
        """Save user preferences for nudging."""
        pref_path = "core/nudge_preferences.json"
        if "PYTEST_CURRENT_TEST" in os.environ:
            return
        try:
            with open(pref_path, "w") as f:
                json.dump(self.user_preferences, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save nudge preferences: {e}")

    def analyze_time_patterns(self) -> Dict[str, List[Dict]]:
        """
        Analyze user's time-based patterns.

        Returns:
            Dictionary of time patterns by category
        """
        patterns = {
            "meeting_times": [],
            "break_times": [],
            "focus_blocks": [],
            "social_events": [],
            "health_activities": [],
        }

        # Get all past events
        past_events = self.core_memory.get_memories_by_type(MemoryType.PAST_EVENT)

        for event in past_events:
            try:
                event_date = datetime.fromisoformat(event.date)
                hour = event_date.hour

                # Categorize events
                if "meeting" in event.title.lower() or "standup" in event.title.lower():
                    patterns["meeting_times"].append(
                        {"hour": hour, "title": event.title, "duration": event.duration}
                    )
                elif "lunch" in event.title.lower() or "break" in event.title.lower():
                    patterns["break_times"].append({"hour": hour, "title": event.title})
                elif "focus" in event.title.lower() or "work" in event.title.lower():
                    patterns["focus_blocks"].append(
                        {"hour": hour, "title": event.title, "duration": event.duration}
                    )
                elif "dinner" in event.title.lower() or "party" in event.title.lower():
                    patterns["social_events"].append(
                        {"hour": hour, "title": event.title}
                    )
                elif "gym" in event.title.lower() or "exercise" in event.title.lower():
                    patterns["health_activities"].append(
                        {"hour": hour, "title": event.title}
                    )
            except:
                continue

        return patterns

    def generate_suggestions(self, current_context: Dict) -> List[Nudge]:
        """
        Generate contextual suggestions based on current context.

        Args:
            current_context: Current user context (time, day, recent activities)

        Returns:
            List of contextual nudges
        """
        suggestions = []

        # Get current time and day
        now = datetime.now()
        current_hour = now.hour
        current_day = now.strftime("%A")

        # Analyze patterns
        patterns = self.analyze_time_patterns()

        # Generate time-based suggestions
        suggestions.extend(
            self._generate_time_based_suggestions(patterns, current_hour, current_day)
        )

        # Generate conflict resolution suggestions
        suggestions.extend(self._generate_conflict_suggestions(current_context))

        # Generate habit reinforcement suggestions
        suggestions.extend(self._generate_habit_suggestions(current_context))

        # Generate productivity optimization suggestions
        suggestions.extend(self._generate_productivity_suggestions(current_context))

        # Filter by user preferences and relevance
        filtered_suggestions = self._filter_suggestions(suggestions, current_context)

        return filtered_suggestions

    def _generate_time_based_suggestions(
        self, patterns: Dict, current_hour: int, current_day: str
    ) -> List[Nudge]:
        """Generate suggestions based on time patterns."""
        suggestions = []

        # Check for regular meeting times
        meeting_times = patterns.get("meeting_times", [])
        if meeting_times:
            # Find most common meeting hours
            from collections import Counter

            hour_counts = Counter([m["hour"] for m in meeting_times])
            most_common_hours = hour_counts.most_common(3)

            for hour, count in most_common_hours:
                if count >= 2:  # At least 2 meetings at this time
                    if abs(current_hour - hour) <= 1:  # Within 1 hour
                        nudge = Nudge(
                            id=f"time_pattern_{hour}_{datetime.now().timestamp()}",
                            type=NudgeType.TIME_PATTERN,
                            title=f"Regular meeting time approaching",
                            description=f"You usually have meetings around {hour}:00. Would you like me to check your availability?",
                            priority=0.7,
                            confidence=min(count / 5.0, 0.9),  # Cap at 0.9
                            context={
                                "hour": hour,
                                "count": count,
                                "current_hour": current_hour,
                            },
                            created_at=datetime.now().isoformat(),
                        )
                        suggestions.append(nudge)

        # Check for break time patterns
        break_times = patterns.get("break_times", [])
        if break_times:
            break_hours = [b["hour"] for b in break_times]
            if current_hour in break_hours:
                nudge = Nudge(
                    id=f"break_reminder_{datetime.now().timestamp()}",
                    type=NudgeType.TIME_PATTERN,
                    title="Time for your usual break",
                    description="This is when you usually take a break. Would you like me to schedule some downtime?",
                    priority=0.6,
                    confidence=0.8,
                    context={"break_hour": current_hour},
                    created_at=datetime.now().isoformat(),
                )
                suggestions.append(nudge)

        return suggestions

    def _generate_conflict_suggestions(self, current_context: Dict) -> List[Nudge]:
        """Generate suggestions for resolving scheduling conflicts."""
        suggestions = []

        # This would integrate with calendar to check for conflicts
        # For now, we'll create a placeholder suggestion
        if current_context.get("has_conflicts", False):
            nudge = Nudge(
                id=f"conflict_resolution_{datetime.now().timestamp()}",
                type=NudgeType.CONFLICT_RESOLUTION,
                title="Schedule conflict detected",
                description="I found a conflict in your schedule. Would you like me to help resolve it?",
                priority=0.9,
                confidence=0.8,
                context=current_context,
                created_at=datetime.now().isoformat(),
            )
            suggestions.append(nudge)

        return suggestions

    def _generate_habit_suggestions(self, current_context: Dict) -> List[Nudge]:
        """Generate suggestions for habit reinforcement."""
        suggestions = []

        # Check for health/wellness intentions
        intentions = self.core_memory.get_memories_by_type(MemoryType.INTENTION)
        for intention in intentions:
            if (
                "exercise" in intention.content.lower()
                or "fitness" in intention.content.lower()
            ):
                # Check if it's a good time for exercise
                now = datetime.now()
                if 6 <= now.hour <= 8 or 17 <= now.hour <= 19:  # Morning or evening
                    nudge = Nudge(
                        id=f"habit_reinforcement_{datetime.now().timestamp()}",
                        type=NudgeType.HABIT_REINFORCEMENT,
                        title="Time for your fitness goal",
                        description=f"You mentioned wanting to {intention.content}. Would you like me to schedule some exercise time?",
                        priority=0.8,
                        confidence=0.7,
                        context={
                            "intention": intention.content,
                            "current_time": now.isoformat(),
                        },
                        created_at=datetime.now().isoformat(),
                    )
                    suggestions.append(nudge)

        return suggestions

    def _generate_productivity_suggestions(self, current_context: Dict) -> List[Nudge]:
        """Generate suggestions for productivity optimization."""
        suggestions = []

        # Check for back-to-back meetings
        if current_context.get("back_to_back_meetings", 0) >= 3:
            nudge = Nudge(
                id=f"productivity_optimization_{datetime.now().timestamp()}",
                type=NudgeType.PRODUCTIVITY_OPTIMIZATION,
                title="Heavy meeting day ahead",
                description="You have several meetings back-to-back. Would you like me to add some buffer time between them?",
                priority=0.8,
                confidence=0.9,
                context=current_context,
                created_at=datetime.now().isoformat(),
            )
            suggestions.append(nudge)

        # Check for focus time opportunities
        if current_context.get("available_slots", 0) >= 2:
            nudge = Nudge(
                id=f"focus_time_{datetime.now().timestamp()}",
                type=NudgeType.PRODUCTIVITY_OPTIMIZATION,
                title="Focus time available",
                description="You have some open time slots. Would you like me to schedule some focused work time?",
                priority=0.6,
                confidence=0.7,
                context=current_context,
                created_at=datetime.now().isoformat(),
            )
            suggestions.append(nudge)

        return suggestions

    def _filter_suggestions(
        self, suggestions: List[Nudge], current_context: Dict
    ) -> List[Nudge]:
        """Filter suggestions based on user preferences and relevance."""
        filtered = []

        for suggestion in suggestions:
            # Check if user has dismissed similar suggestions recently
            if self._should_show_nudge(suggestion, current_context):
                filtered.append(suggestion)

        # Sort by priority and confidence
        filtered.sort(key=lambda x: (x.priority, x.confidence), reverse=True)

        # Limit to top 3 suggestions
        return filtered[:3]

    def _should_show_nudge(self, nudge: Nudge, current_context: Dict) -> bool:
        """Determine if a nudge should be shown based on user preferences."""
        # Check if user has dismissed similar nudges recently
        recent_dismissals = [
            n
            for n in self.nudge_history
            if n.get("type") == nudge.type.value and n.get("dismissed", False)
        ]

        if len(recent_dismissals) >= 3:  # User has dismissed this type 3+ times
            return False

        # Check user's nudge frequency preference
        max_nudges_per_day = self.user_preferences.get("max_nudges_per_day", 5)
        today_nudges = [
            n
            for n in self.nudges.values()
            if n.created_at.startswith(datetime.now().strftime("%Y-%m-%d"))
        ]

        if len(today_nudges) >= max_nudges_per_day:
            return False

        return True

    def learn_preferences(self, user_feedback: Dict):
        """
        Learn from user feedback to improve future suggestions.

        Args:
            user_feedback: Dictionary with feedback data
        """
        nudge_id = user_feedback.get("nudge_id")
        action = user_feedback.get("action")  # "accepted", "dismissed", "ignored"

        if nudge_id and nudge_id in self.nudges:
            nudge = self.nudges[nudge_id]

            # Record the feedback
            feedback_record = {
                "nudge_id": nudge_id,
                "type": nudge.type.value,
                "action": action,
                "timestamp": datetime.now().isoformat(),
                "context": user_feedback.get("context", {}),
            }

            self.nudge_history.append(feedback_record)

            # Update nudge if dismissed
            if action == "dismissed":
                nudge.dismissed = True

            # Learn from the feedback
            if action == "dismissed":
                # Reduce confidence for similar nudges
                self._reduce_confidence_for_type(nudge.type)
            elif action == "accepted":
                # Increase confidence for similar nudges
                self._increase_confidence_for_type(nudge.type)

            # Save updated data
            self._save_nudges()
            self._save_preferences()

    def _reduce_confidence_for_type(self, nudge_type: NudgeType):
        """Reduce confidence for a specific nudge type."""
        key = f"confidence_{nudge_type.value}"
        current_confidence = self.user_preferences.get(key, 0.8)
        self.user_preferences[key] = max(0.1, current_confidence - 0.1)

    def _increase_confidence_for_type(self, nudge_type: NudgeType):
        """Increase confidence for a specific nudge type."""
        key = f"confidence_{nudge_type.value}"
        current_confidence = self.user_preferences.get(key, 0.8)
        self.user_preferences[key] = min(1.0, current_confidence + 0.05)

    def should_nudge(self, context: Dict) -> bool:
        """
        Determine if nudging should be enabled based on context.

        Args:
            context: Current context

        Returns:
            True if nudging should be enabled
        """
        # Check user preference
        if not self.user_preferences.get("nudging_enabled", True):
            return False

        # Check time-based preferences
        now = datetime.now()
        hour = now.hour

        # Don't nudge during quiet hours
        quiet_hours = self.user_preferences.get(
            "quiet_hours", [22, 23, 0, 1, 2, 3, 4, 5, 6]
        )
        if hour in quiet_hours:
            return False

        # Check frequency limits
        max_nudges_per_hour = self.user_preferences.get("max_nudges_per_hour", 2)
        recent_nudges = [
            n
            for n in self.nudges.values()
            if (datetime.now() - datetime.fromisoformat(n.created_at)).seconds < 3600
        ]

        if len(recent_nudges) >= max_nudges_per_hour:
            return False

        return True

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the nudging system.

        Returns:
            Dictionary with statistics
        """
        total_nudges = len(self.nudges)
        active_nudges = len([n for n in self.nudges.values() if not n.dismissed])
        dismissed_nudges = len([n for n in self.nudges.values() if n.dismissed])

        # Calculate acceptance rate
        accepted_count = len(
            [f for f in self.nudge_history if f.get("action") == "accepted"]
        )
        total_feedback = len(self.nudge_history)
        acceptance_rate = accepted_count / total_feedback if total_feedback > 0 else 0

        return {
            "total_nudges": total_nudges,
            "active_nudges": active_nudges,
            "dismissed_nudges": dismissed_nudges,
            "acceptance_rate": acceptance_rate,
            "user_preferences": self.user_preferences,
            "nudge_history_count": len(self.nudge_history),
        }

    def clear_expired_nudges(self):
        """Remove nudges that have expired."""
        now = datetime.now()
        expired_nudges = []

        for nudge_id, nudge in self.nudges.items():
            if nudge.expires_at:
                try:
                    expires_at = datetime.fromisoformat(nudge.expires_at)
                    if now > expires_at:
                        expired_nudges.append(nudge_id)
                except:
                    continue

        for nudge_id in expired_nudges:
            del self.nudges[nudge_id]

        if expired_nudges:
            self._save_nudges()
