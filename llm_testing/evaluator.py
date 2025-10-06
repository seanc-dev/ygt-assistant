"""Scoring agent for LLM-to-LLM testing framework."""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from .config import TestingConfig
from .scenarios import Scenario, ExpectedBehavior
from .types import EvaluationResult

# Import OpenAI client
try:
    from openai_client import client

    OPENAI_AVAILABLE = client is not None
except ImportError:
    OPENAI_AVAILABLE = False


class ScoringAgent:
    """A third LLM that reviews assistant outputs against goals and explains failures."""

    def __init__(self, config: TestingConfig):
        """Initialize the scoring agent."""
        self.primary_model = config.scoring_model
        self.fallback_model = config.fallback_model
        self.config = config
        self.rubric = self._load_rubric()
        self.calibration_data = self._load_calibration()

    def _load_rubric(self) -> Dict[str, Any]:
        """Load the evaluation rubric."""
        return {
            "clarity": {
                "weight": 0.2,
                "description": "How clear and understandable is the response?",
            },
            "helpfulness": {
                "weight": 0.25,
                "description": "Does the response address the user's needs?",
            },
            "efficiency": {
                "weight": 0.15,
                "description": "Is the response concise and actionable?",
            },
            "accuracy": {
                "weight": 0.2,
                "description": "Are the suggestions and information correct?",
            },
            "persona_alignment": {
                "weight": 0.1,
                "description": "Does the response match the persona's style?",
            },
            "goal_achievement": {
                "weight": 0.1,
                "description": "Does the response advance the user's goals?",
            },
            "accessibility": {
                "weight": 0.1,
                "description": "How well does it accommodate accessibility needs?",
            },
            "error_handling": {
                "weight": 0.1,
                "description": "How gracefully does it handle invalid inputs?",
            },
        }

    def _load_calibration(self) -> Dict[str, Any]:
        """Load calibration data for bias prevention."""
        return {
            "verbose_penalty": 0.0,  # Don't penalize verbose but helpful responses
            "bias_detection": True,
            "confidence_threshold": 0.7,
        }

    def evaluate_response(
        self,
        scenario: Scenario,
        assistant_response: str,
        expected_behaviors: List[ExpectedBehavior],
    ) -> EvaluationResult:
        """Evaluate an assistant response against the scenario."""
        if not OPENAI_AVAILABLE:
            # Fallback to placeholder evaluation
            return self._evaluate_placeholder(scenario, assistant_response)

        try:
            # Route to appropriate model based on difficulty
            model = self._route_to_model(scenario.difficulty, {})

            # Create evaluation prompt
            evaluation_prompt = self._create_evaluation_prompt(
                scenario, assistant_response, expected_behaviors
            )

            # Call OpenAI for evaluation
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert evaluator of AI assistant responses. Evaluate the response based on the given criteria and provide detailed scores and feedback.",
                    },
                    {"role": "user", "content": evaluation_prompt},
                ],
                temperature=0.1,
                max_tokens=1000,
            )

            # Parse the response
            evaluation_text = response.choices[0].message.content
            scores, feedback = self._parse_evaluation_response(evaluation_text)

            # Detect bias
            bias_info = self._detect_bias(assistant_response, scores)

            return EvaluationResult(
                scenario_name=scenario.name,
                persona_name=scenario.persona.name,
                prompt=scenario.test_prompts[0].prompt if scenario.test_prompts else "",
                assistant_response=assistant_response,
                scores=scores,
                intermediate_scores={},
                feedback=feedback,
                timestamp=datetime.now().isoformat(),
                code_version="0.1.0",
                model_version=model,
                metadata={
                    "evaluation_method": "llm",
                    "bias_detected": bias_info["bias_detected"],
                    "confidence": bias_info["confidence"],
                },
            )

        except Exception as e:
            # Fallback to placeholder evaluation on error
            print(f"LLM evaluation failed: {e}")
            return self._evaluate_placeholder(scenario, assistant_response)

    def _evaluate_placeholder(
        self, scenario: Scenario, assistant_response: str
    ) -> EvaluationResult:
        """Fallback placeholder evaluation when LLM is not available."""
        scores = {
            "clarity": 4.0,
            "helpfulness": 4.0,
            "efficiency": 3.5,
            "accuracy": 4.0,
            "persona_alignment": 4.0,
            "goal_achievement": 4.0,
            "accessibility": 4.0,
            "error_handling": 4.0,
        }

        return EvaluationResult(
            scenario_name=scenario.name,
            persona_name=scenario.persona.name,
            prompt=scenario.test_prompts[0].prompt if scenario.test_prompts else "",
            assistant_response=assistant_response,
            scores=scores,
            intermediate_scores={},
            feedback="Placeholder feedback - LLM evaluation not available",
            timestamp=datetime.now().isoformat(),
            code_version="0.1.0",
            model_version=self.primary_model,
            metadata={"evaluation_method": "placeholder"},
        )

    def _create_evaluation_prompt(
        self,
        scenario: Scenario,
        assistant_response: str,
        expected_behaviors: List[ExpectedBehavior],
    ) -> str:
        """Create a detailed evaluation prompt for the LLM."""
        rubric_text = "\n".join(
            [
                f"- {category}: {details['description']} (weight: {details['weight']})"
                for category, details in self.rubric.items()
            ]
        )

        expected_behaviors_text = "\n".join(
            [
                f"- {behavior.description} (importance: {behavior.importance})"
                for behavior in expected_behaviors
            ]
        )

        return f"""
Evaluate this AI assistant response based on the following criteria:

SCENARIO: {scenario.name}
PERSONA: {scenario.persona.name}
GOALS: {', '.join(scenario.goals)}
DIFFICULTY: {scenario.difficulty}

USER PROMPT: {scenario.test_prompts[0].prompt if scenario.test_prompts else "N/A"}

ASSISTANT RESPONSE: {assistant_response}

EVALUATION CRITERIA:
{rubric_text}

EXPECTED BEHAVIORS:
{expected_behaviors_text}

Please provide:
1. Scores for each criterion (1-5 scale, where 5 is excellent)
2. Detailed feedback explaining your scores
3. Overall assessment of how well the response meets the scenario goals

Respond in JSON format:
{{
    "scores": {{
        "clarity": <score>,
        "helpfulness": <score>,
        "efficiency": <score>,
        "accuracy": <score>,
        "persona_alignment": <score>,
        "goal_achievement": <score>,
        "accessibility": <score>,
        "error_handling": <score>
    }},
    "feedback": "<detailed feedback>",
    "overall_assessment": "<overall assessment>"
}}
"""

    def _parse_evaluation_response(
        self, response_text: str
    ) -> tuple[Dict[str, float], str]:
        """Parse the LLM evaluation response."""
        try:
            # Try to extract JSON from the response
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                json_text = response_text[start_idx:end_idx]
                data = json.loads(json_text)
                scores = data.get("scores", {})
                feedback = data.get("feedback", "No feedback provided")
                return scores, feedback
        except (json.JSONDecodeError, KeyError):
            pass

        # Fallback: return default scores and use response as feedback
        default_scores = {
            "clarity": 3.0,
            "helpfulness": 3.0,
            "efficiency": 3.0,
            "accuracy": 3.0,
            "persona_alignment": 3.0,
            "goal_achievement": 3.0,
            "accessibility": 3.0,
            "error_handling": 3.0,
        }
        return default_scores, response_text

    def _route_to_model(self, difficulty: str, scores: Dict[str, float]) -> str:
        """Route evaluation to appropriate model based on difficulty and scores."""
        if difficulty == "easy" or (
            scores and max(scores.values()) > self.config.low_stakes_threshold
        ):
            return self.fallback_model
        else:
            return self.primary_model

    def _generate_detailed_feedback(
        self, scenario: Scenario, response: str, scores: Dict[str, float]
    ) -> str:
        """Generate detailed feedback for the response."""
        if not OPENAI_AVAILABLE:
            return "Detailed feedback not available - LLM evaluation disabled"

        try:
            feedback_prompt = f"""
Analyze this AI assistant response and provide detailed, constructive feedback:

SCENARIO: {scenario.name}
PERSONA: {scenario.persona.name}
USER PROMPT: {scenario.test_prompts[0].prompt if scenario.test_prompts else "N/A"}
ASSISTANT RESPONSE: {response}
SCORES: {scores}

Provide detailed feedback covering:
1. What the response did well
2. Areas for improvement
3. Specific suggestions for better performance
4. How well it aligned with the persona and goals
5. Any missed opportunities or errors

Keep feedback constructive and actionable.
"""

            response_obj = client.chat.completions.create(
                model=self.fallback_model,  # Use cheaper model for feedback
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert AI evaluator providing detailed, constructive feedback.",
                    },
                    {"role": "user", "content": feedback_prompt},
                ],
                temperature=0.3,
                max_tokens=800,
            )

            return response_obj.choices[0].message.content

        except Exception as e:
            return f"Feedback generation failed: {e}"

    def _detect_bias(self, response: str, scores: Dict[str, float]) -> Dict[str, Any]:
        """Detect potential bias in the evaluation."""
        if not OPENAI_AVAILABLE:
            return {
                "bias_detected": False,
                "confidence": 0.5,
                "reason": "LLM not available",
            }

        try:
            bias_prompt = f"""
Analyze this evaluation for potential bias:

ASSISTANT RESPONSE: {response}
EVALUATION SCORES: {scores}

Check for:
1. Unconscious bias in scoring
2. Inconsistent evaluation criteria
3. Over-penalization of certain response styles
4. Cultural or demographic bias
5. Confirmation bias in evaluation

Provide analysis in JSON format:
{{
    "bias_detected": <true/false>,
    "confidence": <0.0-1.0>,
    "bias_types": ["<list of detected bias types>"],
    "explanation": "<detailed explanation>",
    "recommendations": ["<list of recommendations>"]
}}
"""

            response_obj = client.chat.completions.create(
                model=self.fallback_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in detecting evaluation bias and ensuring fair assessment.",
                    },
                    {"role": "user", "content": bias_prompt},
                ],
                temperature=0.1,
                max_tokens=600,
            )

            bias_text = response_obj.choices[0].message.content

            # Try to parse JSON response
            try:
                start_idx = bias_text.find("{")
                end_idx = bias_text.rfind("}") + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_text = bias_text[start_idx:end_idx]
                    bias_data = json.loads(json_text)
                    return bias_data
            except (json.JSONDecodeError, KeyError):
                pass

            # Fallback: basic bias detection
            return {
                "bias_detected": False,
                "confidence": 0.7,
                "reason": "Could not parse bias analysis response",
            }

        except Exception as e:
            return {
                "bias_detected": False,
                "confidence": 0.5,
                "reason": f"Bias detection failed: {e}",
            }
