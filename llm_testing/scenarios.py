"""Scenario definitions for LLM-to-LLM testing framework."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from .personas import Persona, get_persona
from .prompts import TestPrompt, get_predefined_prompts


@dataclass
class ExpectedBehavior:
    """Represents an expected behavior for a scenario."""

    description: str
    category: str  # e.g., "scheduling", "communication", "error_handling"
    importance: str  # "critical", "important", "nice_to_have"
    success_criteria: List[str]


@dataclass
class SuccessCriterion:
    """Represents a success criterion for a scenario."""

    description: str
    measurable: bool
    threshold: Optional[float] = None
    category: str = "general"


@dataclass
class Scenario:
    """Represents a test scenario with persona, goals, and evaluation criteria."""

    name: str
    persona: Persona
    goals: List[str]
    initial_context: Dict[str, Any]
    test_prompts: List[TestPrompt]
    expected_behaviors: List[ExpectedBehavior]
    success_criteria: List[SuccessCriterion]
    difficulty: str  # "easy", "medium", "hard"
    category: str  # "scheduling", "conflict_resolution", "optimization", "edge_cases"
    ground_truth: Dict[str, Any]  # Golden transcript for deterministic reference
    version: str  # Scenario version for tracking changes

    def __post_init__(self):
        """Set default values after initialization."""
        if self.expected_behaviors is None:
            self.expected_behaviors = []
        if self.success_criteria is None:
            self.success_criteria = []
        if self.ground_truth is None:
            self.ground_truth = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario to dictionary."""
        return {
            "name": self.name,
            "persona": self.persona.to_dict(),
            "goals": self.goals,
            "initial_context": self.initial_context,
            "test_prompts": [p.to_dict() for p in self.test_prompts],
            "expected_behaviors": [b.__dict__ for b in self.expected_behaviors],
            "success_criteria": [c.__dict__ for c in self.success_criteria],
            "difficulty": self.difficulty,
            "category": self.category,
            "ground_truth": self.ground_truth,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scenario":
        """Create scenario from dictionary."""
        # Reconstruct persona
        persona_data = data["persona"]
        persona = Persona.from_dict(persona_data)

        # Reconstruct test prompts
        prompts_data = data["test_prompts"]
        test_prompts = [TestPrompt.from_dict(p) for p in prompts_data]

        # Reconstruct expected behaviors
        behaviors_data = data["expected_behaviors"]
        expected_behaviors = [ExpectedBehavior(**b) for b in behaviors_data]

        # Reconstruct success criteria
        criteria_data = data["success_criteria"]
        success_criteria = [SuccessCriterion(**c) for c in criteria_data]

        return cls(
            name=data["name"],
            persona=persona,
            goals=data["goals"],
            initial_context=data["initial_context"],
            test_prompts=test_prompts,
            expected_behaviors=expected_behaviors,
            success_criteria=success_criteria,
            difficulty=data["difficulty"],
            category=data["category"],
            ground_truth=data["ground_truth"],
            version=data["version"],
        )


# Basic scenarios
MORNING_ROUTINE_SCENARIO = Scenario(
    name="Morning Routine Setup",
    persona=get_persona("alex"),
    goals=[
        "establish consistent morning routine",
        "optimize productivity",
        "reduce decision fatigue",
    ],
    initial_context={
        "current_schedule": "inconsistent",
        "work_hours": "8-6",
        "preferences": ["morning person", "efficiency-focused"],
    },
    test_prompts=get_predefined_prompts("morning_routine"),
    expected_behaviors=[
        ExpectedBehavior(
            description="Create recurring morning events",
            category="scheduling",
            importance="critical",
            success_criteria=["suggests specific times", "creates recurring events"],
        ),
        ExpectedBehavior(
            description="Consider productivity optimization",
            category="optimization",
            importance="important",
            success_criteria=["suggests optimal times", "considers work patterns"],
        ),
    ],
    success_criteria=[
        SuccessCriterion(
            description="Assistant creates morning routine events",
            measurable=True,
            threshold=0.8,
            category="scheduling",
        ),
        SuccessCriterion(
            description="Assistant considers productivity factors",
            measurable=True,
            threshold=0.7,
            category="optimization",
        ),
    ],
    difficulty="medium",
    category="optimization",
    ground_truth={
        "expected_response": "I'll help you establish a consistent morning routine. Let me create some recurring events...",
        "expected_actions": ["create_recurring_event", "suggest_optimal_times"],
        "key_phrases": ["morning routine", "consistent", "productive"],
    },
    version="1.0",
)

TRAVEL_PLANNING_SCENARIO = Scenario(
    name="Travel Planning",
    persona=get_persona("taylor"),
    goals=[
        "adjust schedule for timezone change",
        "maintain productivity",
        "coordinate with team",
    ],
    initial_context={
        "timezone_change": True,
        "destination": "PST",
        "current_timezone": "EST",
        "team_coordination": True,
    },
    test_prompts=get_predefined_prompts("travel_planning"),
    expected_behaviors=[
        ExpectedBehavior(
            description="Update meeting times for timezone",
            category="timezone",
            importance="critical",
            success_criteria=["adjusts times", "considers timezone difference"],
        ),
        ExpectedBehavior(
            description="Notify team of changes",
            category="communication",
            importance="important",
            success_criteria=["suggests notifications", "considers team impact"],
        ),
    ],
    success_criteria=[
        SuccessCriterion(
            description="Assistant adjusts times for timezone",
            measurable=True,
            threshold=0.9,
            category="timezone",
        ),
        SuccessCriterion(
            description="Assistant considers team coordination",
            measurable=True,
            threshold=0.7,
            category="communication",
        ),
    ],
    difficulty="hard",
    category="timezone",
    ground_truth={
        "expected_response": "I'll help you adjust your schedule for the timezone change...",
        "expected_actions": ["update_meeting_times", "notify_participants"],
        "key_phrases": ["timezone", "adjust", "coordinate"],
    },
    version="1.0",
)

FAMILY_COORDINATION_SCENARIO = Scenario(
    name="Family Coordination",
    persona=get_persona("casey"),
    goals=["balance work and family", "coordinate childcare", "maintain career"],
    initial_context={
        "family_context": True,
        "children": ["school age", "toddler"],
        "work_schedule": "flexible",
        "partner_schedule": "9-5",
    },
    test_prompts=get_predefined_prompts("family_coordination"),
    expected_behaviors=[
        ExpectedBehavior(
            description="Consider family time in scheduling",
            category="scheduling",
            importance="critical",
            success_criteria=["considers family time", "balances work/family"],
        ),
        ExpectedBehavior(
            description="Create family events",
            category="scheduling",
            importance="important",
            success_criteria=["suggests family events", "considers childcare"],
        ),
    ],
    success_criteria=[
        SuccessCriterion(
            description="Assistant considers family needs",
            measurable=True,
            threshold=0.8,
            category="scheduling",
        ),
        SuccessCriterion(
            description="Assistant suggests family-friendly scheduling",
            measurable=True,
            threshold=0.7,
            category="optimization",
        ),
    ],
    difficulty="medium",
    category="optimization",
    ground_truth={
        "expected_response": "I'll help you coordinate your work schedule with your family's needs...",
        "expected_actions": ["consider_family_time", "create_family_events"],
        "key_phrases": ["family", "balance", "coordinate"],
    },
    version="1.0",
)

STUDY_SCHEDULE_SCENARIO = Scenario(
    name="Study Schedule Optimization",
    persona=get_persona("jordan"),
    goals=["optimize study time", "balance classes and research", "avoid conflicts"],
    initial_context={
        "academic_context": True,
        "classes": ["morning", "afternoon"],
        "research_time": "flexible",
        "study_preferences": ["quiet", "focused"],
    },
    test_prompts=get_predefined_prompts("study_schedule"),
    expected_behaviors=[
        ExpectedBehavior(
            description="Analyze class schedule for study blocks",
            category="optimization",
            importance="critical",
            success_criteria=["identifies study blocks", "avoids class conflicts"],
        ),
        ExpectedBehavior(
            description="Suggest optimal study times",
            category="optimization",
            importance="important",
            success_criteria=["suggests optimal times", "considers preferences"],
        ),
    ],
    success_criteria=[
        SuccessCriterion(
            description="Assistant identifies study opportunities",
            measurable=True,
            threshold=0.8,
            category="optimization",
        ),
        SuccessCriterion(
            description="Assistant avoids scheduling conflicts",
            measurable=True,
            threshold=0.9,
            category="scheduling",
        ),
    ],
    difficulty="medium",
    category="optimization",
    ground_truth={
        "expected_response": "I'll help you optimize your study time around your classes...",
        "expected_actions": ["analyze_schedule", "suggest_study_blocks"],
        "key_phrases": ["study", "optimize", "classes"],
    },
    version="1.0",
)

CREATIVE_FLOW_SCENARIO = Scenario(
    name="Creative Flow Maintenance",
    persona=get_persona("sam"),
    goals=["maintain creative energy", "avoid burnout", "balance work and creativity"],
    initial_context={
        "creative_context": True,
        "creative_energy": "afternoon",
        "work_style": "flexible",
        "burnout_risk": "medium",
    },
    test_prompts=get_predefined_prompts("creative_flow"),
    expected_behaviors=[
        ExpectedBehavior(
            description="Suggest creative time blocks",
            category="optimization",
            importance="critical",
            success_criteria=["suggests creative time", "considers energy levels"],
        ),
        ExpectedBehavior(
            description="Avoid burnout through scheduling",
            category="optimization",
            importance="important",
            success_criteria=["prevents overwork", "suggests breaks"],
        ),
    ],
    success_criteria=[
        SuccessCriterion(
            description="Assistant suggests creative time",
            measurable=True,
            threshold=0.8,
            category="optimization",
        ),
        SuccessCriterion(
            description="Assistant considers burnout prevention",
            measurable=True,
            threshold=0.7,
            category="wellness",
        ),
    ],
    difficulty="medium",
    category="optimization",
    ground_truth={
        "expected_response": "I'll help you maintain your creative energy throughout the day...",
        "expected_actions": ["suggest_creative_time", "prevent_burnout"],
        "key_phrases": ["creative", "energy", "balance"],
    },
    version="1.0",
)

ACCESSIBLE_SCHEDULING_SCENARIO = Scenario(
    name="Accessible Scheduling",
    persona=get_persona("morgan"),
    goals=["access calendar information", "maintain independence", "stay organized"],
    initial_context={
        "accessibility": "low_vision",
        "preferred_format": "audio",
        "navigation_needs": "clear",
        "independence": "high",
    },
    test_prompts=get_predefined_prompts("accessible_scheduling"),
    expected_behaviors=[
        ExpectedBehavior(
            description="Provide detailed descriptions",
            category="accessibility",
            importance="critical",
            success_criteria=["uses clear language", "avoids visual references"],
        ),
        ExpectedBehavior(
            description="Consider accessibility needs",
            category="accessibility",
            importance="important",
            success_criteria=["adapts to needs", "provides alternatives"],
        ),
    ],
    success_criteria=[
        SuccessCriterion(
            description="Assistant provides accessible descriptions",
            measurable=True,
            threshold=0.9,
            category="accessibility",
        ),
        SuccessCriterion(
            description="Assistant avoids visual-only references",
            measurable=True,
            threshold=0.8,
            category="accessibility",
        ),
    ],
    difficulty="medium",
    category="accessibility",
    ground_truth={
        "expected_response": "I'll describe your schedule in detail so you can understand it clearly...",
        "expected_actions": ["describe_schedule", "use_clear_language"],
        "key_phrases": ["describe", "detail", "clear"],
    },
    version="1.0",
)

ADHD_STRUCTURE_SCENARIO = Scenario(
    name="ADHD Structure Support",
    persona=get_persona("riley"),
    goals=["maintain focus", "avoid overwhelm", "stay organized"],
    initial_context={
        "accessibility": "neurodivergent",
        "focus_needs": "structured",
        "overwhelm_risk": "high",
        "preferred_format": "step_by_step",
    },
    test_prompts=get_predefined_prompts("adhd_structure"),
    expected_behaviors=[
        ExpectedBehavior(
            description="Provide step-by-step guidance",
            category="accessibility",
            importance="critical",
            success_criteria=["gives clear steps", "avoids overwhelm"],
        ),
        ExpectedBehavior(
            description="Create structured reminders",
            category="scheduling",
            importance="important",
            success_criteria=["suggests reminders", "creates structure"],
        ),
    ],
    success_criteria=[
        SuccessCriterion(
            description="Assistant provides structured guidance",
            measurable=True,
            threshold=0.9,
            category="accessibility",
        ),
        SuccessCriterion(
            description="Assistant prevents overwhelm",
            measurable=True,
            threshold=0.8,
            category="wellness",
        ),
    ],
    difficulty="medium",
    category="accessibility",
    ground_truth={
        "expected_response": "I'll help you create very detailed, structured scheduling to stay focused...",
        "expected_actions": ["provide_steps", "create_structure"],
        "key_phrases": ["detailed", "structured", "focused"],
    },
    version="1.0",
)

LANGUAGE_LEARNING_SCENARIO = Scenario(
    name="Language Learning Support",
    persona=get_persona("kai"),
    goals=["understand technical terms", "improve English", "communicate effectively"],
    initial_context={
        "language_context": "learning",
        "technical_terms": "confusing",
        "preferred_style": "simple",
        "learning_level": "intermediate",
    },
    test_prompts=get_predefined_prompts("language_learning"),
    expected_behaviors=[
        ExpectedBehavior(
            description="Explain technical terms clearly",
            category="language",
            importance="critical",
            success_criteria=["uses simple language", "provides examples"],
        ),
        ExpectedBehavior(
            description="Be patient and educational",
            category="communication",
            importance="important",
            success_criteria=["shows patience", "encourages learning"],
        ),
    ],
    success_criteria=[
        SuccessCriterion(
            description="Assistant explains terms clearly",
            measurable=True,
            threshold=0.8,
            category="language",
        ),
        SuccessCriterion(
            description="Assistant uses appropriate language level",
            measurable=True,
            threshold=0.9,
            category="communication",
        ),
    ],
    difficulty="easy",
    category="language",
    ground_truth={
        "expected_response": "Let me explain what 'recurring' means in calendar terms...",
        "expected_actions": ["explain_terms", "provide_examples"],
        "key_phrases": ["explain", "means", "example"],
    },
    version="1.0",
)

# Scenario registry
SCENARIOS = {
    "morning_routine": MORNING_ROUTINE_SCENARIO,
    "travel_planning": TRAVEL_PLANNING_SCENARIO,
    "family_coordination": FAMILY_COORDINATION_SCENARIO,
    "study_schedule": STUDY_SCHEDULE_SCENARIO,
    "creative_flow": CREATIVE_FLOW_SCENARIO,
    "accessible_scheduling": ACCESSIBLE_SCHEDULING_SCENARIO,
    "adhd_structure": ADHD_STRUCTURE_SCENARIO,
    "language_learning": LANGUAGE_LEARNING_SCENARIO,
}


def get_scenario(name: str) -> Optional[Scenario]:
    """Get scenario by name."""
    return SCENARIOS.get(name.lower())


def get_all_scenarios() -> List[Scenario]:
    """Get all available scenarios."""
    return list(SCENARIOS.values())


def get_scenarios_by_category(category: str) -> List[Scenario]:
    """Get scenarios by category."""
    return [s for s in SCENARIOS.values() if s.category == category]


def get_scenarios_by_difficulty(difficulty: str) -> List[Scenario]:
    """Get scenarios by difficulty."""
    return [s for s in SCENARIOS.values() if s.difficulty == difficulty]


def get_scenarios_by_persona(persona_name: str) -> List[Scenario]:
    """Get scenarios for a specific persona."""
    return [
        s for s in SCENARIOS.values() if s.persona.name.lower() == persona_name.lower()
    ]
