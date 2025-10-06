from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class When(BaseModel):
    """Time window for an intent in ISO-8601 strings with optional timezone."""

    start_iso: Optional[str] = None
    end_iso: Optional[str] = None
    tz: Optional[str] = None


class Participant(BaseModel):
    """Participant metadata for a calendar-related intent."""

    name: Optional[str] = None
    email: Optional[str] = None


class NotesRef(BaseModel):
    """References to external note systems."""

    gdrive_path: Optional[str] = None
    notion_page_id: Optional[str] = None


class SourceIds(BaseModel):
    """Identifiers from upstream sources such as email or external calendars."""

    email_message_id: Optional[str] = None
    thread_id: Optional[str] = None
    external_event_id: Optional[str] = None


class Entities(BaseModel):
    """Canonical entities extracted from natural language for intent execution."""

    title: Optional[str] = None
    when: Optional[When] = None
    participants: List[Participant] = Field(default_factory=list)
    source_ids: Optional[SourceIds] = None
    notes_ref: Optional[NotesRef] = None


class Intent(BaseModel):
    """Canonical intent for LLM-driven actions and downstream services."""

    action: str
    entities: Entities = Field(default_factory=Entities)
    confidence: float = 0.0


