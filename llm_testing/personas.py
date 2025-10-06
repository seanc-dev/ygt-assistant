"""Persona definitions for LLM-to-LLM testing framework."""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class Persona:
    """Represents a test user persona with distinct characteristics."""

    name: str
    traits: List[str]  # e.g., ["busy executive", "health conscious", "family oriented"]
    goals: List[str]  # e.g., ["optimize productivity", "maintain work-life balance"]
    behaviors: List[
        str
    ]  # e.g., ["prefers morning meetings", "avoids back-to-back calls"]
    quirks: List[str]  # e.g., ["forgets to add travel time", "likes 15-minute breaks"]
    communication_style: str  # e.g., "direct", "detailed", "casual"
    tech_savviness: int  # 1-5 scale
    time_preferences: Dict[str, str]  # e.g., {"work_hours": "9-5", "lunch": "12-1"}
    accessibility_needs: List[str]  # e.g., ["low_vision", "neurodivergent", "mobility"]
    language_fluency: str  # e.g., "native", "fluent", "basic", "learning"
    challenge_type: (
        str  # e.g., "standard", "timezone_shifter", "contradictory", "edge_case"
    )

    def __post_init__(self):
        """Set default values after initialization."""
        if self.accessibility_needs is None:
            self.accessibility_needs = []
        if self.time_preferences is None:
            self.time_preferences = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert persona to dictionary."""
        return {
            "name": self.name,
            "traits": self.traits,
            "goals": self.goals,
            "behaviors": self.behaviors,
            "quirks": self.quirks,
            "communication_style": self.communication_style,
            "tech_savviness": self.tech_savviness,
            "time_preferences": self.time_preferences,
            "accessibility_needs": self.accessibility_needs,
            "language_fluency": self.language_fluency,
            "challenge_type": self.challenge_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Persona":
        """Create persona from dictionary."""
        return cls(**data)


# Initial diverse personas
ALEX = Persona(
    name="Alex",
    traits=["busy executive", "tech-savvy", "efficiency-focused"],
    goals=[
        "optimize productivity",
        "maintain professional image",
        "reduce meeting time",
    ],
    behaviors=[
        "prefers morning meetings",
        "avoids back-to-back calls",
        "uses calendar shortcuts",
    ],
    quirks=[
        "forgets to add travel time",
        "likes 15-minute breaks",
        "hates long meetings",
    ],
    communication_style="direct",
    tech_savviness=5,
    time_preferences={"work_hours": "8-6", "lunch": "12-1", "meetings": "9-5"},
    accessibility_needs=[],
    language_fluency="native",
    challenge_type="standard",
)

SAM = Persona(
    name="Sam",
    traits=["creative professional", "flexible schedule", "work-life balance"],
    goals=[
        "maintain creative energy",
        "balance work and personal life",
        "avoid burnout",
    ],
    behaviors=[
        "prefers afternoon creative sessions",
        "takes long breaks",
        "flexible with timing",
    ],
    quirks=[
        "forgets about meetings",
        "likes spontaneous scheduling",
        "needs inspiration time",
    ],
    communication_style="casual",
    tech_savviness=3,
    time_preferences={
        "work_hours": "10-7",
        "creative_time": "2-6",
        "breaks": "flexible",
    },
    accessibility_needs=[],
    language_fluency="native",
    challenge_type="standard",
)

JORDAN = Persona(
    name="Jordan",
    traits=["graduate student", "budget-conscious", "time-constrained"],
    goals=["optimize study time", "balance classes and research", "save money"],
    behaviors=[
        "plans study sessions",
        "avoids expensive activities",
        "uses public transport",
    ],
    quirks=["forgets about deadlines", "needs study reminders", "likes group study"],
    communication_style="detailed",
    tech_savviness=4,
    time_preferences={"study_hours": "9-5", "classes": "varies", "breaks": "30min"},
    accessibility_needs=[],
    language_fluency="native",
    challenge_type="standard",
)

CASEY = Persona(
    name="Casey",
    traits=["working parent", "family-oriented", "time-pressed"],
    goals=["balance work and family", "coordinate childcare", "maintain career"],
    behaviors=[
        "schedules around kids",
        "needs backup plans",
        "communicates with partner",
    ],
    quirks=[
        "forgets about school events",
        "needs family calendar sync",
        "likes early meetings",
    ],
    communication_style="detailed",
    tech_savviness=3,
    time_preferences={"work_hours": "8-4", "family_time": "5-8", "weekends": "family"},
    accessibility_needs=[],
    language_fluency="native",
    challenge_type="standard",
)

TAYLOR = Persona(
    name="Taylor",
    traits=["remote worker", "digital nomad", "timezone-aware"],
    goals=[
        "maintain work-life balance",
        "coordinate across timezones",
        "stay productive",
    ],
    behaviors=[
        "uses timezone tools",
        "schedules flexible hours",
        "communicates clearly",
    ],
    quirks=[
        "forgets timezone differences",
        "needs timezone reminders",
        "likes async work",
    ],
    communication_style="clear",
    tech_savviness=5,
    time_preferences={
        "work_hours": "flexible",
        "timezone": "varies",
        "meetings": "async",
    },
    accessibility_needs=[],
    language_fluency="native",
    challenge_type="timezone_shifter",
)

MORGAN = Persona(
    name="Morgan",
    traits=["low-vision user", "accessibility-focused", "detail-oriented"],
    goals=["maintain independence", "access calendar information", "stay organized"],
    behaviors=[
        "uses screen readers",
        "prefers audio descriptions",
        "needs clear navigation",
    ],
    quirks=[
        "needs detailed descriptions",
        "forgets visual cues",
        "likes voice commands",
    ],
    communication_style="detailed",
    tech_savviness=4,
    time_preferences={
        "work_hours": "9-5",
        "breaks": "regular",
        "meetings": "audio-friendly",
    },
    accessibility_needs=["low_vision"],
    language_fluency="native",
    challenge_type="standard",
)

RILEY = Persona(
    name="Riley",
    traits=["neurodivergent", "ADHD", "structure-needing"],
    goals=["maintain focus", "avoid overwhelm", "stay organized"],
    behaviors=[
        "needs detailed structure",
        "prefers clear instructions",
        "uses reminders",
    ],
    quirks=["gets distracted easily", "needs step-by-step guidance", "likes routine"],
    communication_style="detailed",
    tech_savviness=3,
    time_preferences={
        "work_hours": "9-5",
        "breaks": "frequent",
        "meetings": "structured",
    },
    accessibility_needs=["neurodivergent"],
    language_fluency="native",
    challenge_type="standard",
)

KAI = Persona(
    name="Kai",
    traits=["language learner", "non-native speaker", "learning-focused"],
    goals=["improve English", "understand technical terms", "communicate effectively"],
    behaviors=[
        "asks for clarification",
        "prefers simple language",
        "uses translation tools",
    ],
    quirks=["confuses similar words", "needs technical explanations", "likes examples"],
    communication_style="careful",
    tech_savviness=2,
    time_preferences={
        "study_hours": "flexible",
        "practice_time": "daily",
        "meetings": "prepared",
    },
    accessibility_needs=[],
    language_fluency="learning",
    challenge_type="standard",
)

JORDAN_TRAVELER = Persona(
    name="Jordan (Traveler)",
    traits=["frequent traveler", "timezone-shifter", "adaptable"],
    goals=["maintain productivity", "adapt to timezone changes", "stay connected"],
    behaviors=[
        "changes timezones frequently",
        "uses timezone tools",
        "communicates timezone",
    ],
    quirks=["forgets timezone changes", "needs timezone reminders", "likes local time"],
    communication_style="clear",
    tech_savviness=4,
    time_preferences={
        "work_hours": "varies",
        "timezone": "changes",
        "meetings": "flexible",
    },
    accessibility_needs=[],
    language_fluency="native",
    challenge_type="timezone_shifter",
)

AVERY = Persona(
    name="Avery",
    traits=["contradictory user", "changeable", "testing"],
    goals=["test assistant adaptability", "challenge assumptions", "verify responses"],
    behaviors=[
        "changes preferences mid-conversation",
        "contradicts earlier statements",
        "tests boundaries",
    ],
    quirks=[
        "forgets previous preferences",
        "needs clarification",
        "likes to challenge",
    ],
    communication_style="changeable",
    tech_savviness=3,
    time_preferences={
        "work_hours": "varies",
        "preferences": "changeable",
        "meetings": "flexible",
    },
    accessibility_needs=[],
    language_fluency="native",
    challenge_type="contradictory",
)

# Persona registry
PERSONAS = {
    "alex": ALEX,
    "sam": SAM,
    "jordan": JORDAN,
    "casey": CASEY,
    "taylor": TAYLOR,
    "morgan": MORGAN,
    "riley": RILEY,
    "kai": KAI,
    "jordan_traveler": JORDAN_TRAVELER,
    "avery": AVERY,
}


def get_persona(name: str) -> Persona:
    """Get persona by name."""
    return PERSONAS.get(name.lower())


def get_all_personas() -> List[Persona]:
    """Get all available personas."""
    return list(PERSONAS.values())


def get_personas_by_type(challenge_type: str) -> List[Persona]:
    """Get personas by challenge type."""
    return [p for p in PERSONAS.values() if p.challenge_type == challenge_type]


def get_personas_by_accessibility(accessibility_need: str) -> List[Persona]:
    """Get personas with specific accessibility needs."""
    return [p for p in PERSONAS.values() if accessibility_need in p.accessibility_needs]
