"""Database module for LLM testing framework results and insights."""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import asdict
from .types import EvaluationResult, BatchResult, ScenarioResult


class ResultsDatabase:
    """SQLite database for storing test results and insights."""

    def __init__(self, db_path: str = "llm_testing/results.db"):
        """Initialize the database."""
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evaluation_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scenario_name TEXT NOT NULL,
                    persona_name TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    assistant_response TEXT NOT NULL,
                    scores TEXT NOT NULL,  -- JSON
                    intermediate_scores TEXT,  -- JSON
                    feedback TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    code_version TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    metadata TEXT,  -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS batch_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT UNIQUE NOT NULL,
                    scenarios TEXT NOT NULL,  -- JSON
                    results TEXT NOT NULL,  -- JSON
                    summary TEXT NOT NULL,  -- JSON
                    insights TEXT,  -- JSON
                    performance_alerts TEXT,  -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    insight_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    evidence TEXT,  -- JSON
                    recommendations TEXT,  -- JSON
                    timestamp TEXT NOT NULL,
                    code_version TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    linked_issues TEXT,  -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS performance_trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    code_version TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

    def store_evaluation_result(self, result: EvaluationResult):
        """Store a single evaluation result."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO evaluation_results (
                    scenario_name, persona_name, prompt, assistant_response,
                    scores, intermediate_scores, feedback, timestamp,
                    code_version, model_version, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    result.scenario_name,
                    result.persona_name,
                    result.prompt,
                    result.assistant_response,
                    json.dumps(result.scores),
                    json.dumps(result.intermediate_scores),
                    result.feedback,
                    result.timestamp,
                    result.code_version,
                    result.model_version,
                    json.dumps(result.metadata),
                ),
            )

    def store_batch_result(self, batch_result: BatchResult):
        """Store a batch result."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO batch_results (
                    batch_id, scenarios, results, summary, insights, performance_alerts
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    batch_result.batch_id,
                    json.dumps([asdict(s) for s in batch_result.scenarios]),
                    json.dumps([asdict(r) for r in batch_result.results]),
                    json.dumps(batch_result.summary),
                    json.dumps(batch_result.insights),
                    json.dumps(batch_result.performance_alerts),
                ),
            )

    def store_insight(self, insight: Dict[str, Any]):
        """Store an insight."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO insights (
                    insight_type, description, confidence, evidence,
                    recommendations, timestamp, code_version, model_version, linked_issues
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    insight["insight_type"],
                    insight["description"],
                    insight["confidence"],
                    json.dumps(insight.get("evidence", [])),
                    json.dumps(insight.get("recommendations", [])),
                    insight["timestamp"],
                    insight["code_version"],
                    insight["model_version"],
                    json.dumps(insight.get("linked_issues", [])),
                ),
            )

    def store_performance_metric(
        self, metric_name: str, value: float, code_version: str, model_version: str
    ):
        """Store a performance metric for trend analysis."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO performance_trends (
                    metric_name, value, timestamp, code_version, model_version
                ) VALUES (?, ?, ?, ?, ?)
            """,
                (
                    metric_name,
                    value,
                    datetime.now().isoformat(),
                    code_version,
                    model_version,
                ),
            )

    def get_recent_results(self, limit: int = 100) -> List[EvaluationResult]:
        """Get recent evaluation results."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM evaluation_results 
                ORDER BY created_at DESC 
                LIMIT ?
            """,
                (limit,),
            )

            results = []
            for row in cursor.fetchall():
                result = EvaluationResult(
                    scenario_name=row[1],
                    persona_name=row[2],
                    prompt=row[3],
                    assistant_response=row[4],
                    scores=json.loads(row[5]),
                    intermediate_scores=json.loads(row[6]) if row[6] else {},
                    feedback=row[7],
                    timestamp=row[8],
                    code_version=row[9],
                    model_version=row[10],
                    metadata=json.loads(row[11]) if row[11] else {},
                )
                results.append(result)

            return results

    def get_performance_trends(
        self, metric_name: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get performance trends for a specific metric."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT value, timestamp, code_version, model_version 
                FROM performance_trends 
                WHERE metric_name = ? 
                AND created_at >= datetime('now', '-{} days')
                ORDER BY created_at ASC
            """.format(
                    days
                ),
                (metric_name,),
            )

            trends = []
            for row in cursor.fetchall():
                trends.append(
                    {
                        "value": row[0],
                        "timestamp": row[1],
                        "code_version": row[2],
                        "model_version": row[3],
                    }
                )

            return trends

    def get_insights_by_type(
        self, insight_type: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get insights by type."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM insights 
                WHERE insight_type = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """,
                (insight_type, limit),
            )

            insights = []
            for row in cursor.fetchall():
                insights.append(
                    {
                        "insight_type": row[1],
                        "description": row[2],
                        "confidence": row[3],
                        "evidence": json.loads(row[4]) if row[4] else [],
                        "recommendations": json.loads(row[5]) if row[5] else [],
                        "timestamp": row[6],
                        "code_version": row[7],
                        "model_version": row[8],
                        "linked_issues": json.loads(row[9]) if row[9] else [],
                    }
                )

            return insights

    def get_average_scores_by_scenario(self, days: int = 7) -> Dict[str, float]:
        """Get average scores by scenario for recent results."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT scenario_name, AVG(CAST(json_extract(scores, '$.overall') AS REAL)) as avg_score
                FROM evaluation_results 
                WHERE created_at >= datetime('now', '-{} days')
                GROUP BY scenario_name
                ORDER BY avg_score DESC
            """.format(
                    days
                )
            )

            return {row[0]: row[1] for row in cursor.fetchall()}

    def get_regression_alerts(self, threshold: float = 0.1) -> List[Dict[str, Any]]:
        """Detect performance regressions."""
        # Get recent performance trends and compare with historical data
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT metric_name, AVG(value) as recent_avg
                FROM performance_trends 
                WHERE created_at >= datetime('now', '-7 days')
                GROUP BY metric_name
            """
            )

            recent_metrics = {row[0]: row[1] for row in cursor.fetchall()}

            alerts = []
            for metric_name, recent_avg in recent_metrics.items():
                # Compare with historical average
                cursor = conn.execute(
                    """
                    SELECT AVG(value) as historical_avg
                    FROM performance_trends 
                    WHERE metric_name = ? 
                    AND created_at < datetime('now', '-7 days')
                    AND created_at >= datetime('now', '-30 days')
                """,
                    (metric_name,),
                )

                historical_avg = cursor.fetchone()[0]
                if (
                    historical_avg
                    and (historical_avg - recent_avg) / historical_avg > threshold
                ):
                    alerts.append(
                        {
                            "metric_name": metric_name,
                            "recent_avg": recent_avg,
                            "historical_avg": historical_avg,
                            "regression_percentage": (historical_avg - recent_avg)
                            / historical_avg
                            * 100,
                        }
                    )

            return alerts
