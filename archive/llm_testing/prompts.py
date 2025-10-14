"""Test prompt definitions and template system for LLM-to-LLM testing framework."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import random
import string


@dataclass
class TestPrompt:
    """Represents a test prompt with expected outcomes."""

    prompt: str
    context: Dict[str, Any]
    expected_actions: List[str]
    expected_qualities: List[str]  # e.g., ["clear", "helpful", "efficient"]
    difficulty: str  # "easy", "medium", "hard"
    category: str  # "scheduling", "conflict_resolution", "optimization", "edge_cases"
    template_vars: Dict[str, Any]  # For dynamic prompt generation
    failure_mode: str  # e.g., "invalid_input", "ambiguous", "edge_case"

    def __post_init__(self):
        """Set default values after initialization."""
        if self.template_vars is None:
            self.template_vars = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert prompt to dictionary."""
        return {
            "prompt": self.prompt,
            "context": self.context,
            "expected_actions": self.expected_actions,
            "expected_qualities": self.expected_qualities,
            "difficulty": self.difficulty,
            "category": self.category,
            "template_vars": self.template_vars,
            "failure_mode": self.failure_mode,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestPrompt":
        """Create prompt from dictionary."""
        return cls(**data)


class PromptTemplate:
    """Template system for generating dynamic test prompts."""

    def __init__(self, template: str, slot_fillers: Dict[str, List[str]]):
        """Initialize template with slot fillers."""
        self.template = template
        self.slot_fillers = slot_fillers

    def generate_variations(self, count: int = 5) -> List[TestPrompt]:
        """Generate multiple prompt variations with different slot fillers."""
        variations = []

        for i in range(count):
            # Fill slots randomly
            filled_template = self.template
            context = {}

            for slot, options in self.slot_fillers.items():
                if options:
                    value = random.choice(options)
                    filled_template = filled_template.replace(f"{{{slot}}}", value)
                    context[slot] = value

            # Create test prompt
            prompt = TestPrompt(
                prompt=filled_template,
                context=context,
                expected_actions=[],  # Will be filled by scenario
                expected_qualities=[],  # Will be filled by scenario
                difficulty="medium",  # Default, can be overridden
                category="scheduling",  # Default, can be overridden
                template_vars=context,
                failure_mode="standard",
            )
            variations.append(prompt)

        return variations


# Predefined prompt templates
SCHEDULING_TEMPLATES = {
    "basic_scheduling": PromptTemplate(
        "Schedule a meeting with {contact} on {date} at {time}",
        {
            "contact": ["John", "Sarah", "Mike", "Lisa", "David"],
            "date": ["tomorrow", "next Monday", "this Friday", "next week"],
            "time": ["2pm", "10am", "3:30pm", "9am", "4pm"],
        },
    ),
    "ambiguous_scheduling": PromptTemplate(
        "I need to meet with {contact} sometime {timeframe}",
        {
            "contact": ["the team", "my manager", "the client", "the stakeholders"],
            "timeframe": ["this week", "next week", "soon", "when convenient"],
        },
    ),
    "complex_scheduling": PromptTemplate(
        "Find the best time for a {duration} {meeting_type} that works for {participants}",
        {
            "duration": ["1-hour", "2-hour", "30-minute", "half-day"],
            "meeting_type": ["workshop", "review", "planning session", "brainstorming"],
            "participants": ["everyone", "the team", "stakeholders", "management"],
        },
    ),
    "invalid_input": PromptTemplate(
        "Schedule a meeting with {contact} {invalid_time}",
        {
            "contact": ["John", "Sarah", "Mike"],
            "invalid_time": ["yesterday at 3pm", "last week", "in the past", "never"],
        },
    ),
    "accessibility_request": PromptTemplate(
        "Can you {accessibility_action} my schedule?",
        {
            "accessibility_action": [
                "describe in detail",
                "read aloud",
                "explain step by step",
                "summarize clearly",
            ]
        },
    ),
    "language_learning": PromptTemplate(
        "What does '{term}' mean in calendar terms?",
        {"term": ["recurring", "timezone", "duration", "conflict", "availability"]},
    ),
    "error_recovery": PromptTemplate(
        "I made a mistake, can you {recovery_action} that meeting?",
        {
            "recovery_action": [
                "fix the time",
                "change the date",
                "update the location",
                "cancel it",
            ]
        },
    ),
    "optimization_request": PromptTemplate(
        "I'm feeling {emotion}, can you help me {optimization_action}?",
        {
            "emotion": ["overwhelmed", "stressed", "confused", "busy"],
            "optimization_action": [
                "organize my week",
                "find better times",
                "reduce conflicts",
                "optimize my schedule",
            ],
        },
    ),
    "timezone_challenge": PromptTemplate(
        "I'm now in {timezone}, can you {timezone_action}?",
        {
            "timezone": ["PST", "EST", "GMT", "JST", "AEST"],
            "timezone_action": [
                "adjust my meetings",
                "update my schedule",
                "find local times",
                "coordinate with my team",
            ],
        },
    ),
    "contradictory_request": PromptTemplate(
        "Actually, I changed my mind. {contradiction}",
        {
            "contradiction": [
                "I want the meeting earlier, not later",
                "I prefer afternoon, not morning",
                "I need it shorter, not longer",
                "I want it online, not in person",
            ]
        },
    ),
}

# Predefined test prompts for specific scenarios
PREDEFINED_PROMPTS = {
    "morning_routine": [
        TestPrompt(
            prompt="Help me establish a consistent morning routine",
            context={"persona": "alex", "goal": "productivity"},
            expected_actions=["create recurring events", "suggest optimal times"],
            expected_qualities=["clear", "helpful", "structured"],
            difficulty="medium",
            category="optimization",
            template_vars={},
            failure_mode="standard",
        )
    ],
    "travel_planning": [
        TestPrompt(
            prompt="I'm traveling to a different timezone, help me adjust my schedule",
            context={"persona": "taylor", "timezone_change": True},
            expected_actions=[
                "update times",
                "consider timezone",
                "notify participants",
            ],
            expected_qualities=["clear", "helpful", "timezone-aware"],
            difficulty="hard",
            category="timezone",
            template_vars={},
            failure_mode="standard",
        )
    ],
    "family_coordination": [
        TestPrompt(
            prompt="I need to coordinate my work schedule with my family's needs",
            context={"persona": "casey", "family_context": True},
            expected_actions=[
                "consider family time",
                "balance work/family",
                "create family events",
            ],
            expected_qualities=["understanding", "helpful", "family-oriented"],
            difficulty="medium",
            category="optimization",
            template_vars={},
            failure_mode="standard",
        )
    ],
    "study_schedule": [
        TestPrompt(
            prompt="Help me optimize my study time around my classes",
            context={"persona": "jordan", "academic_context": True},
            expected_actions=[
                "analyze class schedule",
                "suggest study blocks",
                "avoid conflicts",
            ],
            expected_qualities=["academic-focused", "helpful", "efficient"],
            difficulty="medium",
            category="optimization",
            template_vars={},
            failure_mode="standard",
        )
    ],
    "creative_flow": [
        TestPrompt(
            prompt="I want to maintain my creative energy throughout the day",
            context={"persona": "sam", "creative_context": True},
            expected_actions=[
                "suggest creative time",
                "avoid burnout",
                "balance work/creativity",
            ],
            expected_qualities=["creative-friendly", "understanding", "flexible"],
            difficulty="medium",
            category="optimization",
            template_vars={},
            failure_mode="standard",
        )
    ],
    "accessible_scheduling": [
        TestPrompt(
            prompt="Can you describe my schedule in detail so I can understand it clearly?",
            context={"persona": "morgan", "accessibility": "low_vision"},
            expected_actions=[
                "provide detailed descriptions",
                "use clear language",
                "avoid visual references",
            ],
            expected_qualities=["accessible", "clear", "detailed"],
            difficulty="medium",
            category="accessibility",
            template_vars={},
            failure_mode="standard",
        )
    ],
    "adhd_structure": [
        TestPrompt(
            prompt="I need very detailed, structured scheduling to stay focused",
            context={"persona": "riley", "accessibility": "neurodivergent"},
            expected_actions=[
                "provide step-by-step guidance",
                "create detailed structure",
                "use clear reminders",
            ],
            expected_qualities=["structured", "detailed", "supportive"],
            difficulty="medium",
            category="accessibility",
            template_vars={},
            failure_mode="standard",
        )
    ],
    "language_learning": [
        TestPrompt(
            prompt="What does 'recurring' mean in calendar terms?",
            context={"persona": "kai", "language_context": "learning"},
            expected_actions=[
                "explain technical terms",
                "provide examples",
                "use simple language",
            ],
            expected_qualities=["educational", "clear", "patient"],
            difficulty="easy",
            category="language",
            template_vars={},
            failure_mode="standard",
        )
    ],
}


def get_prompt_template(template_name: str) -> Optional[PromptTemplate]:
    """Get a prompt template by name."""
    return SCHEDULING_TEMPLATES.get(template_name)


def get_predefined_prompts(scenario_name: str) -> List[TestPrompt]:
    """Get predefined prompts for a scenario."""
    return PREDEFINED_PROMPTS.get(scenario_name, [])


def generate_fuzz_prompts(template_name: str, count: int = 10) -> List[TestPrompt]:
    """Generate fuzz test prompts using a template."""
    template = get_prompt_template(template_name)
    if template:
        return template.generate_variations(count)
    return []


def get_prompts_by_category(category: str) -> List[TestPrompt]:
    """Get all prompts in a specific category."""
    all_prompts = []
    for prompts in PREDEFINED_PROMPTS.values():
        all_prompts.extend(prompts)

    return [p for p in all_prompts if p.category == category]


def get_prompts_by_difficulty(difficulty: str) -> List[TestPrompt]:
    """Get all prompts of a specific difficulty."""
    all_prompts = []
    for prompts in PREDEFINED_PROMPTS.values():
        all_prompts.extend(prompts)

    return [p for p in all_prompts if p.difficulty == difficulty]
