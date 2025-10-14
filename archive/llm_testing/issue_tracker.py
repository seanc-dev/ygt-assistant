"""Issue tracker for automated issue creation from LLM testing insights."""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .insights_database import Insight


@dataclass
class IssueTemplate:
    """Template for creating issues from insights."""

    title: str
    description: str
    labels: List[str]
    assignees: List[str]
    priority: str  # "low", "medium", "high", "critical"
    category: str  # "bug", "enhancement", "documentation", "performance"


class IssueTracker:
    """Automated issue creation from LLM testing insights."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the issue tracker."""
        self.config = config
        self.github_token = config.get("github_token")
        self.github_repo = config.get("github_repo")
        self.gitlab_token = config.get("gitlab_token")
        self.gitlab_project = config.get("gitlab_project")
        self.issue_templates = self._load_issue_templates()

    def _load_issue_templates(self) -> Dict[str, IssueTemplate]:
        """Load issue templates for different insight types."""
        return {
            "performance_regression": IssueTemplate(
                title="Performance Regression Detected",
                description="A performance regression has been detected in LLM testing results.",
                labels=["performance", "regression", "llm-testing"],
                assignees=[],
                priority="high",
                category="bug",
            ),
            "accessibility_issue": IssueTemplate(
                title="Accessibility Issue Identified",
                description="An accessibility issue has been identified in the assistant responses.",
                labels=["accessibility", "llm-testing"],
                assignees=[],
                priority="medium",
                category="enhancement",
            ),
            "clarity_decline": IssueTemplate(
                title="Response Clarity Decline",
                description="A decline in response clarity has been detected.",
                labels=["clarity", "regression", "llm-testing"],
                assignees=[],
                priority="medium",
                category="enhancement",
            ),
            "helpfulness_decline": IssueTemplate(
                title="Response Helpfulness Decline",
                description="A decline in response helpfulness has been detected.",
                labels=["helpfulness", "regression", "llm-testing"],
                assignees=[],
                priority="medium",
                category="enhancement",
            ),
            "accuracy_issue": IssueTemplate(
                title="Accuracy Issue Detected",
                description="An accuracy issue has been detected in assistant responses.",
                labels=["accuracy", "bug", "llm-testing"],
                assignees=[],
                priority="high",
                category="bug",
            ),
            "trend_analysis": IssueTemplate(
                title="Trend Analysis Alert",
                description="A concerning trend has been identified in testing results.",
                labels=["trend-analysis", "llm-testing"],
                assignees=[],
                priority="medium",
                category="enhancement",
            ),
        }

    def create_issue_from_insight(self, insight: Insight) -> Optional[str]:
        """Create an issue from an insight."""
        try:
            # Determine issue template based on insight type
            template = self._get_template_for_insight(insight)
            if not template:
                print(f"No template found for insight type: {insight.insight_type}")
                return None

            # Generate issue content
            issue_content = self._generate_issue_content(insight, template)

            # Create issue based on platform
            if self.github_token and self.github_repo:
                return self._create_github_issue(issue_content)
            elif self.gitlab_token and self.gitlab_project:
                return self._create_gitlab_issue(issue_content)
            else:
                # Fallback to local issue tracking
                return self._create_local_issue(issue_content)

        except Exception as e:
            print(f"Error creating issue from insight: {e}")
            return None

    def _get_template_for_insight(self, insight: Insight) -> Optional[IssueTemplate]:
        """Get the appropriate template for an insight."""
        insight_type = insight.insight_type.lower()

        # Map insight types to templates
        if "regression" in insight_type or "decline" in insight_type:
            if "performance" in insight_type:
                return self.issue_templates["performance_regression"]
            elif "clarity" in insight_type:
                return self.issue_templates["clarity_decline"]
            elif "helpfulness" in insight_type:
                return self.issue_templates["helpfulness_decline"]
            elif "accuracy" in insight_type:
                return self.issue_templates["accuracy_issue"]

        elif "accessibility" in insight_type:
            return self.issue_templates["accessibility_issue"]

        elif "trend" in insight_type:
            return self.issue_templates["trend_analysis"]

        # Default template for unknown types
        return IssueTemplate(
            title=f"Issue: {insight.insight_type}",
            description=insight.description,
            labels=["llm-testing", "insight"],
            assignees=[],
            priority="medium",
            category="enhancement",
        )

    def _generate_issue_content(
        self, insight: Insight, template: IssueTemplate
    ) -> Dict[str, Any]:
        """Generate issue content from insight and template."""
        # Adjust priority based on insight severity
        priority = self._adjust_priority(template.priority, insight.severity)

        # Generate detailed description
        description = self._generate_description(insight, template)

        # Add metadata
        metadata = {
            "insight_id": insight.insight_id,
            "confidence": insight.confidence,
            "code_version": insight.code_version,
            "timestamp": insight.timestamp,
            "metadata": insight.metadata,
        }

        return {
            "title": template.title,
            "description": description,
            "labels": template.labels + [priority, f"severity-{insight.severity}"],
            "assignees": template.assignees,
            "priority": priority,
            "category": template.category,
            "metadata": metadata,
        }

    def _adjust_priority(self, base_priority: str, severity: str) -> str:
        """Adjust priority based on insight severity."""
        if severity == "critical":
            return "critical"
        elif severity == "high":
            return "high"
        elif severity == "medium":
            return base_priority
        else:  # low
            return "low"

    def _generate_description(self, insight: Insight, template: IssueTemplate) -> str:
        """Generate detailed issue description."""
        description = f"{template.description}\n\n"
        description += f"**Insight Details:**\n"
        description += f"- **Type:** {insight.insight_type}\n"
        description += f"- **Description:** {insight.description}\n"
        description += f"- **Confidence:** {insight.confidence:.2f}\n"
        description += f"- **Severity:** {insight.severity}\n"
        description += f"- **Category:** {insight.category}\n"
        description += f"- **Code Version:** {insight.code_version}\n"
        description += f"- **Timestamp:** {insight.timestamp}\n"

        if insight.metadata:
            description += f"\n**Additional Metadata:**\n"
            for key, value in insight.metadata.items():
                description += f"- **{key}:** {value}\n"

        if insight.linked_issues:
            description += f"\n**Linked Issues:**\n"
            for issue in insight.linked_issues:
                description += f"- {issue}\n"

        if insight.linked_insights:
            description += f"\n**Related Insights:**\n"
            for related_insight in insight.linked_insights:
                description += f"- {related_insight}\n"

        description += f"\n---\n"
        description += (
            f"*This issue was automatically generated by the LLM Testing Framework.*"
        )

        return description

    def _create_github_issue(self, issue_content: Dict[str, Any]) -> Optional[str]:
        """Create a GitHub issue."""
        try:
            import requests

            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            data = {
                "title": issue_content["title"],
                "body": issue_content["description"],
                "labels": issue_content["labels"],
            }

            if issue_content["assignees"]:
                data["assignees"] = issue_content["assignees"]

            url = f"https://api.github.com/repos/{self.github_repo}/issues"
            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 201:
                issue_data = response.json()
                issue_url = issue_data["html_url"]
                issue_number = issue_data["number"]
                print(f"✅ Created GitHub issue #{issue_number}: {issue_url}")
                return issue_url
            else:
                print(
                    f"❌ Failed to create GitHub issue: {response.status_code} - {response.text}"
                )
                return None

        except ImportError:
            print("❌ requests library not available for GitHub integration")
            return None
        except Exception as e:
            print(f"❌ Error creating GitHub issue: {e}")
            return None

    def _create_gitlab_issue(self, issue_content: Dict[str, Any]) -> Optional[str]:
        """Create a GitLab issue."""
        try:
            import requests

            headers = {
                "PRIVATE-TOKEN": self.gitlab_token,
                "Content-Type": "application/json",
            }

            data = {
                "title": issue_content["title"],
                "description": issue_content["description"],
                "labels": ",".join(issue_content["labels"]),
            }

            if issue_content["assignees"]:
                data["assignee_ids"] = issue_content["assignees"]

            url = f"https://gitlab.com/api/v4/projects/{self.gitlab_project}/issues"
            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 201:
                issue_data = response.json()
                issue_url = issue_data["web_url"]
                issue_iid = issue_data["iid"]
                print(f"✅ Created GitLab issue #{issue_iid}: {issue_url}")
                return issue_url
            else:
                print(
                    f"❌ Failed to create GitLab issue: {response.status_code} - {response.text}"
                )
                return None

        except ImportError:
            print("❌ requests library not available for GitLab integration")
            return None
        except Exception as e:
            print(f"❌ Error creating GitLab issue: {e}")
            return None

    def _create_local_issue(self, issue_content: Dict[str, Any]) -> str:
        """Create a local issue file."""
        try:
            # Create issues directory if it doesn't exist
            os.makedirs("issues", exist_ok=True)

            # Generate issue filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"issues/issue_{timestamp}.json"

            # Add creation timestamp
            issue_content["created_at"] = datetime.now().isoformat()
            issue_content["status"] = "open"

            # Write issue to file
            with open(filename, "w") as f:
                json.dump(issue_content, f, indent=2)

            print(f"✅ Created local issue: {filename}")
            return filename

        except Exception as e:
            print(f"❌ Error creating local issue: {e}")
            return ""

    def create_issues_from_insights(self, insights: List[Insight]) -> List[str]:
        """Create issues from multiple insights."""
        issue_urls = []

        for insight in insights:
            # Only create issues for high-confidence, high-severity insights
            if insight.confidence > 0.7 and insight.severity in ["high", "critical"]:
                issue_url = self.create_issue_from_insight(insight)
                if issue_url:
                    issue_urls.append(issue_url)

        return issue_urls

    def get_issue_status(self, issue_url: str) -> Optional[Dict[str, Any]]:
        """Get the status of an issue."""
        try:
            import requests

            if "github.com" in issue_url:
                return self._get_github_issue_status(issue_url)
            elif "gitlab.com" in issue_url:
                return self._get_gitlab_issue_status(issue_url)
            else:
                return self._get_local_issue_status(issue_url)

        except ImportError:
            print("❌ requests library not available for issue status checking")
            return None
        except Exception as e:
            print(f"❌ Error getting issue status: {e}")
            return None

    def _get_github_issue_status(self, issue_url: str) -> Optional[Dict[str, Any]]:
        """Get GitHub issue status."""
        try:
            import requests

            # Extract issue number from URL
            issue_number = issue_url.split("/")[-1]

            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            url = (
                f"https://api.github.com/repos/{self.github_repo}/issues/{issue_number}"
            )
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                issue_data = response.json()
                return {
                    "state": issue_data["state"],
                    "title": issue_data["title"],
                    "created_at": issue_data["created_at"],
                    "updated_at": issue_data["updated_at"],
                    "labels": [label["name"] for label in issue_data["labels"]],
                }
            else:
                return None

        except Exception as e:
            print(f"❌ Error getting GitHub issue status: {e}")
            return None

    def _get_gitlab_issue_status(self, issue_url: str) -> Optional[Dict[str, Any]]:
        """Get GitLab issue status."""
        try:
            import requests

            # Extract issue IID from URL
            issue_iid = issue_url.split("/")[-1]

            headers = {
                "PRIVATE-TOKEN": self.gitlab_token,
                "Content-Type": "application/json",
            }

            url = f"https://gitlab.com/api/v4/projects/{self.gitlab_project}/issues/{issue_iid}"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                issue_data = response.json()
                return {
                    "state": issue_data["state"],
                    "title": issue_data["title"],
                    "created_at": issue_data["created_at"],
                    "updated_at": issue_data["updated_at"],
                    "labels": issue_data["labels"],
                }
            else:
                return None

        except Exception as e:
            print(f"❌ Error getting GitLab issue status: {e}")
            return None

    def _get_local_issue_status(self, issue_path: str) -> Optional[Dict[str, Any]]:
        """Get local issue status."""
        try:
            with open(issue_path, "r") as f:
                issue_data = json.load(f)

            return {
                "state": issue_data.get("status", "unknown"),
                "title": issue_data.get("title", ""),
                "created_at": issue_data.get("created_at", ""),
                "updated_at": issue_data.get("updated_at", ""),
                "labels": issue_data.get("labels", []),
            }

        except Exception as e:
            print(f"❌ Error getting local issue status: {e}")
            return None

    def close_issue(self, issue_url: str, reason: str = "resolved") -> bool:
        """Close an issue."""
        try:
            if "github.com" in issue_url:
                return self._close_github_issue(issue_url, reason)
            elif "gitlab.com" in issue_url:
                return self._close_gitlab_issue(issue_url, reason)
            else:
                return self._close_local_issue(issue_url, reason)

        except Exception as e:
            print(f"❌ Error closing issue: {e}")
            return False

    def _close_github_issue(self, issue_url: str, reason: str) -> bool:
        """Close a GitHub issue."""
        try:
            import requests

            issue_number = issue_url.split("/")[-1]

            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            data = {"state": "closed", "body": f"Issue closed: {reason}"}

            url = (
                f"https://api.github.com/repos/{self.github_repo}/issues/{issue_number}"
            )
            response = requests.patch(url, headers=headers, json=data)

            return response.status_code == 200

        except Exception as e:
            print(f"❌ Error closing GitHub issue: {e}")
            return False

    def _close_gitlab_issue(self, issue_url: str, reason: str) -> bool:
        """Close a GitLab issue."""
        try:
            import requests

            issue_iid = issue_url.split("/")[-1]

            headers = {
                "PRIVATE-TOKEN": self.gitlab_token,
                "Content-Type": "application/json",
            }

            data = {"state_event": "close"}

            url = f"https://gitlab.com/api/v4/projects/{self.gitlab_project}/issues/{issue_iid}"
            response = requests.put(url, headers=headers, json=data)

            return response.status_code == 200

        except Exception as e:
            print(f"❌ Error closing GitLab issue: {e}")
            return False

    def _close_local_issue(self, issue_path: str, reason: str) -> bool:
        """Close a local issue."""
        try:
            with open(issue_path, "r") as f:
                issue_data = json.load(f)

            issue_data["status"] = "closed"
            issue_data["closed_at"] = datetime.now().isoformat()
            issue_data["close_reason"] = reason

            with open(issue_path, "w") as f:
                json.dump(issue_data, f, indent=2)

            return True

        except Exception as e:
            print(f"❌ Error closing local issue: {e}")
            return False
