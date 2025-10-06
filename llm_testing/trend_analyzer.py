"""Trend analyzer for LLM testing framework performance analysis."""

import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json
from .types import EvaluationResult, BatchResult
from .insights_database import InsightsDatabase, Insight


@dataclass
class TrendPoint:
    """Represents a single data point in a trend analysis."""

    timestamp: datetime
    value: float
    metadata: Dict[str, Any]
    confidence: float = 1.0


@dataclass
class TrendAnalysis:
    """Represents the result of a trend analysis."""

    trend_type: str  # "improving", "declining", "stable", "regression"
    confidence: float  # 0.0-1.0
    slope: float  # Rate of change
    r_squared: float  # Goodness of fit
    data_points: List[TrendPoint]
    insights: List[str]
    recommendations: List[str]
    severity: str  # "low", "medium", "high", "critical"


class TrendAnalyzer:
    """Analyzes performance trends and detects regressions in LLM testing results."""

    def __init__(self, insights_db: InsightsDatabase):
        """Initialize the trend analyzer."""
        self.insights_db = insights_db
        self.regression_threshold = 0.1  # 10% decline threshold
        self.confidence_threshold = 0.8  # Minimum confidence for insights

    def analyze_performance_trends(
        self, results: List[EvaluationResult], time_window: int = 30
    ) -> Dict[str, TrendAnalysis]:
        """Analyze performance trends across different dimensions."""

        trends = {}

        # Analyze overall score trends
        trends["overall_score"] = self._analyze_score_trend(results, "overall")

        # Analyze individual criteria trends
        criteria = ["clarity", "helpfulness", "accuracy", "relevance", "completeness"]
        for criterion in criteria:
            trends[f"{criterion}_score"] = self._analyze_score_trend(results, criterion)

        # Analyze persona-specific trends
        persona_trends = self._analyze_persona_trends(results, time_window)
        trends.update(persona_trends)

        # Analyze scenario-specific trends
        scenario_trends = self._analyze_scenario_trends(results, time_window)
        trends.update(scenario_trends)

        return trends

    def _analyze_score_trend(
        self, results: List[EvaluationResult], score_type: str
    ) -> TrendAnalysis:
        """Analyze trends for a specific score type."""

        # Extract data points
        data_points = []
        for result in results:
            if score_type == "overall":
                score = max(result.scores.values()) if result.scores else 0.0
            else:
                score = result.scores.get(score_type, 0.0)

            data_points.append(
                TrendPoint(
                    timestamp=datetime.fromisoformat(result.timestamp),
                    value=score,
                    metadata={
                        "persona": result.persona_name,
                        "scenario": result.scenario_name,
                    },
                    confidence=1.0,
                )
            )

        # Sort by timestamp
        data_points.sort(key=lambda x: x.timestamp)

        if len(data_points) < 3:
            return TrendAnalysis(
                trend_type="insufficient_data",
                confidence=0.0,
                slope=0.0,
                r_squared=0.0,
                data_points=data_points,
                insights=["Insufficient data for trend analysis"],
                recommendations=["Collect more data points"],
                severity="low",
            )

        # Calculate trend statistics
        x_values = [
            (dp.timestamp - data_points[0].timestamp).total_seconds()
            for dp in data_points
        ]
        y_values = [dp.value for dp in data_points]

        slope, r_squared = self._calculate_linear_trend(x_values, y_values)

        # Determine trend type
        trend_type = self._classify_trend(slope, r_squared)

        # Generate insights and recommendations
        insights = self._generate_trend_insights(
            score_type, slope, r_squared, data_points
        )
        recommendations = self._generate_trend_recommendations(
            score_type, trend_type, slope
        )

        # Calculate confidence
        confidence = min(1.0, r_squared * len(data_points) / 10.0)

        # Determine severity
        severity = self._determine_severity(slope, r_squared, len(data_points))

        return TrendAnalysis(
            trend_type=trend_type,
            confidence=confidence,
            slope=slope,
            r_squared=r_squared,
            data_points=data_points,
            insights=insights,
            recommendations=recommendations,
            severity=severity,
        )

    def _calculate_linear_trend(
        self, x_values: List[float], y_values: List[float]
    ) -> Tuple[float, float]:
        """Calculate linear regression slope and R-squared."""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0, 0.0

        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        sum_y2 = sum(y * y for y in y_values)

        # Calculate slope
        numerator = n * sum_xy - sum_x * sum_y
        denominator = n * sum_x2 - sum_x * sum_x

        if denominator == 0:
            return 0.0, 0.0

        slope = numerator / denominator

        # Calculate R-squared
        y_mean = sum_y / n
        ss_tot = sum((y - y_mean) ** 2 for y in y_values)

        if ss_tot == 0:
            r_squared = 1.0
        else:
            y_pred = [slope * x + (sum_y - slope * sum_x) / n for x in x_values]
            ss_res = sum((y - pred) ** 2 for y, pred in zip(y_values, y_pred))
            r_squared = 1 - (ss_res / ss_tot)

        return slope, r_squared

    def _classify_trend(self, slope: float, r_squared: float) -> str:
        """Classify the trend based on slope and R-squared."""
        if r_squared < 0.3:
            return "unclear"
        elif slope > 0.005:  # More sensitive threshold
            return "improving"
        elif slope < -0.005:  # More sensitive threshold
            return "declining"
        else:
            return "stable"

    def _determine_severity(
        self, slope: float, r_squared: float, data_points: int
    ) -> str:
        """Determine the severity of a trend."""
        if r_squared < 0.3 or data_points < 5:
            return "low"
        elif slope < -0.05:  # Significant decline
            return "critical"
        elif slope < -0.02:  # Moderate decline
            return "high"
        elif slope < -0.01:  # Slight decline
            return "medium"
        else:
            return "low"

    def _generate_trend_insights(
        self,
        score_type: str,
        slope: float,
        r_squared: float,
        data_points: List[TrendPoint],
    ) -> List[str]:
        """Generate insights based on trend analysis."""
        insights = []

        if r_squared > 0.7:
            if slope > 0.02:
                insights.append(f"{score_type} scores showing strong improvement trend")
            elif slope < -0.02:
                insights.append(f"{score_type} scores showing concerning decline")
            else:
                insights.append(f"{score_type} scores remaining stable")

        if len(data_points) > 10:
            recent_avg = statistics.mean([dp.value for dp in data_points[-5:]])
            overall_avg = statistics.mean([dp.value for dp in data_points])

            if recent_avg > overall_avg + 0.5:
                insights.append(
                    f"Recent {score_type} performance above historical average"
                )
            elif recent_avg < overall_avg - 0.5:
                insights.append(
                    f"Recent {score_type} performance below historical average"
                )

        return insights

    def _generate_trend_recommendations(
        self, score_type: str, trend_type: str, slope: float
    ) -> List[str]:
        """Generate recommendations based on trend analysis."""
        recommendations = []

        if trend_type == "declining":
            if score_type == "clarity":
                recommendations.append("Review and improve prompt clarity")
                recommendations.append("Consider adding more context to responses")
            elif score_type == "helpfulness":
                recommendations.append("Enhance response utility and actionability")
                recommendations.append("Add more specific guidance in responses")
            elif score_type == "accuracy":
                recommendations.append("Improve fact-checking and validation")
                recommendations.append("Enhance error handling and edge cases")

        if slope < -0.03:
            recommendations.append(
                "Investigate recent changes that may have caused regression"
            )
            recommendations.append("Consider rolling back recent modifications")

        if trend_type == "improving":
            recommendations.append("Continue current practices that are working well")
            recommendations.append("Document successful patterns for replication")

        return recommendations

    def _analyze_persona_trends(
        self, results: List[EvaluationResult], time_window: int
    ) -> Dict[str, TrendAnalysis]:
        """Analyze trends for specific personas."""
        persona_trends = {}

        # Group results by persona
        persona_results = {}
        for result in results:
            persona = result.persona_name
            if persona not in persona_results:
                persona_results[persona] = []
            persona_results[persona].append(result)

        # Analyze each persona
        for persona, persona_result_list in persona_results.items():
            if len(persona_result_list) >= 3:
                trend = self._analyze_score_trend(persona_result_list, "overall")
                trend.insights.append(f"Analysis for persona: {persona}")
                persona_trends[f"persona_{persona}"] = trend

        return persona_trends

    def _analyze_scenario_trends(
        self, results: List[EvaluationResult], time_window: int
    ) -> Dict[str, TrendAnalysis]:
        """Analyze trends for specific scenarios."""
        scenario_trends = {}

        # Group results by scenario
        scenario_results = {}
        for result in results:
            scenario = result.scenario_name
            if scenario not in scenario_results:
                scenario_results[scenario] = []
            scenario_results[scenario].append(result)

        # Analyze each scenario
        for scenario, scenario_result_list in scenario_results.items():
            if len(scenario_result_list) >= 3:
                trend = self._analyze_score_trend(scenario_result_list, "overall")
                trend.insights.append(f"Analysis for scenario: {scenario}")
                scenario_trends[f"scenario_{scenario}"] = trend

        return scenario_trends

    def detect_regressions(
        self,
        recent_results: List[EvaluationResult],
        baseline_results: List[EvaluationResult],
    ) -> List[Dict[str, Any]]:
        """Detect regressions by comparing recent results to baseline."""
        regressions = []

        # Calculate baseline statistics
        baseline_scores = {}
        for result in baseline_results:
            for criterion, score in result.scores.items():
                if criterion not in baseline_scores:
                    baseline_scores[criterion] = []
                baseline_scores[criterion].append(score)

        baseline_means = {
            criterion: statistics.mean(scores)
            for criterion, scores in baseline_scores.items()
        }

        # Compare recent results to baseline
        for result in recent_results:
            for criterion, score in result.scores.items():
                if criterion in baseline_means:
                    baseline_mean = baseline_means[criterion]
                    decline = baseline_mean - score
                    decline_percentage = (decline / baseline_mean) * 100

                    if decline_percentage > 10:  # 10% decline threshold
                        regressions.append(
                            {
                                "criterion": criterion,
                                "baseline_score": baseline_mean,
                                "current_score": score,
                                "decline_percentage": decline_percentage,
                                "persona": result.persona_name,
                                "scenario": result.scenario_name,
                                "timestamp": result.timestamp,
                                "severity": (
                                    "high" if decline_percentage > 20 else "medium"
                                ),
                            }
                        )

        return regressions

    def generate_trend_insights(
        self, trends: Dict[str, TrendAnalysis]
    ) -> List[Insight]:
        """Generate insights from trend analysis."""
        insights = []

        for trend_name, trend in trends.items():
            if trend.confidence > self.confidence_threshold:
                insight = Insight(
                    insight_id=f"trend_{trend_name}_{datetime.now().isoformat()}",
                    insight_type="trend_analysis",
                    description=f"Trend analysis for {trend_name}: {trend.trend_type}",
                    confidence=trend.confidence,
                    severity=trend.severity,
                    category="performance",
                    code_version="0.1.0",
                    timestamp=datetime.now().isoformat(),
                    metadata={
                        "trend_name": trend_name,
                        "trend_type": trend.trend_type,
                        "slope": trend.slope,
                        "r_squared": trend.r_squared,
                        "data_points": len(trend.data_points),
                        "insights": trend.insights,
                        "recommendations": trend.recommendations,
                    },
                    linked_issues=[],
                    linked_insights=[],
                )
                insights.append(insight)

        return insights

    def get_performance_summary(
        self, results: List[EvaluationResult]
    ) -> Dict[str, Any]:
        """Generate a comprehensive performance summary."""
        if not results:
            return {"error": "No results to analyze"}

        # Calculate overall statistics
        all_scores = []
        for result in results:
            all_scores.extend(result.scores.values())

        summary = {
            "total_tests": len(results),
            "average_score": statistics.mean(all_scores) if all_scores else 0.0,
            "score_std": statistics.stdev(all_scores) if len(all_scores) > 1 else 0.0,
            "min_score": min(all_scores) if all_scores else 0.0,
            "max_score": max(all_scores) if all_scores else 0.0,
            "score_distribution": self._calculate_score_distribution(all_scores),
            "persona_performance": self._calculate_persona_performance(results),
            "scenario_performance": self._calculate_scenario_performance(results),
            "criteria_performance": self._calculate_criteria_performance(results),
            "trends": self.analyze_performance_trends(results),
        }

        return summary

    def _calculate_score_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculate the distribution of scores."""
        distribution = {"excellent": 0, "good": 0, "average": 0, "poor": 0}

        for score in scores:
            if score >= 4.5:
                distribution["excellent"] += 1
            elif score >= 3.5:
                distribution["good"] += 1
            elif score >= 2.5:
                distribution["average"] += 1
            else:
                distribution["poor"] += 1

        return distribution

    def _calculate_persona_performance(
        self, results: List[EvaluationResult]
    ) -> Dict[str, float]:
        """Calculate average performance by persona."""
        persona_scores = {}

        for result in results:
            if result.persona_name not in persona_scores:
                persona_scores[result.persona_name] = []
            persona_scores[result.persona_name].extend(result.scores.values())

        return {
            persona: statistics.mean(scores)
            for persona, scores in persona_scores.items()
        }

    def _calculate_scenario_performance(
        self, results: List[EvaluationResult]
    ) -> Dict[str, float]:
        """Calculate average performance by scenario."""
        scenario_scores = {}

        for result in results:
            if result.scenario_name not in scenario_scores:
                scenario_scores[result.scenario_name] = []
            scenario_scores[result.scenario_name].extend(result.scores.values())

        return {
            scenario: statistics.mean(scores)
            for scenario, scores in scenario_scores.items()
        }

    def _calculate_criteria_performance(
        self, results: List[EvaluationResult]
    ) -> Dict[str, float]:
        """Calculate average performance by criteria."""
        criteria_scores = {}

        for result in results:
            for criterion, score in result.scores.items():
                if criterion not in criteria_scores:
                    criteria_scores[criterion] = []
                criteria_scores[criterion].append(score)

        return {
            criterion: statistics.mean(scores)
            for criterion, scores in criteria_scores.items()
        }
