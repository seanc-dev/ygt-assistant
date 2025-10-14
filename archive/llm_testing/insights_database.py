"""Insights database for storing and retrieving testing insights."""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import asdict, dataclass


@dataclass
class Insight:
    """Represents a testing insight with metadata."""

    insight_id: str
    insight_type: str  # e.g., "performance", "accessibility", "regression"
    description: str
    confidence: float  # 0.0-1.0
    severity: str  # "low", "medium", "high", "critical"
    category: str  # e.g., "persona", "scenario", "system"
    code_version: str
    timestamp: str
    metadata: Dict[str, Any]
    linked_issues: List[str] = None
    linked_insights: List[str] = None

    def __post_init__(self):
        """Set default values after initialization."""
        if self.linked_issues is None:
            self.linked_issues = []
        if self.linked_insights is None:
            self.linked_insights = []
        if self.metadata is None:
            self.metadata = {}


class InsightsDatabase:
    """SQLite database for storing and retrieving testing insights."""

    def __init__(self, db_path: str = "llm_testing/insights.db"):
        """Initialize the insights database."""
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        """Create the insights table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS insights (
                    insight_id TEXT PRIMARY KEY,
                    insight_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    severity TEXT NOT NULL,
                    category TEXT NOT NULL,
                    code_version TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    linked_issues TEXT NOT NULL,
                    linked_insights TEXT NOT NULL
                )
            """
            )

            # Create indexes for efficient querying
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_insight_type ON insights(insight_type)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_category ON insights(category)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_code_version ON insights(code_version)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON insights(timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_severity ON insights(severity)"
            )

    def store_insight(self, insight: Insight) -> bool:
        """Store a new insight in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO insights 
                    (insight_id, insight_type, description, confidence, severity, 
                     category, code_version, timestamp, metadata, linked_issues, linked_insights)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        insight.insight_id,
                        insight.insight_type,
                        insight.description,
                        insight.confidence,
                        insight.severity,
                        insight.category,
                        insight.code_version,
                        insight.timestamp,
                        json.dumps(insight.metadata),
                        json.dumps(insight.linked_issues),
                        json.dumps(insight.linked_insights),
                    ),
                )
                return True
        except Exception as e:
            print(f"Error storing insight: {e}")
            return False

    def get_insight(self, insight_id: str) -> Optional[Insight]:
        """Retrieve a specific insight by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM insights WHERE insight_id = ?
                """,
                    (insight_id,),
                )
                row = cursor.fetchone()

                if row:
                    return Insight(
                        insight_id=row[0],
                        insight_type=row[1],
                        description=row[2],
                        confidence=row[3],
                        severity=row[4],
                        category=row[5],
                        code_version=row[6],
                        timestamp=row[7],
                        metadata=json.loads(row[8]),
                        linked_issues=json.loads(row[9]),
                        linked_insights=json.loads(row[10]),
                    )
                return None
        except Exception as e:
            print(f"Error retrieving insight: {e}")
            return None

    def get_insights_by_type(
        self, insight_type: str, limit: int = 100
    ) -> List[Insight]:
        """Get insights by type."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM insights 
                    WHERE insight_type = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """,
                    (insight_type, limit),
                )

                insights = []
                for row in cursor.fetchall():
                    insights.append(
                        Insight(
                            insight_id=row[0],
                            insight_type=row[1],
                            description=row[2],
                            confidence=row[3],
                            severity=row[4],
                            category=row[5],
                            code_version=row[6],
                            timestamp=row[7],
                            metadata=json.loads(row[8]),
                            linked_issues=json.loads(row[9]),
                            linked_insights=json.loads(row[10]),
                        )
                    )
                return insights
        except Exception as e:
            print(f"Error retrieving insights by type: {e}")
            return []

    def get_insights_by_category(
        self, category: str, limit: int = 100
    ) -> List[Insight]:
        """Get insights by category."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM insights 
                    WHERE category = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """,
                    (category, limit),
                )

                insights = []
                for row in cursor.fetchall():
                    insights.append(
                        Insight(
                            insight_id=row[0],
                            insight_type=row[1],
                            description=row[2],
                            confidence=row[3],
                            severity=row[4],
                            category=row[5],
                            code_version=row[6],
                            timestamp=row[7],
                            metadata=json.loads(row[8]),
                            linked_issues=json.loads(row[9]),
                            linked_insights=json.loads(row[10]),
                        )
                    )
                return insights
        except Exception as e:
            print(f"Error retrieving insights by category: {e}")
            return []

    def get_insights_by_version(
        self, code_version: str, limit: int = 100
    ) -> List[Insight]:
        """Get insights by code version."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM insights 
                    WHERE code_version = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """,
                    (code_version, limit),
                )

                insights = []
                for row in cursor.fetchall():
                    insights.append(
                        Insight(
                            insight_id=row[0],
                            insight_type=row[1],
                            description=row[2],
                            confidence=row[3],
                            severity=row[4],
                            category=row[5],
                            code_version=row[6],
                            timestamp=row[7],
                            metadata=json.loads(row[8]),
                            linked_issues=json.loads(row[9]),
                            linked_insights=json.loads(row[10]),
                        )
                    )
                return insights
        except Exception as e:
            print(f"Error retrieving insights by version: {e}")
            return []

    def get_recent_insights(self, days: int = 30, limit: int = 100) -> List[Insight]:
        """Get insights from the last N days."""
        try:
            cutoff_date = datetime.now().isoformat()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM insights 
                    WHERE timestamp >= datetime('now', '-{} days')
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """.format(
                        days
                    ),
                    (limit,),
                )

                insights = []
                for row in cursor.fetchall():
                    insights.append(
                        Insight(
                            insight_id=row[0],
                            insight_type=row[1],
                            description=row[2],
                            confidence=row[3],
                            severity=row[4],
                            category=row[5],
                            code_version=row[6],
                            timestamp=row[7],
                            metadata=json.loads(row[8]),
                            linked_issues=json.loads(row[9]),
                            linked_insights=json.loads(row[10]),
                        )
                    )
                return insights
        except Exception as e:
            print(f"Error retrieving recent insights: {e}")
            return []

    def get_high_confidence_insights(
        self, confidence_threshold: float = 0.8, limit: int = 100
    ) -> List[Insight]:
        """Get insights with confidence above threshold."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM insights 
                    WHERE confidence >= ? 
                    ORDER BY confidence DESC, timestamp DESC 
                    LIMIT ?
                """,
                    (confidence_threshold, limit),
                )

                insights = []
                for row in cursor.fetchall():
                    insights.append(
                        Insight(
                            insight_id=row[0],
                            insight_type=row[1],
                            description=row[2],
                            confidence=row[3],
                            severity=row[4],
                            category=row[5],
                            code_version=row[6],
                            timestamp=row[7],
                            metadata=json.loads(row[8]),
                            linked_issues=json.loads(row[9]),
                            linked_insights=json.loads(row[10]),
                        )
                    )
                return insights
        except Exception as e:
            print(f"Error retrieving high confidence insights: {e}")
            return []

    def get_insights_summary(self) -> Dict[str, Any]:
        """Get a summary of all insights."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get total count
                total = conn.execute("SELECT COUNT(*) FROM insights").fetchone()[0]

                # Get counts by type
                type_counts = {}
                cursor = conn.execute(
                    """
                    SELECT insight_type, COUNT(*) 
                    FROM insights 
                    GROUP BY insight_type
                """
                )
                for row in cursor.fetchall():
                    type_counts[row[0]] = row[1]

                # Get counts by severity
                severity_counts = {}
                cursor = conn.execute(
                    """
                    SELECT severity, COUNT(*) 
                    FROM insights 
                    GROUP BY severity
                """
                )
                for row in cursor.fetchall():
                    severity_counts[row[0]] = row[1]

                # Get average confidence
                avg_confidence = (
                    conn.execute("SELECT AVG(confidence) FROM insights").fetchone()[0]
                    or 0.0
                )

                return {
                    "total_insights": total,
                    "by_type": type_counts,
                    "by_severity": severity_counts,
                    "average_confidence": avg_confidence,
                    "recent_insights": len(self.get_recent_insights(days=7)),
                }
        except Exception as e:
            print(f"Error getting insights summary: {e}")
            return {
                "total_insights": 0,
                "by_type": {},
                "by_severity": {},
                "average_confidence": 0.0,
                "recent_insights": 0,
            }

    def delete_insight(self, insight_id: str) -> bool:
        """Delete an insight by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM insights WHERE insight_id = ?", (insight_id,))
                return True
        except Exception as e:
            print(f"Error deleting insight: {e}")
            return False

    def clear_old_insights(self, days: int = 90) -> int:
        """Clear insights older than N days. Returns number of deleted insights."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    DELETE FROM insights 
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(
                        days
                    )
                )
                return cursor.rowcount
        except Exception as e:
            print(f"Error clearing old insights: {e}")
            return 0
