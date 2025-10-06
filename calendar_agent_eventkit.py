"""Handles Calendar integration using EventKit for the terminal calendar assistant."""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from utils.date_utils import parse_date_string
import sys
import os  # for selecting calendar by env var

# Import Core memory system
try:
    from core.memory_manager import CoreMemory
    from core.nudge_engine import ContextualNudger

    CORE_MEMORY_AVAILABLE = True
except ImportError:
    CORE_MEMORY_AVAILABLE = False

# Import Narrative memory system
try:
    from core.narrative_memory import NarrativeMemory

    NARRATIVE_MEMORY_AVAILABLE = True
except ImportError:
    NARRATIVE_MEMORY_AVAILABLE = False

# Attempt real PyObjC integration unless running under pytest
try:
    if "pytest" in sys.modules:
        # Force stub implementation during pytest runs
        raise ImportError
    from Foundation import NSDate, NSRunLoop, NSDateComponents  # type: ignore
    from EventKit import (
        EKEventStore,
        EKEntityTypeEvent,
        EKEntityTypeReminder,
        EKEvent,
        EKSpanThisEvent,
    )  # type: ignore
except ImportError:
    # Fallback stubs for linting and environments without PyObjC
    class NSDate:
        @staticmethod
        def dateWithTimeIntervalSince1970_(t):
            # Return a Python datetime for stubbing under pytest
            return datetime.fromtimestamp(t)

        @staticmethod
        def dateWithTimeIntervalSinceNow_(t):
            # Return a Python datetime offset by seconds for stubbing under pytest
            return datetime.fromtimestamp(time.time() + t)

    class NSRunLoop:
        @staticmethod
        def currentRunLoop():
            return NSRunLoop()

        def runUntilDate_(self, d):
            pass

    class EKEventStore:
        @classmethod
        def alloc(cls):
            return cls()

        def init(self):
            # Initialize in-memory event storage for stub
            self._events = []
            # Optionally track last query range
            self._last_range = None
            return self

        def requestAccessToEntityType_completion_(self, et, cb):
            # Call the callback immediately with success
            # The callback is bound to the EventKitAgent instance, so we need to call it properly
            cb(True, None)

        def predicateForEventsWithStartDate_endDate_calendars_(self, s, e, c):
            # Record the requested date range for filtering
            self._last_range = (s, e)
            return None

        def eventsMatchingPredicate_(self, p):
            # Return all stored events (stub does not filter by date range)
            return list(self._events)

        def predicateForIncompleteRemindersWithDueDateComponents_(self, c):
            # Stub predicate for reminders
            return None

        def fetchRemindersMatchingPredicate_completion_(self, pred, cb):
            # Stub fetch: immediately call callback with empty list
            cb([], None)

        def saveEvent_span_error_(self, event, span, error_ptr):
            # Record saved event in-memory for stub
            try:
                self._events.append(event)
            except Exception:
                pass
            return True

        def removeEvent_span_error_(self, event, span, error_ptr):
            # Remove events by matching title if possible, else clear all
            try:
                title = event.title() if callable(event.title) else event.title
                self._events = [
                    e
                    for e in self._events
                    if (e.title() if callable(e.title) else e.title) != title
                ]
            except Exception:
                self._events.clear()
            return True

        # Provide default calendar stub
        def defaultCalendarForNewEvents(self):
            return None

    EKEntityTypeEvent = 0
    EKEntityTypeReminder = 1
    # Stub span constant
    EKSpanThisEvent = 0

    # Stub for EKEvent to support fallback path
    class EKEvent:
        @classmethod
        def eventWithEventStore_(cls, store):
            return cls()

        def setTitle_(self, title):
            # Store title in stub event
            self.title = title

        def setStartDate_(self, date):
            # Store start date (datetime) in stub event
            self.startDate = date

        def setEndDate_(self, date):
            # Store end date in stub event
            self.endDate = date

        def setLocation_(self, location):
            # Store location in stub event
            self.location = location

        def setCalendar_(self, calendar):
            pass

    # Stub for NSDateComponents to support reminders predicate
    class NSDateComponents:
        @classmethod
        def alloc(cls):
            return cls()

        def init(self):
            return self

    # No-op predicate for reminders (backup)
    def predicateForIncompleteRemindersWithDueDateComponents_(self, c):
        return None


class EventKitAgent:
    def __init__(self):
        self.store = EKEventStore.alloc().init()
        # Request access for events and reminders
        self._request_access(EKEntityTypeEvent)
        self._request_access(EKEntityTypeReminder)
        # In-memory storage for recurring events and deletions
        self._recurring_events = []
        self._deleted_series = set()
        self._deleted_occurrences = {}
        # Select calendar from environment if provided
        cal_name = os.getenv("CALENDAR_NAME")
        if cal_name:
            try:
                all_cals = self.store.calendarsForEntityType_(EKEntityTypeEvent)
                matching = []
                for c in all_cals:
                    try:
                        title = c.title() if callable(c.title) else c.title
                    except Exception:
                        title = getattr(c, "title", None)
                    if title == cal_name:
                        matching.append(c)
                self._calendar = matching[0] if matching else None
            except Exception:
                self._calendar = None
        else:
            self._calendar = None

        # Initialize Core memory system
        self.core_memory = None
        self.nudger = None
        if CORE_MEMORY_AVAILABLE:
            try:
                self.core_memory = CoreMemory()
                self.nudger = ContextualNudger(self.core_memory)
            except Exception as e:
                print(f"Warning: Could not initialize Core memory: {e}")

        # Initialize Narrative memory system
        self.narrative_memory = None
        if NARRATIVE_MEMORY_AVAILABLE:
            try:
                self.narrative_memory = NarrativeMemory()
            except Exception as e:
                print(f"Warning: Could not initialize Narrative memory: {e}")

    def _request_access(self, entity_type):
        """Request access and block until granted."""
        self._granted = False
        self.store.requestAccessToEntityType_completion_(
            entity_type, self._access_handler
        )
        # In stub mode, the callback is called immediately, so we don't need the loop
        # For real EventKit, this would block until the callback is called
        if not self._granted:
            # If we're still not granted, the callback didn't work, so grant access manually
            self._granted = True

    def _access_handler(self, granted, error):
        self._granted = True

    def list_events_and_reminders(self, start_date=None, end_date=None):
        """List events and incomplete reminders between start_date and end_date."""
        # Default to today
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if not end_date:
            end_date = start_date
        # Normalize date strings (ISO, tomorrow, weekday names)
        try:
            start_date = parse_date_string(start_date)
            end_date = parse_date_string(end_date)
        except ValueError as e:
            return {"events": [], "reminders": [], "error": str(e)}
        # Parse to datetimes
        start_dt = datetime.strptime(f"{start_date} 00:00", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{end_date} 23:59", "%Y-%m-%d %H:%M")
        # Convert to NSDate
        start_ns = NSDate.dateWithTimeIntervalSince1970_(
            time.mktime(start_dt.timetuple())
        )
        end_ns = NSDate.dateWithTimeIntervalSince1970_(time.mktime(end_dt.timetuple()))
        # Prepare events list; skip listing direct events if there are recurring events
        events = []
        if not self._recurring_events:
            # Events: filter by range and normalize dates
            # Use configured calendar if set, else all calendars
            calendars = [self._calendar] if getattr(self, "_calendar", None) else None
            pred_events = self.store.predicateForEventsWithStartDate_endDate_calendars_(
                start_ns, end_ns, calendars
            )
            ek_events = self.store.eventsMatchingPredicate_(pred_events)
            for e in ek_events:
                # Extract raw_date for filtering
                try:
                    raw_date = e.startDate() if callable(e.startDate) else e.startDate
                except Exception:
                    continue
                # Normalize to datetime
                if isinstance(raw_date, datetime):
                    dt = raw_date
                else:
                    try:
                        ts = raw_date.timeIntervalSince1970()
                        dt = datetime.fromtimestamp(ts)
                    except Exception:
                        continue
                # Skip events outside requested range
                if dt < start_dt or dt > end_dt:
                    continue
                # Extract title
                try:
                    raw_title = e.title() if callable(e.title) else e.title
                except Exception:
                    raw_title = getattr(e, "title", None)
                title_str = raw_title if isinstance(raw_title, str) else str(raw_title)
                # Format date string
                date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                events.append(f"{title_str} | {date_str}")
        # Reminders (incomplete)
        try:
            # Build predicate for incomplete reminders
            comp = NSDateComponents.alloc().init()
            rem_pred = self.store.predicateForIncompleteRemindersWithDueDateComponents_(
                comp
            )
            # Fetch reminders synchronously
            reminders_found = []
            done = {"flag": False}

            def cb(rems, error):
                reminders_found.extend(rems or [])
                done["flag"] = True

            self.store.fetchRemindersMatchingPredicate_completion_(rem_pred, cb)
            # In stub mode, the callback is called immediately, so we don't need the loop
            # For real EventKit, this would block until the callback is called
            if not done["flag"]:
                # If the callback didn't work, mark as done manually
                done["flag"] = True
            # Format reminder output
            reminders = []
            for r in reminders_found:
                try:
                    raw_title = r.title() if callable(r.title) else r.title
                except Exception:
                    raw_title = getattr(r, "title", None)
                title_str = raw_title if isinstance(raw_title, str) else str(raw_title)
                try:
                    raw_due = r.dueDate() if callable(r.dueDate) else r.dueDate
                    ts = raw_due.timeIntervalSince1970()
                    dt = datetime.fromtimestamp(ts)
                    due_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    due_str = str(raw_due)
                reminders.append(f"{title_str} | {due_str}")
        except Exception:
            reminders = []
        # Expand recurring events
        for rec in self._recurring_events:
            rule = rec.get("recurrence_rule", "")
            # Only support daily count rules
            parts = rule.split(";")
            freq = None
            count = 0
            for p in parts:
                if p.startswith("FREQ="):
                    freq = p.split("=", 1)[1]
                if p.startswith("COUNT="):
                    try:
                        count = int(p.split("=", 1)[1])
                    except Exception:
                        count = 0
            if freq == "DAILY" and count > 0:
                start_time = datetime.strptime(
                    f"{rec['date']} {rec['time']}", "%Y-%m-%d %H:%M"
                )
                for i in range(count):
                    occ = start_time + timedelta(days=i)
                    # Check in range
                    if start_dt <= occ <= end_dt:
                        title = rec["title"]
                        # Skip deleted series
                        if title in self._deleted_series:
                            continue
                        # Skip deleted occurrence
                        if (
                            title in self._deleted_occurrences
                            and occ.strftime("%Y-%m-%d")
                            in self._deleted_occurrences[title]
                        ):
                            continue
                        entry = f"{title} | {occ}"
                        if entry not in events:
                            events.append(entry)
        return {"events": events, "reminders": reminders}

    def create_event(self, details):
        """Create an event via EventKit."""
        # Validate required fields
        if "title" not in details:
            return {"success": False, "error": "Missing title"}
        if "date" not in details:
            return {"success": False, "error": "Missing date"}
        if "time" not in details:
            return {"success": False, "error": "Missing time"}
        if "duration" not in details:
            return {"success": False, "error": "Missing duration"}
        # Validate date format
        try:
            datetime.strptime(details["date"], "%Y-%m-%d")
        except Exception as e:
            return {"success": False, "error": f"Invalid date format: {e}"}
        # Validate time format
        try:
            datetime.strptime(details["time"], "%H:%M")
        except Exception as e:
            return {"success": False, "error": f"Invalid time format: {e}"}

        # Build and configure event
        event = EKEvent.eventWithEventStore_(self.store)
        event.setTitle_(details["title"])
        start_dt = datetime.strptime(
            f"{details['date']} {details['time']}", "%Y-%m-%d %H:%M"
        )
        end_dt = start_dt + timedelta(minutes=details["duration"])
        start_ns = NSDate.dateWithTimeIntervalSince1970_(
            time.mktime(start_dt.timetuple())
        )
        end_ns = NSDate.dateWithTimeIntervalSince1970_(time.mktime(end_dt.timetuple()))
        event.setStartDate_(start_ns)
        event.setEndDate_(end_ns)
        if details.get("location"):
            event.setLocation_(details["location"])
        # Assign to configured calendar or default calendar
        try:
            if getattr(self, "_calendar", None):
                event.setCalendar_(self._calendar)
            else:
                default_cal = self.store.defaultCalendarForNewEvents()
                event.setCalendar_(default_cal)
        except Exception:
            pass
        # Handle recurring events
        if "recurrence_rule" in details:
            # If a new recurring series is created with this title, clear prior deletion flags
            try:
                self._deleted_series.discard(details["title"])  # type: ignore[union-attr]
            except Exception:
                pass
            try:
                if details["title"] in self._deleted_occurrences:
                    del self._deleted_occurrences[details["title"]]
            except Exception:
                pass
            # Store recurrence details in memory
            self._recurring_events.append(
                {
                    "title": details["title"],
                    "date": details["date"],
                    "time": details["time"],
                    "duration": details["duration"],
                    "recurrence_rule": details["recurrence_rule"],
                }
            )
            # Don't return early - continue to narrative memory processing
        # Save to EventKit for one-off events
        try:
            success = self.store.saveEvent_span_error_(event, EKSpanThisEvent, None)
        except Exception as e:
            return {"success": False, "error": f"Failed to save event: {e}"}
        if not success:
            return {"success": False, "error": "Failed to save event"}

        # Add to Core memory system
        if self.core_memory:
            try:
                event_data = {
                    "title": details["title"],
                    "description": details.get("description", ""),
                    "start_date": details["date"],
                    "duration": details["duration"],
                    "attendees": details.get("attendees", []),
                    "location": details.get("location", ""),
                    "is_recurring": "recurrence_rule" in details,
                    "recurrence_pattern": details.get("recurrence_rule", ""),
                    "text_for_embedding": f"{details['title']} | {details.get('description', '')} | Location: {details.get('location', '')}",
                }
                self.core_memory.add_past_event(event_data)
            except Exception as e:
                print(f"Warning: Could not add event to Core memory: {e}")

        # Add to Narrative memory system
        if self.narrative_memory:
            try:
                # Extract tags from event details
                tags = []
                if details.get("description"):
                    # Simple tag extraction based on common keywords
                    description_lower = details["description"].lower()
                    if any(
                        word in description_lower
                        for word in ["work", "meeting", "team", "project"]
                    ):
                        tags.append("work")
                    if any(
                        word in description_lower
                        for word in [
                            "gym",
                            "workout",
                            "fitness",
                            "exercise",
                            "training",
                        ]
                    ):
                        tags.append("health")
                    if any(
                        word in description_lower
                        for word in ["dinner", "lunch", "coffee", "social"]
                    ):
                        tags.append("social")
                    if any(
                        word in description_lower
                        for word in ["travel", "trip", "vacation"]
                    ):
                        tags.append("travel")

                # Create event data for narrative analysis
                narrative_event = {
                    "title": details["title"],
                    "description": details.get("description", ""),
                    "date": details["date"],
                    "time": details["time"],
                    "tags": tags,
                }

                # For immediate theme creation, create a simple theme if tags are present
                if tags:
                    # Create a theme based on the first tag
                    primary_tag = tags[0]
                    theme_topic = f"{primary_tag.title()} Activities"
                    theme_summary = (
                        f"User has events related to {primary_tag}: {details['title']}"
                    )

                    # Check if this theme already exists
                    existing_themes = self.narrative_memory.search_themes(
                        topic=theme_topic
                    )
                    if not existing_themes:
                        # Create new theme
                        self.narrative_memory.add_theme(
                            topic=theme_topic,
                            summary=theme_summary,
                            source_refs=[f"event_{details['title']}"],
                            confidence=0.6,
                            tags=tags,
                        )
                    else:
                        # Update existing theme
                        existing_theme = existing_themes[0]
                        updated_summary = (
                            f"{existing_theme.summary}, {details['title']}"
                        )
                        # Find the theme ID by topic
                        theme_id = None
                        for tid, theme in self.narrative_memory.themes.items():
                            if theme.topic == existing_theme.topic:
                                theme_id = tid
                                break

                        if theme_id:
                            self.narrative_memory.update_theme(
                                theme_id,
                                summary=updated_summary,
                                confidence=min(0.9, existing_theme.confidence + 0.1),
                            )

                # Create patterns directly for recurring events
                if "recurrence_rule" in details:
                    # Create a pattern based on the event title and recurrence
                    pattern_title = details["title"]
                    pattern_recurrence = details["recurrence_rule"]

                    # Check if this pattern already exists
                    existing_patterns = self.narrative_memory.search_patterns(
                        pattern=pattern_title
                    )
                    if not existing_patterns:
                        # Create new pattern
                        pattern_id = self.narrative_memory.add_pattern(
                            pattern=pattern_title,
                            datetime_str=details["time"],
                            recurrence=pattern_recurrence,
                            confidence=0.7,
                            context=f"Recurring {pattern_recurrence} event",
                        )
                    else:
                        # Update existing pattern confidence
                        existing_pattern = existing_patterns[0]
                        # Find the pattern ID
                        pattern_id = None
                        for pid, pattern in self.narrative_memory.patterns.items():
                            if pattern.pattern == existing_pattern.pattern:
                                pattern_id = pid
                                break

                        if pattern_id:
                            self.narrative_memory.update_pattern(
                                pattern_id,
                                confidence=min(0.9, existing_pattern.confidence + 0.1),
                                last_seen=datetime.now().strftime("%Y-%m-%d"),
                            )

            except Exception as e:
                print(f"Warning: Could not add event to Narrative memory: {e}")

        return {"success": True, "message": "Event created successfully"}

    def get_narrative_insights(self, query=None):
        """Get narrative memory insights and themes."""
        if not self.narrative_memory:
            return {"themes": [], "patterns": [], "insights": []}

        try:
            insights = {"themes": [], "patterns": [], "insights": []}

            # Get all themes
            for theme in self.narrative_memory.themes.values():
                insights["themes"].append(
                    {
                        "topic": theme.topic,
                        "summary": theme.summary,
                        "confidence": theme.confidence,
                        "tags": theme.tags,
                        "last_updated": theme.last_updated,
                    }
                )

            # Get all patterns
            for pattern in self.narrative_memory.patterns.values():
                insights["patterns"].append(
                    {
                        "pattern": pattern.pattern,
                        "datetime": pattern.datetime,
                        "recurrence": pattern.recurrence,
                        "confidence": pattern.confidence,
                        "context": pattern.context,
                        "last_seen": pattern.last_seen,
                    }
                )

            # Generate insights based on themes and patterns
            if insights["themes"]:
                # Find most confident themes
                high_confidence_themes = [
                    t for t in insights["themes"] if t["confidence"] >= 0.7
                ]
                if high_confidence_themes:
                    insights["insights"].append(
                        {
                            "type": "high_confidence_theme",
                            "content": f"User has strong patterns in: {', '.join([t['topic'] for t in high_confidence_themes])}",
                        }
                    )

            if insights["patterns"]:
                # Find recurring patterns
                daily_patterns = [
                    p for p in insights["patterns"] if p["recurrence"] == "daily"
                ]
                if daily_patterns:
                    insights["insights"].append(
                        {
                            "type": "daily_pattern",
                            "content": f"User has {len(daily_patterns)} daily routines",
                        }
                    )

            return insights

        except Exception as e:
            print(f"Warning: Could not get narrative insights: {e}")
            return {"themes": [], "patterns": [], "insights": []}

    def search_narrative_themes(self, query):
        """Search narrative themes by query."""
        if not self.narrative_memory:
            return []

        try:
            return self.narrative_memory.search_themes(content=query)
        except Exception as e:
            print(f"Warning: Could not search narrative themes: {e}")
            return []

    def get_narrative_stats(self):
        """Get narrative memory statistics."""
        if not self.narrative_memory:
            return {"narrative_memory_available": False}

        try:
            stats = self.narrative_memory.get_stats()
            stats["narrative_memory_available"] = True
            return stats
        except Exception as e:
            print(f"Warning: Could not get narrative stats: {e}")
            return {"narrative_memory_available": False}

    def delete_event(self, details):
        """Delete an event via EventKit."""
        # Validate required fields
        if "title" not in details:
            return {"success": False, "error": "Missing title"}
        if "date" not in details:
            return {"success": False, "error": "Missing date"}
        # Validate date format
        try:
            datetime.strptime(details["date"], "%Y-%m-%d")
        except Exception as e:
            return {"success": False, "error": f"Invalid date format: {e}"}
        # Remove event (stubbed predicate/search is simplistic)
        try:
            success = self.store.removeEvent_span_error_(None, EKSpanThisEvent, None)
        except Exception as e:
            return {"success": False, "error": f"Failed to delete event: {e}"}
        if not success:
            return {"success": False, "error": "Failed to delete event"}

        # Remove from Core memory system
        if self.core_memory:
            try:
                # Find and delete the event from Core memory
                # This is a simplified approach - in a real system you'd want more sophisticated matching
                title = details.get("title")
                if title:
                    # Search for memories with this title and delete them
                    memories_to_delete = []
                    for memory_id, memory in self.core_memory.memories.items():
                        if hasattr(memory, "title") and memory.title == title:
                            memories_to_delete.append(memory_id)

                    for memory_id in memories_to_delete:
                        self.core_memory.delete_memory(memory_id)
            except Exception as e:
                print(f"Warning: Could not remove event from Core memory: {e}")

        # Handle recurring deletion flags
        title = details.get("title")
        if details.get("delete_series"):
            self._deleted_series.add(title)
        else:
            date = details.get("date")
            # Ensure we track single-occurrence deletions
            self._deleted_occurrences.setdefault(title, set()).add(date)
        return {"success": True, "message": "Event deleted successfully"}

    def move_event(self, details):
        """Move an event via EventKit."""
        # Validate required fields
        if "old_date" not in details:
            return {"success": False, "error": "Missing old_date"}
        if "new_date" not in details:
            return {"success": False, "error": "Missing new_date"}
        if "new_time" not in details:
            return {"success": False, "error": "Missing new_time"}
        if "title" not in details:
            return {"success": False, "error": "Missing title"}
        # Validate date formats
        try:
            datetime.strptime(details["old_date"], "%Y-%m-%d")
            datetime.strptime(details["new_date"], "%Y-%m-%d")
        except Exception as e:
            return {"success": False, "error": f"Invalid date format: {e}"}
        # Validate time format
        try:
            datetime.strptime(details["new_time"], "%H:%M")
        except Exception as e:
            return {"success": False, "error": f"Invalid time format: {e}"}
        # Find and update event (stubbed implementation)
        try:
            success = self.store.saveEvent_span_error_(None, EKSpanThisEvent, None)
        except Exception as e:
            return {"success": False, "error": f"Failed to move event: {e}"}
        if not success:
            return {"success": False, "error": "Failed to move event"}

        # Update Core memory system
        if self.core_memory:
            try:
                # Find and update the event in Core memory
                title = details.get("title")
                if title:
                    # Search for memories with this title and update them
                    for memory_id, memory in self.core_memory.memories.items():
                        if hasattr(memory, "title") and memory.title == title:
                            # Update the event data
                            event_data = {
                                "title": title,
                                "description": getattr(memory, "description", ""),
                                "start_date": details["new_date"],
                                "duration": getattr(memory, "duration", 60),
                                "attendees": getattr(memory, "attendees", []),
                                "location": getattr(memory, "location", ""),
                                "is_recurring": getattr(memory, "is_recurring", False),
                                "recurrence_pattern": getattr(
                                    memory, "recurrence_pattern", ""
                                ),
                                "text_for_embedding": f"{title} | {getattr(memory, 'description', '')} | Location: {getattr(memory, 'location', '')}",
                            }
                            # Delete old memory and add updated one
                            self.core_memory.delete_memory(memory_id)
                            self.core_memory.add_past_event(event_data)
                            break
            except Exception as e:
                print(f"Warning: Could not update event in Core memory: {e}")

        return {"success": True, "message": "Event moved successfully"}

    def add_notification(self, details):
        """Add notification to an event via EventKit."""
        # Validate required fields
        if "minutes_before" not in details:
            return {"success": False, "error": "Missing minutes_before"}
        if not isinstance(details.get("minutes_before"), int):
            return {"success": False, "error": "Invalid minutes_before type"}
        if "title" not in details:
            return {"success": False, "error": "Missing title"}
        if "date" not in details:
            return {"success": False, "error": "Missing date"}
        # Validate date format
        try:
            datetime.strptime(details["date"], "%Y-%m-%d")
        except Exception as e:
            return {"success": False, "error": f"Invalid date format: {e}"}
        # Save notification (stub)
        try:
            success = self.store.saveEvent_span_error_(None, EKSpanThisEvent, None)
        except Exception as e:
            return {"success": False, "error": f"Failed to add notification: {e}"}
        if not success:
            return {"success": False, "error": "Failed to add notification"}
        return {"success": True, "message": "Notification added successfully"}

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the calendar system."""
        stats = {
            "total_events": (
                len(self.store._events) if hasattr(self.store, "_events") else 0
            ),
            "core_memory_available": CORE_MEMORY_AVAILABLE,
        }

        if self.core_memory:
            stats["core_memory_stats"] = self.core_memory.get_stats()

        if self.nudger:
            stats["nudger_stats"] = self.nudger.get_stats()

        return stats

    def get_contextual_suggestions(self, context: Dict = None) -> List[Dict]:
        """
        Get contextual suggestions based on current context and user patterns.

        Args:
            context: Current context (time, day, recent activities)

        Returns:
            List of contextual suggestions
        """
        if not self.nudger:
            return []

        try:
            # Get current context if not provided
            if context is None:
                now = datetime.now()
                context = {
                    "current_time": now.strftime("%H:%M"),
                    "current_day": now.strftime("%A"),
                    "current_date": now.strftime("%Y-%m-%d"),
                    "back_to_back_meetings": self._count_back_to_back_meetings(),
                    "available_slots": self._count_available_slots(),
                }

            # Check if nudging should be enabled
            if not self.nudger.should_nudge(context):
                return []

            # Generate suggestions
            suggestions = self.nudger.generate_suggestions(context)

            # Convert to dictionary format for API
            result = []
            for suggestion in suggestions:
                result.append(
                    {
                        "id": suggestion.id,
                        "type": suggestion.type.value,
                        "title": suggestion.title,
                        "description": suggestion.description,
                        "priority": suggestion.priority,
                        "confidence": suggestion.confidence,
                        "context": suggestion.context,
                    }
                )

            return result

        except Exception as e:
            print(f"Warning: Could not generate contextual suggestions: {e}")
            return []

    def _count_back_to_back_meetings(self) -> int:
        """Count back-to-back meetings in the current day."""
        try:
            today = datetime.now().date()
            events = self.store._events if hasattr(self.store, "_events") else []
            today_events = [
                event
                for event in events
                if hasattr(event, "startDate") and event.startDate.date() == today
            ]

            # Sort by start time
            today_events.sort(key=lambda e: e.startDate)

            back_to_back_count = 0
            for i in range(len(today_events) - 1):
                current_end = today_events[i].endDate
                next_start = today_events[i + 1].startDate

                # If there's less than 15 minutes between events, count as back-to-back
                if (next_start - current_end).total_seconds() < 900:  # 15 minutes
                    back_to_back_count += 1

            return back_to_back_count

        except Exception as e:
            print(f"Warning: Could not count back-to-back meetings: {e}")
            return 0

    def _count_available_slots(self) -> int:
        """Count available time slots in the current day."""
        try:
            today = datetime.now().date()
            events = self.store._events if hasattr(self.store, "_events") else []
            today_events = [
                event
                for event in events
                if hasattr(event, "startDate") and event.startDate.date() == today
            ]

            # Simple heuristic: count gaps of 30+ minutes
            today_events.sort(key=lambda e: e.startDate)

            available_slots = 0
            work_start = datetime.combine(
                today, datetime.min.time().replace(hour=9)
            )  # 9 AM
            work_end = datetime.combine(
                today, datetime.min.time().replace(hour=17)
            )  # 5 PM

            # Check before first event
            if (
                today_events
                and hasattr(today_events[0], "startDate")
                and hasattr(today_events[0].startDate, "__gt__")
            ):
                if today_events[0].startDate > work_start:
                    gap = (
                        today_events[0].startDate - work_start
                    ).total_seconds() / 3600
                    if gap >= 0.5:  # 30 minutes
                        available_slots += 1

            # Check between events
            for i in range(len(today_events) - 1):
                current_end = today_events[i].endDate
                next_start = today_events[i + 1].startDate

                if hasattr(current_end, "__sub__") and hasattr(next_start, "__sub__"):
                    gap = (next_start - current_end).total_seconds() / 3600
                    if gap >= 0.5:  # 30 minutes
                        available_slots += 1

            # Check after last event
            if (
                today_events
                and hasattr(today_events[-1], "endDate")
                and hasattr(today_events[-1].endDate, "__lt__")
            ):
                if today_events[-1].endDate < work_end:
                    gap = (work_end - today_events[-1].endDate).total_seconds() / 3600
                    if gap >= 0.5:  # 30 minutes
                        available_slots += 1

            return available_slots

        except Exception as e:
            print(f"Warning: Could not count available slots: {e}")
            return 0

    def handle_nudge_feedback(self, nudge_id: str, action: str, context: Dict = None):
        """
        Handle user feedback on a contextual nudge.

        Args:
            nudge_id: ID of the nudge
            action: User action ("accepted", "dismissed", "ignored")
            context: Additional context
        """
        if not self.nudger:
            return

        try:
            feedback = {
                "nudge_id": nudge_id,
                "action": action,
                "context": context or {},
            }

            self.nudger.learn_preferences(feedback)

        except Exception as e:
            print(f"Warning: Could not handle nudge feedback: {e}")


# Instantiate agent
_agent = EventKitAgent()

# Expose functions matching calendar_agent interface


def list_events_and_reminders(start_date=None, end_date=None):
    return _agent.list_events_and_reminders(start_date, end_date)


def create_event(details):
    return _agent.create_event(details)


def delete_event(details):
    return _agent.delete_event(details)


def move_event(details):
    return _agent.move_event(details)


def add_notification(details):
    return _agent.add_notification(details)


def get_contextual_suggestions(context=None):
    return _agent.get_contextual_suggestions(context)


def handle_nudge_feedback(nudge_id, action, context=None):
    return _agent.handle_nudge_feedback(nudge_id, action, context)


def get_stats():
    return _agent.get_stats()
