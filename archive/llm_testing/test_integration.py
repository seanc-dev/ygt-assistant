"""Integration tests for the LLM testing framework."""

import pytest
import tempfile
import os
from datetime import datetime
from llm_testing.config import TestingConfig
from llm_testing.personas import Persona
from llm_testing.scenarios import Scenario, TestPrompt, ExpectedBehavior
from llm_testing.prompts import PromptTemplate
from llm_testing.evaluator import ScoringAgent
from llm_testing.evaluation_loop import EvaluationLoop
from llm_testing.database import ResultsDatabase
from llm_testing.dashboard import Dashboard, AlertSystem
from llm_testing.types import EvaluationResult


class TestLLMTestingFrameworkIntegration:
    """Test the complete LLM testing framework integration."""

    def setup_method(self):
        """Set up test environment."""
        # Create temporary database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_integration.db")

        # Create test configuration
        self.config = TestingConfig(
            scoring_model="gpt-3.5-turbo",
            fallback_model="gpt-3.5-turbo",
            results_storage=self.db_path,
            alert_threshold=3.5,
        )

    def teardown_method(self):
        """Clean up test environment."""
        # Remove temporary database file
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        # Remove any other files in temp dir
        if os.path.exists(self.temp_dir):
            for file in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(self.temp_dir)

    def test_framework_components_integration(self):
        """Test that all framework components work together."""
        # Create test persona
        persona = Persona(
            name="Test User",
            traits=["busy", "efficient"],
            goals=["optimize productivity"],
            behaviors=["prefers morning meetings"],
            quirks=["forgets to add travel time"],
            communication_style="direct",
            tech_savviness=4,
            time_preferences={"work_hours": "9-5"},
            accessibility_needs=[],
            language_fluency="native",
            challenge_type="standard",
        )

        # Create test prompt
        test_prompt = TestPrompt(
            prompt="Schedule a team meeting for tomorrow at 2pm",
            context={"current_time": "2024-01-15T10:00:00"},
            expected_actions=["create_event"],
            expected_qualities=["clear", "helpful"],
            difficulty="easy",
            category="scheduling",
            template_vars={},
            failure_mode="none",
        )

        # Create test scenario
        scenario = Scenario(
            name="Basic Scheduling Test",
            persona=persona,
            goals=["Schedule a meeting"],
            initial_context={"calendar": "empty"},
            test_prompts=[test_prompt],
            expected_behaviors=[
                ExpectedBehavior(
                    description="Should create a calendar event",
                    category="scheduling",
                    importance="critical",
                    success_criteria=["Event is created"],
                )
            ],
            success_criteria=[
                "Event is created with correct time",
                "Response is clear and helpful",
            ],
            difficulty="easy",
            category="scheduling",
            ground_truth={
                "expected_response": "I'll schedule a team meeting for tomorrow at 2pm.",
                "expected_actions": ["create_event"],
            },
            version="1.0",
        )

        # Create scoring agent
        scoring_agent = ScoringAgent(self.config)

        # Create mock assistant client
        class MockAssistantClient:
            def generate_response(self, prompt: str) -> str:
                return "I'll schedule a team meeting for tomorrow at 2pm."

        assistant_client = MockAssistantClient()

        # Create evaluation loop
        evaluation_loop = EvaluationLoop(
            assistant_client=assistant_client,
            scoring_agent=scoring_agent,
            config=self.config,
        )

        # Run a scenario
        scenario_result = evaluation_loop.run_scenario(scenario)

        # Verify results
        assert scenario_result.scenario == scenario
        assert len(scenario_result.results) == 1
        assert scenario_result.success_rate >= 0.0
        assert scenario_result.average_score >= 0.0

        # Check database integration
        recent_results = evaluation_loop.results_db.get_recent_results(limit=10)
        assert len(recent_results) == 1
        assert recent_results[0].scenario_name == "Basic Scheduling Test"

        # Check dashboard integration
        dashboard = evaluation_loop.dashboard
        metrics = dashboard.get_key_metrics()
        assert metrics["total_tests"] == 1
        assert metrics["average_score"] >= 0.0

    def test_prompt_template_integration(self):
        """Test prompt template integration."""
        # Create a prompt template
        template = PromptTemplate(
            template="Schedule a {meeting_type} meeting for {date} at {time}",
            slot_fillers={
                "meeting_type": ["team", "client", "review"],
                "date": ["tomorrow", "next Monday", "this Friday"],
                "time": ["9am", "2pm", "4pm"],
            },
        )

        # Generate variations
        variations = template.generate_variations(count=3)
        assert len(variations) == 3
        assert all(isinstance(v, TestPrompt) for v in variations)

    def test_database_persistence(self):
        """Test that data persists correctly in database."""
        db = ResultsDatabase(self.db_path)

        # Store test data
        result = EvaluationResult(
            scenario_name="test_scenario",
            persona_name="test_persona",
            prompt="test prompt",
            assistant_response="test response",
            scores={"clarity": 4.0, "helpfulness": 4.0},
            intermediate_scores={},
            feedback="test feedback",
            timestamp=datetime.now().isoformat(),
            code_version="test_version",
            model_version="test_model",
            metadata={"test": "data"},
        )

        db.store_evaluation_result(result)

        # Verify persistence
        recent_results = db.get_recent_results(limit=10)
        assert len(recent_results) == 1
        assert recent_results[0].scenario_name == "test_scenario"

    def test_dashboard_metrics(self):
        """Test dashboard metrics calculation."""
        db = ResultsDatabase(self.db_path)
        dashboard = Dashboard(db, alert_threshold=3.5)

        # Store test data
        for i in range(5):
            result = EvaluationResult(
                scenario_name=f"scenario_{i}",
                persona_name=f"persona_{i}",
                prompt=f"prompt_{i}",
                assistant_response=f"response_{i}",
                scores={"clarity": 4.0, "helpfulness": 4.0},
                intermediate_scores={},
                feedback=f"feedback_{i}",
                timestamp=datetime.now().isoformat(),
                code_version="test_version",
                model_version="test_model",
                metadata={},
            )
            db.store_evaluation_result(result)

        # Check metrics
        metrics = dashboard.get_key_metrics()
        assert metrics["total_tests"] == 5
        assert metrics["average_score"] == 4.0
        assert metrics["success_rate"] == 100.0

        # Check performance breakdowns
        scenario_performance = dashboard.get_scenario_performance()
        assert len(scenario_performance) == 5

        persona_performance = dashboard.get_persona_performance()
        assert len(persona_performance) == 5

    def test_alert_system_integration(self):
        """Test alert system integration."""
        db = ResultsDatabase(self.db_path)
        dashboard = Dashboard(db, alert_threshold=3.5)
        alert_system = AlertSystem(dashboard)

        # Create low scores to trigger alerts
        for i in range(3):
            result = EvaluationResult(
                scenario_name=f"scenario_{i}",
                persona_name=f"persona_{i}",
                prompt=f"prompt_{i}",
                assistant_response=f"response_{i}",
                scores={"clarity": 2.0, "helpfulness": 2.5},  # Low scores
                intermediate_scores={},
                feedback=f"feedback_{i}",
                timestamp=datetime.now().isoformat(),
                code_version="test_version",
                model_version="test_model",
                metadata={},
            )
            db.store_evaluation_result(result)

        # Check for alerts
        new_alerts = alert_system.check_alerts()
        assert len(new_alerts) > 0

        # Process alerts
        alert_system.process_alerts()
        assert len(alert_system.get_alert_history()) > 0

    def test_batch_evaluation(self):
        """Test batch evaluation functionality."""
        # Create test scenarios
        scenarios = []
        for i in range(3):
            persona = Persona(
                name=f"Test User {i}",
                traits=["busy"],
                goals=["optimize productivity"],
                behaviors=["prefers morning meetings"],
                quirks=[],
                communication_style="direct",
                tech_savviness=4,
                time_preferences={"work_hours": "9-5"},
                accessibility_needs=[],
                language_fluency="native",
                challenge_type="standard",
            )

            test_prompt = TestPrompt(
                prompt=f"Schedule meeting {i}",
                context={},
                expected_actions=["create_event"],
                expected_qualities=["clear"],
                difficulty="easy",
                category="scheduling",
                template_vars={},
                failure_mode="none",
            )

            scenario = Scenario(
                name=f"Test Scenario {i}",
                persona=persona,
                goals=["Schedule a meeting"],
                initial_context={"calendar": "empty"},
                test_prompts=[test_prompt],
                expected_behaviors=[],
                success_criteria=[],
                difficulty="easy",
                category="scheduling",
                ground_truth={},
                version="1.0",
            )
            scenarios.append(scenario)

        # Create evaluation loop
        scoring_agent = ScoringAgent(self.config)

        class MockAssistantClient:
            def generate_response(self, prompt: str) -> str:
                return "I'll schedule that meeting for you."

        assistant_client = MockAssistantClient()

        evaluation_loop = EvaluationLoop(
            assistant_client=assistant_client,
            scoring_agent=scoring_agent,
            config=self.config,
        )

        # Run batch evaluation
        batch_result = evaluation_loop.run_batch(scenarios)

        # Verify batch results
        assert len(batch_result.scenarios) == 3
        assert len(batch_result.results) == 3
        assert "batch_" in batch_result.batch_id

        # Check database storage
        recent_results = evaluation_loop.results_db.get_recent_results(limit=10)
        assert len(recent_results) == 3
