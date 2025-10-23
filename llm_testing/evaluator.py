from __future__ import annotations
from typing import Any, Dict, List
import json
import os
import re


def offline_eval(
    scenario: Dict[str, Any], transcript: Dict[str, Any]
) -> Dict[str, Any]:
    text = json.dumps(transcript)
    must = scenario.get("expectations", {}).get("must_contain", [])
    must_not = scenario.get("expectations", {}).get("must_not_contain", [])
    ok = True
    reasons: List[str] = []
    for s in must:
        if s and s not in text:
            ok = False
            reasons.append(f"missing:{s}")
    for s in must_not:
        if s and s in text:
            ok = False
            reasons.append(f"forbidden:{s}")
    score = 1.0 if ok else 0.0
    return {
        "scores": {"factual": score, "clarity": score, "safety": score},
        "ok": ok,
        "rationale": "; ".join(reasons),
    }


def evaluate(report_path: str) -> Dict[str, Any]:
    with open(report_path, "r") as f:
        rep = json.load(f)
    scenario = rep.get("scenario") or {}
    transcript = rep.get("transcript") or {}
    if os.getenv("OFFLINE_EVAL", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    } or not os.getenv("LLM_EVAL_API_KEY"):
        return offline_eval(scenario, transcript)
    # Placeholder for online eval (OpenAI). Keep offline by default in CI.
    return offline_eval(scenario, transcript)
