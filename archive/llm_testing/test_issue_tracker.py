"""Tests for the IssueTracker module."""

import pytest
import tempfile
import os
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
from llm_testing.issue_tracker import IssueTracker, IssueTemplate
from llm_testing.insights_database import Insight


class TestIssueTracker:
    """Test the IssueTracker functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            "github_token": "test_token",
            "github_repo": "test/repo",
            "gitlab_token": "test_gitlab_token",
            "gitlab_project": "test/project",
        }
        self.issue_tracker = IssueTracker(self.config)

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up any created files
        if os.path.exists("issues"):
            for file in os.listdir("issues"):
                os.remove(os.path.join("issues", file))
            os.rmdir("issues")

        # Remove temp directory
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def create_test_insight(
        self,
        insight_type: str = "performance_regression",
        severity: str = "high",
        confidence: float = 0.8,
    ) -> Insight:
        """Create a test insight."""
        return Insight(
            insight_id=f"test-{insight_type}",
            insight_type=insight_type,
            description=f"Test {insight_type} insight",
            confidence=confidence,
            severity=severity,
            category="performance",
            code_version="0.1.0",
            timestamp=datetime.now().isoformat(),
            metadata={"test": True, "trend": "declining"},
            linked_issues=[],
            linked_insights=[],
        )

    def test_issue_tracker_initialization(self):
        """Test IssueTracker initialization."""
        assert self.issue_tracker.github_token == "test_token"
        assert self.issue_tracker.github_repo == "test/repo"
        assert self.issue_tracker.gitlab_token == "test_gitlab_token"
        assert self.issue_tracker.gitlab_project == "test/project"
        assert len(self.issue_tracker.issue_templates) > 0

    def test_issue_templates_loading(self):
        """Test that issue templates are loaded correctly."""
        templates = self.issue_tracker.issue_templates

        assert "performance_regression" in templates
        assert "accessibility_issue" in templates
        assert "clarity_decline" in templates
        assert "helpfulness_decline" in templates
        assert "accuracy_issue" in templates
        assert "trend_analysis" in templates

        # Check template structure
        template = templates["performance_regression"]
        assert isinstance(template, IssueTemplate)
        assert template.title == "Performance Regression Detected"
        assert "performance" in template.labels
        assert template.priority == "high"
        assert template.category == "bug"

    def test_get_template_for_insight(self):
        """Test getting appropriate template for different insight types."""
        # Performance regression
        insight = self.create_test_insight("performance_regression")
        template = self.issue_tracker._get_template_for_insight(insight)
        assert template.title == "Performance Regression Detected"

        # Clarity decline
        insight = self.create_test_insight("clarity_decline")
        template = self.issue_tracker._get_template_for_insight(insight)
        assert template.title == "Response Clarity Decline"

        # Accessibility issue
        insight = self.create_test_insight("accessibility_issue")
        template = self.issue_tracker._get_template_for_insight(insight)
        assert template.title == "Accessibility Issue Identified"

        # Unknown type
        insight = self.create_test_insight("unknown_type")
        template = self.issue_tracker._get_template_for_insight(insight)
        assert template.title == "Issue: unknown_type"

    def test_adjust_priority(self):
        """Test priority adjustment based on severity."""
        # Critical severity should override base priority
        assert self.issue_tracker._adjust_priority("medium", "critical") == "critical"
        assert self.issue_tracker._adjust_priority("low", "critical") == "critical"

        # High severity should override low/medium
        assert self.issue_tracker._adjust_priority("low", "high") == "high"
        assert self.issue_tracker._adjust_priority("medium", "high") == "high"

        # Medium severity should keep base priority
        assert self.issue_tracker._adjust_priority("medium", "medium") == "medium"
        assert self.issue_tracker._adjust_priority("high", "medium") == "high"

        # Low severity should downgrade
        assert self.issue_tracker._adjust_priority("high", "low") == "low"
        assert self.issue_tracker._adjust_priority("medium", "low") == "low"

    def test_generate_description(self):
        """Test issue description generation."""
        insight = self.create_test_insight("performance_regression", "high", 0.9)
        template = self.issue_tracker.issue_templates["performance_regression"]

        description = self.issue_tracker._generate_description(insight, template)

        # Check that all insight details are included
        assert "performance regression has been detected" in description.lower()
        assert "performance_regression" in description
        assert "Test performance_regression insight" in description
        assert "0.90" in description  # confidence
        assert "high" in description  # severity
        assert "performance" in description  # category
        assert "0.1.0" in description  # code version
        assert "test" in description  # metadata
        assert "LLM Testing Framework" in description

    def test_generate_issue_content(self):
        """Test issue content generation."""
        insight = self.create_test_insight("performance_regression", "critical", 0.9)
        template = self.issue_tracker.issue_templates["performance_regression"]

        content = self.issue_tracker._generate_issue_content(insight, template)

        assert content["title"] == "Performance Regression Detected"
        assert "performance" in content["labels"]
        assert "regression" in content["labels"]
        assert "critical" in content["labels"]  # adjusted priority
        assert "severity-critical" in content["labels"]
        assert content["priority"] == "critical"
        assert content["category"] == "bug"
        assert "insight_id" in content["metadata"]
        assert content["metadata"]["confidence"] == 0.9

    def test_create_local_issue(self):
        """Test local issue creation."""
        insight = self.create_test_insight("performance_regression")
        template = self.issue_tracker._get_template_for_insight(insight)
        issue_content = self.issue_tracker._generate_issue_content(insight, template)

        issue_path = self.issue_tracker._create_local_issue(issue_content)

        assert issue_path.startswith("issues/issue_")
        assert issue_path.endswith(".json")
        assert os.path.exists(issue_path)

        # Check file content
        with open(issue_path, "r") as f:
            data = json.load(f)

        assert data["title"] == "Performance Regression Detected"
        assert data["status"] == "open"
        assert "created_at" in data
        assert "performance" in data["labels"]

    def test_create_issues_from_insights(self):
        """Test creating issues from multiple insights."""
        # Create a tracker without credentials to force local creation
        local_config = {}
        local_tracker = IssueTracker(local_config)

        insights = [
            self.create_test_insight("performance_regression", "high", 0.8),
            self.create_test_insight(
                "clarity_decline", "medium", 0.6
            ),  # Should be filtered out
            self.create_test_insight("accuracy_issue", "critical", 0.9),
        ]

        issue_urls = local_tracker.create_issues_from_insights(insights)

        # Should create 2 issues (high/critical severity, high confidence)
        assert len(issue_urls) == 2
        assert all(url.startswith("issues/issue_") for url in issue_urls)

    def test_create_issues_from_insights_filtering(self):
        """Test that insights are properly filtered."""
        # Create a tracker without credentials to force local creation
        local_config = {}
        local_tracker = IssueTracker(local_config)

        insights = [
            self.create_test_insight(
                "performance_regression", "low", 0.8
            ),  # Low severity
            self.create_test_insight("clarity_decline", "high", 0.6),  # Low confidence
            self.create_test_insight(
                "accuracy_issue", "critical", 0.9
            ),  # Should be created
        ]

        issue_urls = local_tracker.create_issues_from_insights(insights)

        # Should only create 1 issue (critical severity, high confidence)
        assert len(issue_urls) == 1

    def test_create_github_issue_success(self):
        """Test successful GitHub issue creation."""
        try:
            import requests

            with patch("requests.post") as mock_post:
                mock_response = MagicMock()
                mock_response.status_code = 201
                mock_response.json.return_value = {
                    "html_url": "https://github.com/test/repo/issues/123",
                    "number": 123,
                }
                mock_post.return_value = mock_response

                insight = self.create_test_insight("performance_regression")
                template = self.issue_tracker._get_template_for_insight(insight)
                issue_content = self.issue_tracker._generate_issue_content(
                    insight, template
                )

                issue_url = self.issue_tracker._create_github_issue(issue_content)

                assert issue_url == "https://github.com/test/repo/issues/123"
                mock_post.assert_called_once()

                # Check the request data
                call_args = mock_post.call_args
                assert (
                    "https://api.github.com/repos/test/repo/issues" in call_args[0][0]
                )
                assert (
                    call_args[1]["json"]["title"] == "Performance Regression Detected"
                )
        except ImportError:
            pytest.skip("requests module not available")

    def test_create_github_issue_failure(self):
        """Test GitHub issue creation failure."""
        try:
            import requests
        except ImportError:
            pytest.skip("requests module not available")

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_post.return_value = mock_response

            insight = self.create_test_insight("performance_regression")
            template = self.issue_tracker._get_template_for_insight(insight)
            issue_content = self.issue_tracker._generate_issue_content(
                insight, template
            )

            issue_url = self.issue_tracker._create_github_issue(issue_content)

            assert issue_url is None

    def test_create_gitlab_issue_success(self):
        """Test successful GitLab issue creation."""
        try:
            import requests
        except ImportError:
            pytest.skip("requests module not available")

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "web_url": "https://gitlab.com/test/project/issues/456",
                "iid": 456,
            }
            mock_post.return_value = mock_response

            insight = self.create_test_insight("performance_regression")
            template = self.issue_tracker._get_template_for_insight(insight)
            issue_content = self.issue_tracker._generate_issue_content(
                insight, template
            )

            issue_url = self.issue_tracker._create_gitlab_issue(issue_content)

            assert issue_url == "https://gitlab.com/test/project/issues/456"
            mock_post.assert_called_once()

    def test_get_local_issue_status(self):
        """Test getting local issue status."""
        # Create a test issue file
        os.makedirs("issues", exist_ok=True)
        test_issue = {
            "title": "Test Issue",
            "status": "open",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "labels": ["test", "bug"],
        }

        with open("issues/test_issue.json", "w") as f:
            json.dump(test_issue, f)

        status = self.issue_tracker._get_local_issue_status("issues/test_issue.json")

        assert status["state"] == "open"
        assert status["title"] == "Test Issue"
        assert "test" in status["labels"]
        assert "bug" in status["labels"]

    def test_close_local_issue(self):
        """Test closing a local issue."""
        # Create a test issue file
        os.makedirs("issues", exist_ok=True)
        test_issue = {
            "title": "Test Issue",
            "status": "open",
            "created_at": "2024-01-01T00:00:00",
        }

        with open("issues/test_issue.json", "w") as f:
            json.dump(test_issue, f)

        success = self.issue_tracker._close_local_issue(
            "issues/test_issue.json", "resolved"
        )

        assert success

        # Check that the issue was updated
        with open("issues/test_issue.json", "r") as f:
            updated_issue = json.load(f)

        assert updated_issue["status"] == "closed"
        assert "closed_at" in updated_issue
        assert updated_issue["close_reason"] == "resolved"

    def test_issue_tracker_without_credentials(self):
        """Test IssueTracker without GitHub/GitLab credentials."""
        config = {}  # No credentials
        tracker = IssueTracker(config)

        insight = self.create_test_insight("performance_regression")
        template = tracker._get_template_for_insight(insight)
        issue_content = tracker._generate_issue_content(insight, template)

        # Should fall back to local issue creation
        issue_path = tracker._create_github_issue(issue_content)
        assert issue_path is None  # No GitHub credentials

        issue_path = tracker._create_gitlab_issue(issue_content)
        assert issue_path is None  # No GitLab credentials

        # Should work with local creation
        issue_path = tracker._create_local_issue(issue_content)
        assert issue_path.startswith("issues/issue_")

    def test_issue_template_creation(self):
        """Test IssueTemplate dataclass."""
        template = IssueTemplate(
            title="Test Issue",
            description="Test description",
            labels=["test", "bug"],
            assignees=["user1"],
            priority="high",
            category="bug",
        )

        assert template.title == "Test Issue"
        assert template.description == "Test description"
        assert template.labels == ["test", "bug"]
        assert template.assignees == ["user1"]
        assert template.priority == "high"
        assert template.category == "bug"

    def test_error_handling(self):
        """Test error handling in issue creation."""
        # Test with invalid insight
        insight = self.create_test_insight("invalid_type")
        template = self.issue_tracker._get_template_for_insight(insight)
        issue_content = self.issue_tracker._generate_issue_content(insight, template)

        # Should handle errors gracefully
        issue_path = self.issue_tracker._create_local_issue(issue_content)
        assert issue_path.startswith("issues/issue_")

    def test_issue_content_with_metadata(self):
        """Test issue content generation with rich metadata."""
        insight = self.create_test_insight("performance_regression", "critical", 0.9)
        insight.metadata = {
            "trend": "declining",
            "regression_percentage": 15.5,
            "affected_personas": ["Alex", "Sam"],
            "affected_scenarios": ["MorningRoutine", "EveningRoutine"],
        }
        insight.linked_issues = ["#123", "#456"]
        insight.linked_insights = ["insight-1", "insight-2"]

        template = self.issue_tracker._get_template_for_insight(insight)
        content = self.issue_tracker._generate_issue_content(insight, template)
        description = self.issue_tracker._generate_description(insight, template)

        assert "declining" in description
        assert "15.5" in description
        assert "Alex" in description
        assert "Sam" in description
        assert "MorningRoutine" in description
        assert "EveningRoutine" in description
        assert "#123" in description
        assert "#456" in description
        assert "insight-1" in description
        assert "insight-2" in description
