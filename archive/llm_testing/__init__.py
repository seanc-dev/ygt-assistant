"""LLM-to-LLM Testing Framework for Calendar Assistant."""

from .config import TestingConfig
from .personas import Persona, get_all_personas
from .scenarios import Scenario, get_all_scenarios
from .prompts import TestPrompt, PromptTemplate
from .evaluator import ScoringAgent
from .evaluation_loop import EvaluationLoop
from .meta_tracker import MetaTracker
from .database import ResultsDatabase
from .dashboard import Dashboard, AlertSystem
from .insights_database import InsightsDatabase

__version__ = "0.1.0"
__all__ = [
    # Configuration
    "TestingConfig",
    # Test components
    "Persona",
    "get_all_personas",
    "Scenario",
    "get_all_scenarios",
    "TestPrompt",
    "PromptTemplate",
    # Evaluation
    "ScoringAgent",
    "EvaluationLoop",
    # Analysis and tracking
    "MetaTracker",
    "ResultsDatabase",
    "Dashboard",
    "AlertSystem",
    "InsightsDatabase",
]
