"""Tests for the dashboard module."""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from llm_testing.database import ResultsDatabase
from llm_testing.dashboard import Dashboard, AlertSystem
from llm_testing.types import EvaluationResult


class TestDashboard:
    """Test the Dashboard class."""

    def setup_method(self):
        """Set up test database and dashboard."""
        # Create a temporary database file
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_dashboard.db")
        self.db = ResultsDatabase(self.db_path)
        self.dashboard = Dashboard(self.db, alert_threshold=3.5)

    def teardown_method(self):
        """Clean up test database."""
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

    def test_get_key_metrics_empty(self):
        """Test key metrics when no data exists."""
        metrics = self.dashboard.get_key_metrics()

        assert metrics["total_tests"] == 0
        assert metrics["average_score"] == 0.0
        assert metrics["success_rate"] == 0.0
        assert metrics["recent_trend"] == "no_data"
        assert len(metrics["alerts"]) == 0

    def test_get_key_metrics_with_data(self):
        """Test key metrics with test data."""
        # Store some test results
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
            self.db.store_evaluation_result(result)

        metrics = self.dashboard.get_key_metrics()

        assert metrics["total_tests"] == 5
        assert metrics["average_score"] == 4.0
        assert metrics["success_rate"] == 100.0  # All scores >= 3.5
        assert len(metrics["alerts"]) == 0

    def test_get_scenario_performance(self):
        """Test getting scenario performance breakdown."""
        # Store results for different scenarios
        scenarios = ["scenario_a", "scenario_b", "scenario_a"]
        scores = [4.0, 3.0, 5.0]

        for i, scenario in enumerate(scenarios):
            result = EvaluationResult(
                scenario_name=scenario,
                persona_name="test_persona",
                prompt="test prompt",
                assistant_response="test response",
                scores={"overall": scores[i]},
                intermediate_scores={},
                feedback="test feedback",
                timestamp=datetime.now().isoformat(),
                code_version="test_version",
                model_version="test_model",
                metadata={},
            )
            self.db.store_evaluation_result(result)

        performance = self.dashboard.get_scenario_performance()

        assert "scenario_a" in performance
        assert "scenario_b" in performance
        assert abs(performance["scenario_a"] - 4.5) < 0.01
        assert abs(performance["scenario_b"] - 3.0) < 0.01

    def test_get_persona_performance(self):
        """Test getting persona performance breakdown."""
        # Store results for different personas
        personas = ["persona_a", "persona_b", "persona_a"]
        scores = [4.0, 3.0, 5.0]

        for i, persona in enumerate(personas):
            result = EvaluationResult(
                scenario_name="test_scenario",
                persona_name=persona,
                prompt="test prompt",
                assistant_response="test response",
                scores={"overall": scores[i]},
                intermediate_scores={},
                feedback="test feedback",
                timestamp=datetime.now().isoformat(),
                code_version="test_version",
                model_version="test_model",
                metadata={},
            )
            self.db.store_evaluation_result(result)

        performance = self.dashboard.get_persona_performance()

        assert "persona_a" in performance
        assert "persona_b" in performance
        assert abs(performance["persona_a"] - 4.5) < 0.01
        assert abs(performance["persona_b"] - 3.0) < 0.01

    def test_get_alerts_low_score(self):
        """Test alert generation for low scores."""
        # Store results with low scores
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
            self.db.store_evaluation_result(result)

        metrics = self.dashboard.get_key_metrics()

        # Should have alerts for low scores
        assert len(metrics["alerts"]) > 0
        assert any(alert["type"] == "low_score" for alert in metrics["alerts"])

    def test_get_alerts_high_failure_rate(self):
        """Test alert generation for high failure rate."""
        # Store results with many failures
        for i in range(10):
            score = 2.0 if i < 6 else 4.0  # 60% failures
            result = EvaluationResult(
                scenario_name=f"scenario_{i}",
                persona_name=f"persona_{i}",
                prompt=f"prompt_{i}",
                assistant_response=f"response_{i}",
                scores={"clarity": score, "helpfulness": score},
                intermediate_scores={},
                feedback=f"feedback_{i}",
                timestamp=datetime.now().isoformat(),
                code_version="test_version",
                model_version="test_model",
                metadata={},
            )
            self.db.store_evaluation_result(result)

        metrics = self.dashboard.get_key_metrics()

        # Should have alerts for high failure rate
        assert len(metrics["alerts"]) > 0
        assert any(alert["type"] == "high_failure_rate" for alert in metrics["alerts"])

    def test_get_insights_summary(self):
        """Test getting insights summary."""
        # Store some insights
        insight_types = ["performance_pattern", "user_experience", "feature_gap"]

        for insight_type in insight_types:
            insight = {
                "insight_type": insight_type,
                "description": f"Test {insight_type} insight",
                "confidence": 0.8,
                "evidence": [],
                "recommendations": [],
                "timestamp": datetime.now().isoformat(),
                "code_version": "test_version",
                "model_version": "test_model",
                "linked_issues": [],
            }
            self.db.store_insight(insight)

        summary = self.dashboard.get_insights_summary()

        assert "performance_pattern" in summary
        assert "user_experience" in summary
        assert "feature_gap" in summary
        assert "accessibility" in summary  # Should be present even if empty

        for insight_type in ["performance_pattern", "user_experience", "feature_gap"]:
            assert summary[insight_type]["count"] == 1

    def test_generate_dashboard_data(self):
        """Test generating complete dashboard data."""
        # Store some test data
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
            metadata={},
        )
        self.db.store_evaluation_result(result)

        dashboard_data = self.dashboard.generate_dashboard_data()

        assert "key_metrics" in dashboard_data
        assert "scenario_performance" in dashboard_data
        assert "persona_performance" in dashboard_data
        assert "insights_summary" in dashboard_data
        assert "regression_alerts" in dashboard_data
        assert "last_updated" in dashboard_data

    def test_export_dashboard_json(self):
        """Test exporting dashboard data to JSON."""
        # Store some test data
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
            metadata={},
        )
        self.db.store_evaluation_result(result)

        # Export to temporary file
        temp_file = os.path.join(self.temp_dir, "dashboard.json")
        self.dashboard.export_dashboard_json(temp_file)

        # Verify file was created
        assert os.path.exists(temp_file)

        # Verify file contains valid JSON
        import json

        with open(temp_file, "r") as f:
            data = json.load(f)
            assert "key_metrics" in data


class TestAlertSystem:
    """Test the AlertSystem class."""

    def setup_method(self):
        """Set up test database, dashboard, and alert system."""
        # Create a temporary database file
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_alerts.db")
        self.db = ResultsDatabase(self.db_path)
        self.dashboard = Dashboard(self.db, alert_threshold=3.5)
        self.alert_system = AlertSystem(self.dashboard)

    def teardown_method(self):
        """Clean up test database."""
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

    def test_check_alerts_no_alerts(self):
        """Test checking alerts when no alerts exist."""
        new_alerts = self.alert_system.check_alerts()
        assert len(new_alerts) == 0

    def test_check_alerts_with_alerts(self):
        """Test checking alerts when alerts exist."""
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
            self.db.store_evaluation_result(result)

        new_alerts = self.alert_system.check_alerts()

        # Should have new alerts
        assert len(new_alerts) > 0

    def test_process_alerts(self):
        """Test processing alerts."""
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
            self.db.store_evaluation_result(result)

        # Process alerts
        self.alert_system.process_alerts()

        # Should have alert history
        assert len(self.alert_system.get_alert_history()) > 0

    def test_clear_resolved_alerts(self):
        """Test clearing resolved alerts."""
        # Create alerts
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
            self.db.store_evaluation_result(result)

        # Process alerts to create history
        self.alert_system.process_alerts()
        initial_history_count = len(self.alert_system.get_alert_history())

        # Clear resolved alerts
        self.alert_system.clear_resolved_alerts()

        # History should be cleared if alerts are resolved
        # (This depends on the current state of alerts)
        assert len(self.alert_system.get_alert_history()) <= initial_history_count
