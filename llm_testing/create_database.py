"""Script to create and demonstrate the LLM testing database."""

import os
from llm_testing.database import ResultsDatabase
from llm_testing.config import TestingConfig
from llm_testing.types import EvaluationResult
from datetime import datetime


def main():
    """Create and populate the database with sample data."""
    print("Creating LLM testing database...")

    # Create database
    db = ResultsDatabase()

    # Show where the database was created
    db_path = os.path.abspath(db.db_path)
    print(f"Database created at: {db_path}")

    # Add some sample data
    print("Adding sample evaluation results...")

    sample_result = EvaluationResult(
        scenario_name="Sample Scenario",
        persona_name="Test Persona",
        prompt="Schedule a meeting for tomorrow",
        assistant_response="I'll schedule a meeting for tomorrow at 2pm.",
        scores={"clarity": 4.0, "helpfulness": 4.5, "efficiency": 3.8},
        intermediate_scores={},
        feedback="Good response, clear and helpful",
        timestamp=datetime.now().isoformat(),
        code_version="1.0.0",
        model_version="gpt-4",
        metadata={"test": True},
    )

    db.store_evaluation_result(sample_result)

    # Store a performance metric
    db.store_performance_metric("overall_score", 4.1, "1.0.0", "gpt-4")

    # Store an insight
    insight = {
        "insight_type": "performance_pattern",
        "description": "Assistant performs well on scheduling tasks",
        "confidence": 0.85,
        "evidence": ["High scores on clarity and helpfulness"],
        "recommendations": ["Continue with current approach"],
        "timestamp": datetime.now().isoformat(),
        "code_version": "1.0.0",
        "model_version": "gpt-4",
        "linked_issues": [],
    }
    db.store_insight(insight)

    # Verify data was stored
    recent_results = db.get_recent_results(limit=10)
    print(f"Stored {len(recent_results)} evaluation results")

    # Show database file size
    if os.path.exists(db.db_path):
        size = os.path.getsize(db.db_path)
        print(f"Database file size: {size} bytes")

    print("Database setup complete!")


if __name__ == "__main__":
    main()
