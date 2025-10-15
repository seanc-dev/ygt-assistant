"""Evaluation loop for LLM-to-LLM testing framework."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from .config import TestingConfig
from .scenarios import Scenario
from .evaluator import ScoringAgent
from .types import EvaluationResult, ScenarioResult, BatchResult, EvaluationReport
from .database import ResultsDatabase
from .dashboard import Dashboard, AlertSystem


class EvaluationLoop:
    """Orchestrate the testing process and track results over time."""

    def __init__(
        self, assistant_client, scoring_agent: ScoringAgent, config: TestingConfig
    ):
        """Initialize the evaluation loop."""
        self.assistant = assistant_client
        self.scorer = scoring_agent
        self.config = config
        self.results_db = ResultsDatabase(config.results_storage)
        self.dashboard = Dashboard(self.results_db, config.alert_threshold)
        self.alert_system = AlertSystem(self.dashboard)

    def run_scenario(self, scenario: Scenario) -> ScenarioResult:
        """Execute a single scenario with the assistant."""
        results = []

        for prompt in scenario.test_prompts:
            # Call the actual assistant
            assistant_response = self._call_assistant(prompt.prompt, scenario)

            # Evaluate the response
            evaluation = self.scorer.evaluate_response(
                scenario, assistant_response, scenario.expected_behaviors
            )
            results.append(evaluation)

        # Calculate metrics
        if results:
            scores = [max(r.scores.values()) for r in results]
            success_rate = len([s for s in scores if s >= 3.5]) / len(scores)
            average_score = sum(scores) / len(scores)
        else:
            success_rate = 0.0
            average_score = 0.0

        # Store results in database
        for result in results:
            self.results_db.store_evaluation_result(result)

        # Store performance metrics
        if results:
            overall_score = sum(scores) / len(scores)
            self.results_db.store_performance_metric(
                "overall_score", overall_score, "unknown", "unknown"
            )

        return ScenarioResult(
            scenario=scenario,
            results=results,
            success_rate=success_rate,
            average_score=average_score,
            insights=self._generate_insights(
                [
                    ScenarioResult(
                        scenario=scenario,
                        results=results,
                        success_rate=success_rate,
                        average_score=average_score,
                        insights=[],
                    )
                ]
            ),
        )

    def run_batch(self, scenarios: List[Scenario]) -> BatchResult:
        """Run multiple scenarios and aggregate results."""
        all_results = []
        scenario_results = []

        for scenario in scenarios:
            scenario_result = self.run_scenario(scenario)
            scenario_results.append(scenario_result)
            all_results.extend(scenario_result.results)

        # Store batch result in database
        batch_result = BatchResult(
            batch_id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            scenarios=scenarios,
            results=all_results,
            summary={},
            insights=[],
            performance_alerts=[],
        )

        # Generate summary
        if all_results:
            all_scores = [max(r.scores.values()) for r in all_results]
            summary = {
                "total_scenarios": len(scenarios),
                "total_evaluations": len(all_results),
                "average_score": sum(all_scores) / len(all_scores),
                "success_rate": len([s for s in all_scores if s >= 3.5])
                / len(all_scores),
                "score_distribution": {
                    "excellent": len([s for s in all_scores if s >= 4.5]),
                    "good": len([s for s in all_scores if 3.5 <= s < 4.5]),
                    "fair": len([s for s in all_scores if 2.5 <= s < 3.5]),
                    "poor": len([s for s in all_scores if s < 2.5]),
                },
            }
        else:
            summary = {
                "total_scenarios": 0,
                "total_evaluations": 0,
                "average_score": 0.0,
                "success_rate": 0.0,
                "score_distribution": {"excellent": 0, "good": 0, "fair": 0, "poor": 0},
            }

        # Generate insights
        insights = self._generate_insights(scenario_results)

        # Check for performance alerts
        alerts = self._check_alerts(summary)

        return BatchResult(
            batch_id=f"batch_{len(scenarios)}_{len(all_results)}",
            scenarios=scenarios,
            results=all_results,
            summary=summary,
            insights=insights,
            performance_alerts=alerts,
        )

    def generate_report(self, results: BatchResult) -> EvaluationReport:
        """Generate a detailed evaluation report."""
        trends = self._analyze_trends(results)
        recommendations = self._generate_recommendations(results)
        alerts = results.performance_alerts

        return EvaluationReport(
            batch_result=results,
            trends=trends,
            recommendations=recommendations,
            alerts=alerts,
        )

    def _call_assistant(self, prompt: str, scenario: Scenario) -> str:
        """Call the assistant through the current FastAPI API via backend adapter.

        The adapter must be provided as `assistant_client` and expose methods for
        WhatsApp flows or direct actions. For free-text prompts, we simulate a
        WhatsApp text message payload.
        """
        try:
            backend = self.assistant
            # Simulate a WhatsApp text inbound payload
            payload = {
                "entry": [
                    {
                        "changes": [
                            {
                                "value": {
                                    "messages": [
                                        {"type": "text", "text": {"body": prompt}}
                                    ],
                                    "contacts": [{"wa_id": "tester"}],
                                }
                            }
                        ]
                    }
                ]
            }
            res = backend.whatsapp_post(payload)
            return str(res)
        except Exception as e:
            print(f"Assistant call failed: {e}")
            return f"Error calling assistant: {e}"

    def _generate_insights(self, scenario_results: List[ScenarioResult]) -> List[str]:
        """Generate insights from scenario results."""
        insights = []

        for result in scenario_results:
            # Analyze performance patterns
            if result.average_score < 3.0:
                insights.append(
                    f"Low performance in {result.scenario.name} (avg: {result.average_score:.2f})"
                )
            elif result.average_score > 4.5:
                insights.append(
                    f"Excellent performance in {result.scenario.name} (avg: {result.average_score:.2f})"
                )

            # Analyze success rate
            if result.success_rate < 0.5:
                insights.append(
                    f"Low success rate in {result.scenario.name} ({result.success_rate:.1%})"
                )

            # Analyze persona-specific patterns
            persona = result.scenario.persona.name
            if persona in ["Morgan", "Riley"]:  # Accessibility personas
                if result.average_score < 3.5:
                    insights.append(
                        f"Accessibility support needs improvement for {persona}"
                    )

        return insights if insights else ["No significant insights from this batch"]

    def _check_alerts(self, summary: Dict[str, Any]) -> List[str]:
        """Check for performance alerts."""
        alerts = []

        if summary["average_score"] < self.config.alert_threshold:
            alerts.append(
                f"Average score {summary['average_score']:.2f} below threshold {self.config.alert_threshold}"
            )

        if summary["success_rate"] < 0.7:
            alerts.append(f"Success rate {summary['success_rate']:.2f} below 70%")

        return alerts

    def _analyze_trends(self, results: BatchResult) -> Dict[str, Any]:
        """Analyze trends in the results."""
        if not results.results:
            return {
                "trend": "no_data",
                "improvement_rate": 0.0,
                "regression_detected": False,
            }

        # Calculate average scores by category
        category_scores = {}
        persona_scores = {}

        for result in results.results:
            # Group by scenario category
            scenario = next(
                (s for s in results.scenarios if s.name == result.scenario_name), None
            )
            if scenario:
                category = scenario.category
                if category not in category_scores:
                    category_scores[category] = []
                category_scores[category].append(max(result.scores.values()))

            # Group by persona
            persona = result.persona_name
            if persona not in persona_scores:
                persona_scores[persona] = []
            persona_scores[persona].append(max(result.scores.values()))

        # Calculate trends
        overall_avg = sum(max(r.scores.values()) for r in results.results) / len(
            results.results
        )

        # Identify weak areas
        weak_categories = [
            cat
            for cat, scores in category_scores.items()
            if sum(scores) / len(scores) < 3.5
        ]

        weak_personas = [
            persona
            for persona, scores in persona_scores.items()
            if sum(scores) / len(scores) < 3.5
        ]

        return {
            "trend": "stable" if overall_avg >= 3.5 else "declining",
            "improvement_rate": 0.0,  # Would need historical data for this
            "regression_detected": len(weak_categories) > 0 or len(weak_personas) > 0,
            "overall_average": overall_avg,
            "weak_categories": weak_categories,
            "weak_personas": weak_personas,
            "category_averages": {
                cat: sum(scores) / len(scores)
                for cat, scores in category_scores.items()
            },
            "persona_averages": {
                persona: sum(scores) / len(scores)
                for persona, scores in persona_scores.items()
            },
        }

    def _generate_recommendations(self, results: BatchResult) -> List[str]:
        """Generate recommendations based on results."""
        recommendations = []

        if not results.results:
            return ["No recommendations - no data available"]

        # Analyze trends
        trends = self._analyze_trends(results)

        # Generate recommendations based on weak areas
        if trends["weak_categories"]:
            for category in trends["weak_categories"]:
                recommendations.append(f"Improve performance in {category} scenarios")

        if trends["weak_personas"]:
            for persona in trends["weak_personas"]:
                recommendations.append(f"Enhance support for {persona} persona")

        # Check for accessibility issues
        accessibility_personas = ["Morgan", "Riley"]
        for persona in accessibility_personas:
            if persona in trends["persona_averages"]:
                avg_score = trends["persona_averages"][persona]
                if avg_score < 3.5:
                    recommendations.append(
                        f"Improve accessibility support (current avg: {avg_score:.2f})"
                    )

        # Check for overall performance
        if trends["overall_average"] < 3.5:
            recommendations.append("Overall performance needs improvement")
        elif trends["overall_average"] > 4.5:
            recommendations.append(
                "Excellent performance - consider expanding test scenarios"
            )

        # Check for consistency issues
        scores = [max(r.scores.values()) for r in results.results]
        score_variance = sum(
            (s - trends["overall_average"]) ** 2 for s in scores
        ) / len(scores)
        if score_variance > 1.0:
            recommendations.append(
                "High score variance - improve consistency across scenarios"
            )

        return (
            recommendations
            if recommendations
            else ["Continue current approach - performance is good"]
        )
