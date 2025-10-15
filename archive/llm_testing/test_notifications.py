"""Tests for the notification system."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from llm_testing.notifications import (
    NotificationConfig,
    EmailNotifier,
    SlackNotifier,
    WebhookNotifier,
    NotificationManager,
    create_notification_config_from_dict,
)


class TestNotificationConfig:
    """Test NotificationConfig class."""

    def test_notification_config_defaults(self):
        """Test default configuration values."""
        config = NotificationConfig()

        assert config.email_enabled is False
        assert config.smtp_server == ""
        assert config.smtp_port == 587
        assert config.email_username == ""
        assert config.email_password == ""
        assert config.email_recipients == []

        assert config.slack_enabled is False
        assert config.slack_webhook_url == ""
        assert config.slack_channel == "#alerts"

        assert config.webhook_enabled is False
        assert config.webhook_url == ""
        assert config.webhook_headers == {}

    def test_notification_config_custom_values(self):
        """Test custom configuration values."""
        config = NotificationConfig(
            email_enabled=True,
            smtp_server="smtp.gmail.com",
            email_username="test@example.com",
            email_recipients=["alerts@example.com"],
            slack_enabled=True,
            slack_webhook_url="https://hooks.slack.com/test",
            webhook_enabled=True,
            webhook_url="https://api.example.com/webhook",
        )

        assert config.email_enabled is True
        assert config.smtp_server == "smtp.gmail.com"
        assert config.email_username == "test@example.com"
        assert config.email_recipients == ["alerts@example.com"]

        assert config.slack_enabled is True
        assert config.slack_webhook_url == "https://hooks.slack.com/test"

        assert config.webhook_enabled is True
        assert config.webhook_url == "https://api.example.com/webhook"


class TestEmailNotifier:
    """Test EmailNotifier class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = NotificationConfig(
            email_enabled=True,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            email_username="test@example.com",
            email_password="password123",
            email_recipients=["alerts@example.com"],
        )
        self.notifier = EmailNotifier(self.config)

    def test_email_notifier_initialization(self):
        """Test EmailNotifier initialization."""
        assert self.notifier.config == self.config

    def test_send_notification_disabled(self):
        """Test sending notification when email is disabled."""
        config = NotificationConfig(email_enabled=False)
        notifier = EmailNotifier(config)

        alert = {
            "severity": "high",
            "type": "test",
            "message": "Test alert",
        }

        result = notifier.send_notification(alert)
        assert result is False

    def test_send_notification_no_recipients(self):
        """Test sending notification with no recipients."""
        config = NotificationConfig(
            email_enabled=True,
            email_recipients=[],
        )
        notifier = EmailNotifier(config)

        alert = {
            "severity": "high",
            "type": "test",
            "message": "Test alert",
        }

        result = notifier.send_notification(alert)
        assert result is False

    @patch("smtplib.SMTP")
    def test_send_notification_success(self, mock_smtp):
        """Test successful email notification."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        alert = {
            "severity": "high",
            "type": "test",
            "message": "Test alert message",
        }

        result = self.notifier.send_notification(alert)

        assert result is True
        mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@example.com", "password123")
        mock_server.send_message.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_notification_failure(self, mock_smtp):
        """Test email notification failure."""
        mock_smtp.side_effect = Exception("SMTP error")

        alert = {
            "severity": "high",
            "type": "test",
            "message": "Test alert message",
        }

        result = self.notifier.send_notification(alert)

        assert result is False

    def test_create_html_content(self):
        """Test HTML content creation."""
        alert = {
            "severity": "critical",
            "type": "regression",
            "message": "Performance regression detected",
            "first_seen": "2024-01-01T12:00:00",
        }

        html_content = self.notifier._create_html_content(alert)

        assert "LLM Testing Alert" in html_content
        assert "CRITICAL" in html_content
        assert "regression" in html_content
        assert "Performance regression detected" in html_content
        assert "2024-01-01T12:00:00" in html_content


class TestSlackNotifier:
    """Test SlackNotifier class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = NotificationConfig(
            slack_enabled=True,
            slack_webhook_url="https://hooks.slack.com/test",
            slack_channel="#alerts",
        )
        self.notifier = SlackNotifier(self.config)

    def test_slack_notifier_initialization(self):
        """Test SlackNotifier initialization."""
        assert self.notifier.config == self.config

    def test_send_notification_disabled(self):
        """Test sending notification when Slack is disabled."""
        config = NotificationConfig(slack_enabled=False)
        notifier = SlackNotifier(config)

        alert = {
            "severity": "high",
            "type": "test",
            "message": "Test alert",
        }

        result = notifier.send_notification(alert)
        assert result is False

    def test_send_notification_no_webhook(self):
        """Test sending notification with no webhook URL."""
        config = NotificationConfig(
            slack_enabled=True,
            slack_webhook_url="",
        )
        notifier = SlackNotifier(config)

        alert = {
            "severity": "high",
            "type": "test",
            "message": "Test alert",
        }

        result = notifier.send_notification(alert)
        assert result is False

    @patch("llm_testing.notifications.requests")
    def test_send_notification_success(self, mock_requests):
        """Test successful Slack notification."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        alert = {
            "severity": "high",
            "type": "test",
            "message": "Test alert message",
        }

        result = self.notifier.send_notification(alert)

        assert result is True
        mock_requests.post.assert_called_once()

    @patch("llm_testing.notifications.requests")
    def test_send_notification_failure(self, mock_requests):
        """Test Slack notification failure."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_requests.post.return_value = mock_response

        alert = {
            "severity": "high",
            "type": "test",
            "message": "Test alert message",
        }

        result = self.notifier.send_notification(alert)

        assert result is False

    def test_create_slack_message(self):
        """Test Slack message creation."""
        alert = {
            "severity": "critical",
            "type": "regression",
            "message": "Performance regression detected",
            "first_seen": "2024-01-01T12:00:00",
        }

        message = self.notifier._create_slack_message(alert)

        assert message["channel"] == "#alerts"
        assert "attachments" in message
        assert len(message["attachments"]) == 1

        attachment = message["attachments"][0]
        assert "🚨" in attachment["title"]  # Critical emoji
        assert attachment["color"] == "#dc3545"  # Critical color

        # Check fields
        fields = attachment["fields"]
        field_titles = [field["title"] for field in fields]
        assert "Severity" in field_titles
        assert "Type" in field_titles
        assert "Message" in field_titles
        assert "Timestamp" in field_titles


class TestWebhookNotifier:
    """Test WebhookNotifier class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = NotificationConfig(
            webhook_enabled=True,
            webhook_url="https://api.example.com/webhook",
            webhook_headers={"Authorization": "Bearer token123"},
        )
        self.notifier = WebhookNotifier(self.config)

    def test_webhook_notifier_initialization(self):
        """Test WebhookNotifier initialization."""
        assert self.notifier.config == self.config

    def test_send_notification_disabled(self):
        """Test sending notification when webhook is disabled."""
        config = NotificationConfig(webhook_enabled=False)
        notifier = WebhookNotifier(config)

        alert = {
            "severity": "high",
            "type": "test",
            "message": "Test alert",
        }

        result = notifier.send_notification(alert)
        assert result is False

    def test_send_notification_no_url(self):
        """Test sending notification with no webhook URL."""
        config = NotificationConfig(
            webhook_enabled=True,
            webhook_url="",
        )
        notifier = WebhookNotifier(config)

        alert = {
            "severity": "high",
            "type": "test",
            "message": "Test alert",
        }

        result = notifier.send_notification(alert)
        assert result is False

    @patch("llm_testing.notifications.requests")
    def test_send_notification_success(self, mock_requests):
        """Test successful webhook notification."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        alert = {
            "severity": "high",
            "type": "test",
            "message": "Test alert message",
        }

        result = self.notifier.send_notification(alert)

        assert result is True
        mock_requests.post.assert_called_once()

    @patch("llm_testing.notifications.requests")
    def test_send_notification_success_201(self, mock_requests):
        """Test successful webhook notification with 201 status."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_requests.post.return_value = mock_response

        alert = {
            "severity": "high",
            "type": "test",
            "message": "Test alert message",
        }

        result = self.notifier.send_notification(alert)

        assert result is True

    @patch("llm_testing.notifications.requests")
    def test_send_notification_failure(self, mock_requests):
        """Test webhook notification failure."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_requests.post.return_value = mock_response

        alert = {
            "severity": "high",
            "type": "test",
            "message": "Test alert message",
        }

        result = self.notifier.send_notification(alert)

        assert result is False

    def test_create_webhook_payload(self):
        """Test webhook payload creation."""
        alert = {
            "severity": "critical",
            "type": "regression",
            "message": "Performance regression detected",
            "first_seen": "2024-01-01T12:00:00",
            "key": "test_key",
        }

        payload = self.notifier._create_webhook_payload(alert)

        assert payload["source"] == "llm_testing_framework"
        assert "timestamp" in payload
        assert "alert" in payload

        alert_data = payload["alert"]
        assert alert_data["severity"] == "critical"
        assert alert_data["type"] == "regression"
        assert alert_data["message"] == "Performance regression detected"
        assert alert_data["first_seen"] == "2024-01-01T12:00:00"
        assert alert_data["key"] == "test_key"


class TestNotificationManager:
    """Test NotificationManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = NotificationConfig(
            email_enabled=True,
            slack_enabled=True,
            webhook_enabled=True,
            smtp_server="smtp.gmail.com",
            email_username="test@example.com",
            email_password="password123",
            email_recipients=["alerts@example.com"],
            slack_webhook_url="https://hooks.slack.com/test",
            webhook_url="https://api.example.com/webhook",
        )
        self.manager = NotificationManager(self.config)

    def test_notification_manager_initialization(self):
        """Test NotificationManager initialization."""
        assert len(self.manager.providers) == 3
        provider_types = [
            type(provider).__name__ for provider in self.manager.providers
        ]
        assert "EmailNotifier" in provider_types
        assert "SlackNotifier" in provider_types
        assert "WebhookNotifier" in provider_types

    def test_notification_manager_no_providers(self):
        """Test NotificationManager with no providers enabled."""
        config = NotificationConfig()
        manager = NotificationManager(config)

        assert len(manager.providers) == 0

    @patch("llm_testing.notifications.requests")
    @patch("smtplib.SMTP")
    def test_send_notification_all_providers(self, mock_smtp, mock_requests):
        """Test sending notification through all providers."""
        # Mock email success
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Mock Slack success
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        alert = {
            "severity": "high",
            "type": "test",
            "message": "Test alert message",
        }

        results = self.manager.send_notification(alert)

        assert len(results) == 3
        assert results["email"] is True
        assert results["slack"] is True
        assert results["webhook"] is True

    def test_test_connections(self):
        """Test connection testing."""
        results = self.manager.test_connections()

        assert len(results) == 3
        assert "email" in results
        assert "slack" in results
        assert "webhook" in results


class TestNotificationConfigFactory:
    """Test notification config factory function."""

    def test_create_notification_config_from_dict(self):
        """Test creating NotificationConfig from dictionary."""
        config_dict = {
            "email_enabled": True,
            "smtp_server": "smtp.gmail.com",
            "email_username": "test@example.com",
            "email_recipients": ["alerts@example.com"],
            "slack_enabled": True,
            "slack_webhook_url": "https://hooks.slack.com/test",
            "webhook_enabled": True,
            "webhook_url": "https://api.example.com/webhook",
        }

        config = create_notification_config_from_dict(config_dict)

        assert config.email_enabled is True
        assert config.smtp_server == "smtp.gmail.com"
        assert config.email_username == "test@example.com"
        assert config.email_recipients == ["alerts@example.com"]

        assert config.slack_enabled is True
        assert config.slack_webhook_url == "https://hooks.slack.com/test"

        assert config.webhook_enabled is True
        assert config.webhook_url == "https://api.example.com/webhook"

    def test_create_notification_config_from_dict_defaults(self):
        """Test creating NotificationConfig with defaults."""
        config_dict = {}

        config = create_notification_config_from_dict(config_dict)

        assert config.email_enabled is False
        assert config.slack_enabled is False
        assert config.webhook_enabled is False
        assert config.email_recipients == []
        assert config.webhook_headers == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
