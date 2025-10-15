"""Tests for the InsightsDatabase module."""

import pytest
import tempfile
import os
from datetime import datetime
from llm_testing.insights_database import InsightsDatabase, Insight


class TestInsightsDatabase:
    """Test the InsightsDatabase functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary database file
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_insights.db")
        self.db = InsightsDatabase(self.db_path)

    def teardown_method(self):
        """Clean up test fixtures."""
        # Remove the database file
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        # Remove the temp directory
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_create_tables(self):
        """Test that tables are created correctly."""
        # The database should be created in setup_method
        assert os.path.exists(self.db_path)

        # Check that we can query the table
        insights = self.db.get_insights_by_type("test")
        assert isinstance(insights, list)

    def test_store_and_retrieve_insight(self):
        """Test storing and retrieving a single insight."""
        insight = Insight(
            insight_id="test-1",
            insight_type="performance",
            description="Test insight",
            confidence=0.8,
            severity="medium",
            category="persona",
            code_version="0.1.0",
            timestamp=datetime.now().isoformat(),
            metadata={"test": "data"},
            linked_issues=["issue-1"],
            linked_insights=["insight-2"],
        )

        # Store the insight
        success = self.db.store_insight(insight)
        assert success

        # Retrieve the insight
        retrieved = self.db.get_insight("test-1")
        assert retrieved is not None
        assert retrieved.insight_id == "test-1"
        assert retrieved.insight_type == "performance"
        assert retrieved.description == "Test insight"
        assert retrieved.confidence == 0.8
        assert retrieved.severity == "medium"
        assert retrieved.category == "persona"
        assert retrieved.metadata == {"test": "data"}
        assert retrieved.linked_issues == ["issue-1"]
        assert retrieved.linked_insights == ["insight-2"]

    def test_get_insights_by_type(self):
        """Test retrieving insights by type."""
        # Create multiple insights
        insights = [
            Insight(
                insight_id=f"test-{i}",
                insight_type="performance" if i % 2 == 0 else "accessibility",
                description=f"Test insight {i}",
                confidence=0.7 + (i * 0.1),
                severity="medium",
                category="persona",
                code_version="0.1.0",
                timestamp=datetime.now().isoformat(),
                metadata={"test": i},
                linked_issues=[],
                linked_insights=[],
            )
            for i in range(5)
        ]

        # Store all insights
        for insight in insights:
            self.db.store_insight(insight)

        # Get performance insights
        performance_insights = self.db.get_insights_by_type("performance")
        assert len(performance_insights) == 3  # 0, 2, 4

        # Get accessibility insights
        accessibility_insights = self.db.get_insights_by_type("accessibility")
        assert len(accessibility_insights) == 2  # 1, 3

    def test_get_insights_by_category(self):
        """Test retrieving insights by category."""
        # Create insights with different categories
        insights = [
            Insight(
                insight_id=f"test-{i}",
                insight_type="performance",
                description=f"Test insight {i}",
                confidence=0.8,
                severity="medium",
                category="persona" if i % 2 == 0 else "scenario",
                code_version="0.1.0",
                timestamp=datetime.now().isoformat(),
                metadata={"test": i},
                linked_issues=[],
                linked_insights=[],
            )
            for i in range(4)
        ]

        # Store all insights
        for insight in insights:
            self.db.store_insight(insight)

        # Get persona insights
        persona_insights = self.db.get_insights_by_category("persona")
        assert len(persona_insights) == 2  # 0, 2

        # Get scenario insights
        scenario_insights = self.db.get_insights_by_category("scenario")
        assert len(scenario_insights) == 2  # 1, 3

    def test_get_insights_by_version(self):
        """Test retrieving insights by code version."""
        # Create insights with different versions
        insights = [
            Insight(
                insight_id=f"test-{i}",
                insight_type="performance",
                description=f"Test insight {i}",
                confidence=0.8,
                severity="medium",
                category="persona",
                code_version="0.1.0" if i % 2 == 0 else "0.2.0",
                timestamp=datetime.now().isoformat(),
                metadata={"test": i},
                linked_issues=[],
                linked_insights=[],
            )
            for i in range(4)
        ]

        # Store all insights
        for insight in insights:
            self.db.store_insight(insight)

        # Get v0.1.0 insights
        v1_insights = self.db.get_insights_by_version("0.1.0")
        assert len(v1_insights) == 2  # 0, 2

        # Get v0.2.0 insights
        v2_insights = self.db.get_insights_by_version("0.2.0")
        assert len(v2_insights) == 2  # 1, 3

    def test_get_high_confidence_insights(self):
        """Test retrieving high confidence insights."""
        # Create insights with different confidence levels
        insights = [
            Insight(
                insight_id=f"test-{i}",
                insight_type="performance",
                description=f"Test insight {i}",
                confidence=0.6 + (i * 0.1),  # 0.6, 0.7, 0.8, 0.9
                severity="medium",
                category="persona",
                code_version="0.1.0",
                timestamp=datetime.now().isoformat(),
                metadata={"test": i},
                linked_issues=[],
                linked_insights=[],
            )
            for i in range(4)
        ]

        # Store all insights
        for insight in insights:
            self.db.store_insight(insight)

        # Get high confidence insights (>= 0.8)
        high_confidence = self.db.get_high_confidence_insights(0.8)
        assert len(high_confidence) == 2  # 0.8, 0.9

        # Verify they're ordered by confidence descending
        assert high_confidence[0].confidence >= high_confidence[1].confidence

    def test_get_insights_summary(self):
        """Test getting insights summary."""
        # Create insights with different types and severities
        insights = [
            Insight(
                insight_id=f"test-{i}",
                insight_type="performance" if i % 2 == 0 else "accessibility",
                description=f"Test insight {i}",
                confidence=0.8,
                severity="high" if i % 3 == 0 else "medium",
                category="persona",
                code_version="0.1.0",
                timestamp=datetime.now().isoformat(),
                metadata={"test": i},
                linked_issues=[],
                linked_insights=[],
            )
            for i in range(6)
        ]

        # Store all insights
        for insight in insights:
            self.db.store_insight(insight)

        # Get summary
        summary = self.db.get_insights_summary()

        assert summary["total_insights"] == 6
        assert summary["by_type"]["performance"] == 3
        assert summary["by_type"]["accessibility"] == 3
        assert summary["by_severity"]["high"] == 2
        assert summary["by_severity"]["medium"] == 4
        assert abs(summary["average_confidence"] - 0.8) < 0.001
        assert summary["recent_insights"] == 6

    def test_delete_insight(self):
        """Test deleting an insight."""
        insight = Insight(
            insight_id="test-delete",
            insight_type="performance",
            description="Test insight to delete",
            confidence=0.8,
            severity="medium",
            category="persona",
            code_version="0.1.0",
            timestamp=datetime.now().isoformat(),
            metadata={"test": "delete"},
            linked_issues=[],
            linked_insights=[],
        )

        # Store the insight
        self.db.store_insight(insight)
        assert self.db.get_insight("test-delete") is not None

        # Delete the insight
        success = self.db.delete_insight("test-delete")
        assert success

        # Verify it's deleted
        assert self.db.get_insight("test-delete") is None

    def test_clear_old_insights(self):
        """Test clearing old insights."""
        # Create insights with different timestamps
        from datetime import timedelta

        now = datetime.now()
        insights = [
            Insight(
                insight_id=f"test-{i}",
                insight_type="performance",
                description=f"Test insight {i}",
                confidence=0.8,
                severity="medium",
                category="persona",
                code_version="0.1.0",
                timestamp=(
                    now - timedelta(days=i * 10)
                ).isoformat(),  # 0, 10, 20, 30 days ago
                metadata={"test": i},
                linked_issues=[],
                linked_insights=[],
            )
            for i in range(4)
        ]

        # Store all insights
        for insight in insights:
            self.db.store_insight(insight)

        # Clear insights older than 15 days
        deleted_count = self.db.clear_old_insights(15)
        assert deleted_count == 2  # 20 and 30 days ago

        # Verify remaining insights
        remaining = self.db.get_insights_by_type("performance")
        assert len(remaining) == 2  # 0 and 10 days ago

    def test_error_handling(self):
        """Test error handling in database operations."""
        # Test with invalid insight (missing required fields)
        invalid_insight = Insight(
            insight_id="test-invalid",
            insight_type="",  # Empty type
            description="",  # Empty description
            confidence=-1.0,  # Invalid confidence
            severity="invalid",  # Invalid severity
            category="",
            code_version="",
            timestamp="",
            metadata={},
            linked_issues=[],
            linked_insights=[],
        )

        # Should handle gracefully
        success = self.db.store_insight(invalid_insight)
        # SQLite will store it anyway, so this should succeed
        assert success

    def test_insight_metadata(self):
        """Test storing and retrieving complex metadata."""
        complex_metadata = {
            "scores": {"clarity": 4.0, "helpfulness": 3.5},
            "persona": "Alex",
            "scenario": "Morning Routine Setup",
            "nested": {"level1": {"level2": "value"}},
            "list": [1, 2, 3, "string"],
            "boolean": True,
            "null": None,
        }

        insight = Insight(
            insight_id="test-metadata",
            insight_type="performance",
            description="Test insight with complex metadata",
            confidence=0.9,
            severity="high",
            category="persona",
            code_version="0.1.0",
            timestamp=datetime.now().isoformat(),
            metadata=complex_metadata,
            linked_issues=["issue-1", "issue-2"],
            linked_insights=["insight-1", "insight-2"],
        )

        # Store and retrieve
        self.db.store_insight(insight)
        retrieved = self.db.get_insight("test-metadata")

        assert retrieved is not None
        assert retrieved.metadata == complex_metadata
        assert retrieved.linked_issues == ["issue-1", "issue-2"]
        assert retrieved.linked_insights == ["insight-1", "insight-2"]
