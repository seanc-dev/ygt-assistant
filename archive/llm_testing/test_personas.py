"""Tests for persona definitions."""

import pytest
from llm_testing.personas import (
    Persona,
    get_persona,
    get_all_personas,
    get_personas_by_type,
    get_personas_by_accessibility,
)


class TestPersonas:
    """Test persona functionality."""

    def test_persona_creation(self):
        """Test creating a persona with all fields."""
        persona = Persona(
            name="Test User",
            traits=["test trait"],
            goals=["test goal"],
            behaviors=["test behavior"],
            quirks=["test quirk"],
            communication_style="test",
            tech_savviness=3,
            time_preferences={"work": "9-5"},
            accessibility_needs=["test_need"],
            language_fluency="native",
            challenge_type="standard",
        )

        assert persona.name == "Test User"
        assert persona.traits == ["test trait"]
        assert persona.accessibility_needs == ["test_need"]
        assert persona.time_preferences == {"work": "9-5"}

    def test_persona_defaults(self):
        """Test persona creation with defaults."""
        persona = Persona(
            name="Test User",
            traits=[],
            goals=[],
            behaviors=[],
            quirks=[],
            communication_style="test",
            tech_savviness=3,
            time_preferences={},
            accessibility_needs=None,
            language_fluency="native",
            challenge_type="standard",
        )

        assert persona.accessibility_needs == []
        assert persona.time_preferences == {}

    def test_persona_serialization(self):
        """Test persona serialization and deserialization."""
        original = Persona(
            name="Test User",
            traits=["trait1", "trait2"],
            goals=["goal1"],
            behaviors=["behavior1"],
            quirks=["quirk1"],
            communication_style="direct",
            tech_savviness=4,
            time_preferences={"work": "9-5"},
            accessibility_needs=["low_vision"],
            language_fluency="native",
            challenge_type="standard",
        )

        data = original.to_dict()
        restored = Persona.from_dict(data)

        assert restored.name == original.name
        assert restored.traits == original.traits
        assert restored.accessibility_needs == original.accessibility_needs
        assert restored.time_preferences == original.time_preferences

    def test_get_persona(self):
        """Test getting persona by name."""
        persona = get_persona("alex")
        assert persona is not None
        assert persona.name == "Alex"

        # Test case insensitive
        persona = get_persona("ALEX")
        assert persona is not None
        assert persona.name == "Alex"

        # Test non-existent persona
        persona = get_persona("nonexistent")
        assert persona is None

    def test_get_all_personas(self):
        """Test getting all personas."""
        personas = get_all_personas()
        assert len(personas) == 10  # We have 10 personas defined

        names = [p.name for p in personas]
        assert "Alex" in names
        assert "Morgan" in names
        assert "Avery" in names

    def test_get_personas_by_type(self):
        """Test getting personas by challenge type."""
        standard_personas = get_personas_by_type("standard")
        assert len(standard_personas) > 0

        timezone_personas = get_personas_by_type("timezone_shifter")
        assert len(timezone_personas) > 0

        contradictory_personas = get_personas_by_type("contradictory")
        assert len(contradictory_personas) > 0

    def test_get_personas_by_accessibility(self):
        """Test getting personas by accessibility needs."""
        low_vision_personas = get_personas_by_accessibility("low_vision")
        assert len(low_vision_personas) > 0

        neurodivergent_personas = get_personas_by_accessibility("neurodivergent")
        assert len(neurodivergent_personas) > 0

        # Test non-existent accessibility need
        none_personas = get_personas_by_accessibility("nonexistent")
        assert len(none_personas) == 0

    def test_diverse_personas(self):
        """Test that we have diverse personas."""
        personas = get_all_personas()

        # Check for accessibility diversity
        accessibility_personas = [p for p in personas if p.accessibility_needs]
        assert len(accessibility_personas) > 0

        # Check for challenge diversity
        challenge_types = set(p.challenge_type for p in personas)
        assert "standard" in challenge_types
        assert "timezone_shifter" in challenge_types
        assert "contradictory" in challenge_types

        # Check for language diversity
        language_levels = set(p.language_fluency for p in personas)
        assert "native" in language_levels
        assert "learning" in language_levels

    def test_persona_characteristics(self):
        """Test that personas have appropriate characteristics."""
        alex = get_persona("alex")
        assert alex.tech_savviness == 5
        assert "efficiency-focused" in alex.traits
        assert alex.communication_style == "direct"

        morgan = get_persona("morgan")
        assert "low_vision" in morgan.accessibility_needs
        assert morgan.communication_style == "detailed"

        kai = get_persona("kai")
        assert kai.language_fluency == "learning"
        assert kai.tech_savviness == 2  # Lower for language learner
