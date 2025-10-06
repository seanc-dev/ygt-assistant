"""Dashboard and alert system for LLM testing framework."""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import asdict
from .database import ResultsDatabase
from .types import BatchResult, EvaluationReport
from .notifications import NotificationManager, create_notification_config_from_dict


class Dashboard:
    """Real-time dashboard for LLM testing metrics and alerts."""

    def __init__(self, db: ResultsDatabase, alert_threshold: float = 3.5):
        """Initialize the dashboard."""
        self.db = db
        self.alert_threshold = alert_threshold
        self.alerts = []

    def get_key_metrics(self) -> Dict[str, Any]:
        """Get key metrics for the dashboard."""
        recent_results = self.db.get_recent_results(limit=100)

        if not recent_results:
            return {
                "total_tests": 0,
                "average_score": 0.0,
                "success_rate": 0.0,
                "recent_trend": "no_data",
                "alerts": [],
            }

        # Calculate metrics
        total_tests = len(recent_results)
        scores = [max(r.scores.values()) for r in recent_results]
        average_score = sum(scores) / len(scores)
        success_rate = len([s for s in scores if s >= self.alert_threshold]) / len(
            scores
        )

        # Calculate recent trend (last 7 days vs previous 7 days)
        week_ago = datetime.now().replace(tzinfo=None) - timedelta(days=7)
        recent_scores = [
            max(r.scores.values())
            for r in recent_results
            if datetime.fromisoformat(r.timestamp.replace("Z", "+00:00")).replace(
                tzinfo=None
            )
            >= week_ago
        ]
        older_scores = [
            max(r.scores.values())
            for r in recent_results
            if datetime.fromisoformat(r.timestamp.replace("Z", "+00:00")).replace(
                tzinfo=None
            )
            < week_ago
        ]

        if recent_scores and older_scores:
            recent_avg = sum(recent_scores) / len(recent_scores)
            older_avg = sum(older_scores) / len(older_scores)
            if recent_avg > older_avg:
                trend = "improving"
            elif recent_avg < older_avg:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        # Get alerts
        alerts = self._get_alerts(recent_results)

        return {
            "total_tests": total_tests,
            "average_score": round(average_score, 2),
            "success_rate": round(success_rate * 100, 1),
            "recent_trend": trend,
            "alerts": alerts,
            "last_updated": datetime.now().isoformat(),
        }

    def get_scenario_performance(self) -> Dict[str, float]:
        """Get performance breakdown by scenario."""
        return self.db.get_average_scores_by_scenario(days=7)

    def get_persona_performance(self) -> Dict[str, float]:
        """Get performance breakdown by persona."""
        recent_results = self.db.get_recent_results(limit=100)

        persona_scores = {}
        for result in recent_results:
            persona = result.persona_name
            score = max(result.scores.values())

            if persona not in persona_scores:
                persona_scores[persona] = []
            persona_scores[persona].append(score)

        # Calculate averages
        return {
            persona: sum(scores) / len(scores)
            for persona, scores in persona_scores.items()
        }

    def get_performance_trends(
        self, metric_name: str = "overall_score", days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get performance trends for a specific metric."""
        return self.db.get_performance_trends(metric_name, days)

    def get_regression_alerts(self) -> List[Dict[str, Any]]:
        """Get regression alerts."""
        return self.db.get_regression_alerts()

    def get_insights_summary(self) -> Dict[str, Any]:
        """Get summary of recent insights."""
        insight_types = [
            "performance_pattern",
            "user_experience",
            "feature_gap",
            "accessibility",
        ]

        insights_summary = {}
        for insight_type in insight_types:
            insights = self.db.get_insights_by_type(insight_type, limit=10)
            insights_summary[insight_type] = {
                "count": len(insights),
                "recent": insights[:3] if insights else [],
            }

        return insights_summary

    def _get_alerts(self, recent_results: List) -> List[Dict[str, Any]]:
        """Generate alerts based on recent results."""
        alerts = []

        if not recent_results:
            return alerts

        # Check for low average score
        scores = [max(r.scores.values()) for r in recent_results]
        avg_score = sum(scores) / len(scores)
        if avg_score < self.alert_threshold:
            alerts.append(
                {
                    "type": "low_score",
                    "message": f"Average score ({avg_score:.2f}) below threshold ({self.alert_threshold})",
                    "severity": "high" if avg_score < 3.0 else "medium",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Check for high failure rate
        failure_rate = len([s for s in scores if s < 3.0]) / len(scores)
        if failure_rate > 0.2:  # More than 20% failures
            alerts.append(
                {
                    "type": "high_failure_rate",
                    "message": f"High failure rate: {failure_rate:.1%} of tests failed",
                    "severity": "high",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Check for specific scenario issues
        scenario_scores = {}
        for result in recent_results:
            scenario = result.scenario_name
            score = max(result.scores.values())

            if scenario not in scenario_scores:
                scenario_scores[scenario] = []
            scenario_scores[scenario].append(score)

        for scenario, scores_list in scenario_scores.items():
            avg_scenario_score = sum(scores_list) / len(scores_list)
            if avg_scenario_score < 3.0:
                alerts.append(
                    {
                        "type": "scenario_issue",
                        "message": f"Scenario '{scenario}' performing poorly (avg: {avg_scenario_score:.2f})",
                        "severity": "medium",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return alerts

    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate complete dashboard data."""
        key_metrics = self.get_key_metrics()
        scenario_performance = self.get_scenario_performance()
        persona_performance = self.get_persona_performance()
        insights_summary = self.get_insights_summary()
        regression_alerts = self.get_regression_alerts()

        return {
            "key_metrics": key_metrics,
            "scenario_performance": scenario_performance,
            "persona_performance": persona_performance,
            "insights_summary": insights_summary,
            "regression_alerts": regression_alerts,
            "last_updated": datetime.now().isoformat(),
        }

    def export_dashboard_json(self, filepath: str = "llm_testing/dashboard.json"):
        """Export dashboard data to JSON file."""
        dashboard_data = self.generate_dashboard_data()

        with open(filepath, "w") as f:
            json.dump(dashboard_data, f, indent=2, default=str)

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of all active alerts."""
        key_metrics = self.get_key_metrics()
        regression_alerts = self.get_regression_alerts()

        all_alerts = key_metrics["alerts"] + regression_alerts

        return {
            "total_alerts": len(all_alerts),
            "high_severity": len(
                [a for a in all_alerts if a.get("severity") == "high"]
            ),
            "medium_severity": len(
                [a for a in all_alerts if a.get("severity") == "medium"]
            ),
            "low_severity": len([a for a in all_alerts if a.get("severity") == "low"]),
            "alerts": all_alerts,
        }


class AlertSystem:
    """Alert system for monitoring test performance."""

    def __init__(
        self, dashboard: Dashboard, notification_config: Dict[str, Any] = None
    ):
        """Initialize the alert system."""
        self.dashboard = dashboard
        self.notification_config = notification_config or {}
        self.alert_history = []

        # Initialize notification manager
        config = create_notification_config_from_dict(self.notification_config)
        self.notification_manager = NotificationManager(config)

    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for new alerts and return them."""
        alert_summary = self.dashboard.get_alert_summary()
        new_alerts = []

        for alert in alert_summary["alerts"]:
            # Check if this is a new alert (not in history)
            alert_key = f"{alert['type']}_{alert.get('message', '')[:50]}"

            if not any(a.get("key") == alert_key for a in self.alert_history):
                alert["key"] = alert_key
                alert["first_seen"] = datetime.now().isoformat()
                self.alert_history.append(alert)
                new_alerts.append(alert)

        return new_alerts

    def send_notification(self, alert: Dict[str, Any]):
        """Send notification for an alert."""
        # Send through notification manager
        results = self.notification_manager.send_notification(alert)

        # Log results
        for provider, success in results.items():
            if success:
                print(f"✅ {provider.capitalize()} notification sent successfully")
            else:
                print(f"❌ Failed to send {provider} notification")

        # Fallback to console if no providers configured
        if not any(results.values()):
            print(f"ALERT: {alert['severity'].upper()} - {alert['message']}")

    def process_alerts(self):
        """Process all new alerts."""
        new_alerts = self.check_alerts()

        for alert in new_alerts:
            self.send_notification(alert)

            # Store alert in database
            self.dashboard.db.store_insight(
                {
                    "insight_type": "alert",
                    "description": alert["message"],
                    "confidence": 0.9,
                    "evidence": [alert],
                    "recommendations": [f"Investigate {alert['type']} issue"],
                    "timestamp": datetime.now().isoformat(),
                    "code_version": "unknown",
                    "model_version": "unknown",
                }
            )

    def get_alert_history(self) -> List[Dict[str, Any]]:
        """Get alert history."""
        return self.alert_history

    def clear_resolved_alerts(self):
        """Clear alerts that are no longer active."""
        current_alerts = self.dashboard.get_alert_summary()["alerts"]
        current_keys = {a.get("key") for a in current_alerts}

        # Keep only alerts that are still active
        self.alert_history = [
            alert for alert in self.alert_history if alert.get("key") in current_keys
        ]
