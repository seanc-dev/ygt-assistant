"""Tests for prompt definitions and templates."""

import pytest
from llm_testing.prompts import (
    TestPrompt,
    PromptTemplate,
    get_prompt_template,
    get_predefined_prompts,
    generate_fuzz_prompts,
    get_prompts_by_category,
    get_prompts_by_difficulty,
)


class TestTestPrompt:
    """Test TestPrompt functionality."""

    def test_prompt_creation(self):
        """Test creating a test prompt."""
        prompt = TestPrompt(
            prompt="Test prompt",
            context={"test": "value"},
            expected_actions=["action1", "action2"],
            expected_qualities=["clear", "helpful"],
            difficulty="medium",
            category="scheduling",
            template_vars={"var1": "value1"},
            failure_mode="standard",
        )

        assert prompt.prompt == "Test prompt"
        assert prompt.context == {"test": "value"}
        assert prompt.expected_actions == ["action1", "action2"]
        assert prompt.expected_qualities == ["clear", "helpful"]
        assert prompt.difficulty == "medium"
        assert prompt.category == "scheduling"
        assert prompt.template_vars == {"var1": "value1"}
        assert prompt.failure_mode == "standard"

    def test_prompt_defaults(self):
        """Test prompt creation with defaults."""
        prompt = TestPrompt(
            prompt="Test prompt",
            context={},
            expected_actions=[],
            expected_qualities=[],
            difficulty="easy",
            category="scheduling",
            template_vars=None,
            failure_mode="standard",
        )

        assert prompt.template_vars == {}

    def test_prompt_serialization(self):
        """Test prompt serialization and deserialization."""
        original = TestPrompt(
            prompt="Test prompt",
            context={"key": "value"},
            expected_actions=["action1"],
            expected_qualities=["clear"],
            difficulty="hard",
            category="optimization",
            template_vars={"var": "val"},
            failure_mode="edge_case",
        )

        data = original.to_dict()
        restored = TestPrompt.from_dict(data)

        assert restored.prompt == original.prompt
        assert restored.context == original.context
        assert restored.expected_actions == original.expected_actions
        assert restored.expected_qualities == original.expected_qualities
        assert restored.difficulty == original.difficulty
        assert restored.category == original.category
        assert restored.template_vars == original.template_vars
        assert restored.failure_mode == original.failure_mode


class TestPromptTemplate:
    """Test PromptTemplate functionality."""

    def test_template_creation(self):
        """Test creating a prompt template."""
        template = PromptTemplate(
            "Schedule a meeting with {contact} on {date}",
            {"contact": ["John", "Sarah"], "date": ["tomorrow", "next week"]},
        )

        assert template.template == "Schedule a meeting with {contact} on {date}"
        assert template.slot_fillers == {
            "contact": ["John", "Sarah"],
            "date": ["tomorrow", "next week"],
        }

    def test_generate_variations(self):
        """Test generating prompt variations."""
        template = PromptTemplate(
            "Schedule a meeting with {contact} on {date}",
            {"contact": ["John", "Sarah"], "date": ["tomorrow", "next week"]},
        )

        variations = template.generate_variations(3)
        assert len(variations) == 3

        for variation in variations:
            assert "Schedule a meeting with" in variation.prompt
            assert variation.context
            assert "contact" in variation.context
            assert "date" in variation.context
            assert variation.difficulty == "medium"  # Default
            assert variation.category == "scheduling"  # Default
            assert variation.failure_mode == "standard"  # Default

    def test_template_with_empty_slots(self):
        """Test template with empty slot fillers."""
        template = PromptTemplate("Simple prompt", {})

        variations = template.generate_variations(2)
        assert len(variations) == 2

        for variation in variations:
            assert variation.prompt == "Simple prompt"
            assert variation.context == {}


class TestPromptFunctions:
    """Test prompt utility functions."""

    def test_get_prompt_template(self):
        """Test getting prompt template by name."""
        template = get_prompt_template("basic_scheduling")
        assert template is not None
        assert "Schedule a meeting with" in template.template

        # Test non-existent template
        template = get_prompt_template("nonexistent")
        assert template is None

    def test_get_predefined_prompts(self):
        """Test getting predefined prompts for scenarios."""
        prompts = get_predefined_prompts("morning_routine")
        assert len(prompts) > 0
        assert "morning routine" in prompts[0].prompt.lower()

        # Test non-existent scenario
        prompts = get_predefined_prompts("nonexistent")
        assert len(prompts) == 0

    def test_generate_fuzz_prompts(self):
        """Test generating fuzz prompts."""
        prompts = generate_fuzz_prompts("basic_scheduling", 5)
        assert len(prompts) == 5

        for prompt in prompts:
            assert "Schedule a meeting with" in prompt.prompt
            assert prompt.context
            assert "contact" in prompt.context
            assert "date" in prompt.context
            assert "time" in prompt.context

        # Test non-existent template
        prompts = generate_fuzz_prompts("nonexistent", 5)
        assert len(prompts) == 0

    def test_get_prompts_by_category(self):
        """Test getting prompts by category."""
        optimization_prompts = get_prompts_by_category("optimization")
        assert len(optimization_prompts) > 0

        accessibility_prompts = get_prompts_by_category("accessibility")
        assert len(accessibility_prompts) > 0

        # Test non-existent category
        none_prompts = get_prompts_by_category("nonexistent")
        assert len(none_prompts) == 0

    def test_get_prompts_by_difficulty(self):
        """Test getting prompts by difficulty."""
        easy_prompts = get_prompts_by_difficulty("easy")
        assert len(easy_prompts) > 0

        hard_prompts = get_prompts_by_difficulty("hard")
        assert len(hard_prompts) > 0

        # Test non-existent difficulty
        none_prompts = get_prompts_by_difficulty("nonexistent")
        assert len(none_prompts) == 0

    def test_template_diversity(self):
        """Test that we have diverse template types."""
        templates = [
            "basic_scheduling",
            "ambiguous_scheduling",
            "complex_scheduling",
            "invalid_input",
            "accessibility_request",
            "language_learning",
            "error_recovery",
            "optimization_request",
            "timezone_challenge",
            "contradictory_request",
        ]

        for template_name in templates:
            template = get_prompt_template(template_name)
            assert template is not None, f"Template {template_name} should exist"

    def test_predefined_prompts_diversity(self):
        """Test that we have diverse predefined prompts."""
        scenarios = [
            "morning_routine",
            "travel_planning",
            "family_coordination",
            "study_schedule",
            "creative_flow",
            "accessible_scheduling",
            "adhd_structure",
            "language_learning",
        ]

        for scenario in scenarios:
            prompts = get_predefined_prompts(scenario)
            assert len(prompts) > 0, f"Scenario {scenario} should have prompts"

    def test_failure_modes(self):
        """Test that we have various failure modes."""
        prompts = get_predefined_prompts("morning_routine")
        assert len(prompts) > 0

        # Check that we have different failure modes
        failure_modes = set(p.failure_mode for p in prompts)
        assert "standard" in failure_modes

        # Check invalid input prompts
        invalid_prompts = get_prompts_by_category("edge_cases")
        # Note: We don't have edge_cases category yet, but the function should handle it
        assert isinstance(invalid_prompts, list)
