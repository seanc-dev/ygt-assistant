"""Configuration for LLM-to-LLM Testing Framework."""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class TestingConfig:
    """Configuration for the LLM-to-LLM testing framework."""

    # Model Configuration
    scoring_model: str = "gpt-4"
    fallback_model: str = "gpt-3.5-turbo"
    max_tokens: int = 1000
    temperature: float = 0.1

    # Testing Configuration
    batch_size: int = 10
    evaluation_timeout: int = 30

    # Storage Configuration
    results_storage: str = "llm_testing/results.db"  # SQLite for performance
    insights_storage: str = "llm_testing/insights.db"

    # Dashboard and Alerts
    dashboard_url: str = "http://localhost:3000"
    alert_threshold: float = 3.5

    # Integration Configuration
    ci_integration: bool = True
    version_tracking: bool = True

    # Cost Management
    max_cost_per_batch: float = 10.0  # USD
    low_stakes_threshold: float = 3.0  # Use cheaper model for scores above this

    # Calibration
    calibration_samples: int = 100
    bias_detection_enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "scoring_model": self.scoring_model,
            "fallback_model": self.fallback_model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "batch_size": self.batch_size,
            "evaluation_timeout": self.evaluation_timeout,
            "results_storage": self.results_storage,
            "insights_storage": self.insights_storage,
            "dashboard_url": self.dashboard_url,
            "alert_threshold": self.alert_threshold,
            "ci_integration": self.ci_integration,
            "version_tracking": self.version_tracking,
            "max_cost_per_batch": self.max_cost_per_batch,
            "low_stakes_threshold": self.low_stakes_threshold,
            "calibration_samples": self.calibration_samples,
            "bias_detection_enabled": self.bias_detection_enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestingConfig":
        """Create config from dictionary."""
        return cls(**data)

    def validate(self) -> bool:
        """Validate configuration values."""
        if self.alert_threshold < 0 or self.alert_threshold > 5:
            return False
        if self.batch_size < 1:
            return False
        if self.max_tokens < 1:
            return False
        if self.temperature < 0 or self.temperature > 2:
            return False
        return True
