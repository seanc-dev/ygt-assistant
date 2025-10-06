"""Shared data types for the LLM testing framework."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class EvaluationResult:
    """Result of evaluating an assistant response."""

    scenario_name: str
    persona_name: str
    prompt: str
    assistant_response: str
    scores: Dict[str, float]
    intermediate_scores: Dict[str, List[float]]  # For regression tracking
    feedback: str
    timestamp: str
    code_version: str
    model_version: str
    metadata: Dict[str, Any]

    def __post_init__(self):
        """Set default values after initialization."""
        if self.intermediate_scores is None:
            self.intermediate_scores = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ScenarioResult:
    """Result of running a single scenario."""

    scenario: Any  # Scenario type
    results: List[EvaluationResult]
    success_rate: float
    average_score: float
    insights: List[str]


@dataclass
class BatchResult:
    """Result of running a batch of scenarios."""

    batch_id: str
    scenarios: List[Any]  # List[Scenario]
    results: List[EvaluationResult]
    summary: Dict[str, Any]
    insights: List[str]
    performance_alerts: List[str]


@dataclass
class EvaluationReport:
    """Detailed evaluation report."""

    batch_result: BatchResult
    trends: Dict[str, Any]
    recommendations: List[str]
    alerts: List[str]
