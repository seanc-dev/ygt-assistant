"""
LLM Testing Evaluator

This module implements the evaluation strategy for LLM e2e tests:

1. **Chat Responses** (non-deterministic):
   - Uses agent evaluator (GPT-4o-mini) when LLM_EVAL_API_KEY is available
   - Assesses suitability, safety, and clarity of LLM-generated chat responses
   - Falls back to offline string matching (must_contain/must_not_contain) if unavailable
   - Full transcript snapshots are NOT enforced with live LLM (responses vary)

2. **Operations** (deterministic):
   - Uses deterministic validation via _assess_function_calling()
   - Validates structure (op, params fields), enums, and user intent matching
   - Operation snapshots only enforced with fixtures (LLM_TESTING_MODE=true)
   - Always validates enum values and required parameters

3. **Infrastructure** (fixtures):
   - Uses LLM_TESTING_MODE=true (deterministic fixtures)
   - Full transcript snapshots enforced for regression testing
   - Tests HTTP flow, JSONPath extraction, database operations, execution logic
   - No live LLM calls - pure infrastructure validation
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import json
import os
import re
from datetime import datetime
from pathlib import Path

try:  # Prefer shared client if present
    from openai_client import client as _shared_openai_client  # type: ignore
except ImportError:  # pragma: no cover - optional
    _shared_openai_client = None
try:
    from openai import OpenAI as _OpenAI  # type: ignore
except ImportError:  # pragma: no cover - optional
    _OpenAI = None

PRIORITY_VALUES = {"low", "medium", "high", "urgent"}
TASK_STATUS_VALUES = {"backlog", "ready", "doing", "blocked", "done", "todo"}
ACTION_STATE_VALUES = {
    "queued",
    "deferred",
    "completed",
    "dismissed",
    "converted_to_task",
}


def _normalize_for_snapshot(obj: Any) -> Any:
    """Normalize object for snapshot comparison by replacing timestamps and UUIDs."""
    if isinstance(obj, dict):
        return {k: _normalize_for_snapshot(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_normalize_for_snapshot(item) for item in obj]
    elif isinstance(obj, str):
        # Replace ISO timestamps
        obj = re.sub(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?",
            "<timestamp>",
            obj,
        )
        # Replace UUIDs (8+ hex chars)
        obj = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "<uuid>",
            obj,
            flags=re.IGNORECASE,
        )
        obj = re.sub(r"[0-9a-f]{8,}", "<uuid>", obj, flags=re.IGNORECASE)
        return obj
    return obj


def _extract_operation_responses(transcript: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract operation responses from assistant-suggest endpoints.
    
    Returns list of normalized operation response dicts.
    """
    operation_responses = []
    steps = transcript.get("steps", [])
    
    for step in steps:
        endpoint = step.get("endpoint", "")
        if endpoint and "assistant-suggest" in endpoint:
            resp = step.get("response", {})
            if isinstance(resp, dict) and "operations" in resp:
                # Extract just the operation-related fields (deterministic)
                op_response = {
                    "ok": resp.get("ok"),
                    "operations": resp.get("operations", []),
                    "applied": resp.get("applied", []),
                    "pending": resp.get("pending", []),
                    "errors": resp.get("errors", []),
                }
                # Normalize for snapshot (remove UUIDs, timestamps from operation params)
                operation_responses.append(_normalize_for_snapshot(op_response))
    
    return operation_responses


def _compare_operation_snapshots(
    operation_responses: List[Dict[str, Any]], snapshot_path: str
) -> Dict[str, Any]:
    """Compare operation responses against stored snapshot.
    
    Returns:
        Dict with "match" (bool), "diff" (str if mismatch)
    """
    snapshot_file = Path("llm_testing") / "snapshots" / snapshot_path
    
    if not snapshot_file.exists():
        # First run - save snapshot
        snapshot_file.parent.mkdir(parents=True, exist_ok=True)
        with open(snapshot_file, "w") as f:
            json.dump(operation_responses, f, indent=2)
        return {
            "match": True,
            "diff": None,
            "message": "Operation snapshot created",
        }
    
    # Load and compare
    with open(snapshot_file, "r") as f:
        stored = json.load(f)
    
    if operation_responses == stored:
        return {
            "match": True,
            "diff": None,
        }
    
    # Generate diff
    import difflib
    
    stored_str = json.dumps(stored, indent=2).splitlines(keepends=True)
    current_str = json.dumps(operation_responses, indent=2).splitlines(keepends=True)
    diff = "".join(
        difflib.unified_diff(
            stored_str, current_str, fromfile="stored", tofile="current"
        )
    )
    
    return {
        "match": False,
        "diff": diff,
    }


def _validate_deterministic_params(
    op: Dict[str, Any], user_message: str, scenario: Dict[str, Any]
) -> List[str]:
    """Validate deterministic aspects of operation parameters.
    
    For example:
    - "defer to next week" -> defer_until should be in next week
    - "update status to done" -> status should be "done"
    - "create task" -> should have title
    
    Returns list of validation errors.
    """
    reasons: List[str] = []
    op_type = op.get("op")
    params = op.get("params", {})

    def _normalized_enum(field: str, allowed: set[str]) -> Optional[str]:
        value = params.get(field)
        if value is None:
            return None
        normalized = str(value).strip().lower()
        if normalized not in allowed:
            reasons.append(
                f"{op_type} invalid {field} '{value}' (allowed: {', '.join(sorted(allowed))})"
            )
            return None
        return normalized
    
    # Validate defer_until dates
    if "defer_until" in params and params["defer_until"]:
        defer_until = params["defer_until"]
        if isinstance(defer_until, str) and defer_until:
            try:
                from datetime import datetime, date
                from zoneinfo import ZoneInfo
                
                # Parse defer_until (could be ISO datetime or just date)
                if "T" in defer_until or "+" in defer_until or "Z" in defer_until:
                    defer_dt = datetime.fromisoformat(defer_until.replace("Z", "+00:00"))
                    defer_date = defer_dt.date()
                else:
                    # Just a date string like "2023-11-06"
                    defer_date = date.fromisoformat(defer_until)
                    defer_dt = datetime.combine(defer_date, datetime.min.time())
                
                # Get current date (use UTC for consistency)
                now = datetime.now(ZoneInfo("UTC"))
                today = now.date()
                
                # Check if user mentioned "next week"
                msg_lower = user_message.lower()
                if "next week" in msg_lower or "following week" in msg_lower:
                    # defer_until should be in the next week (Monday to Friday)
                    days_ahead = (defer_date - today).days
                    # Next week is roughly 5-14 days ahead (accounting for current day of week)
                    # More precisely: if today is Monday, next week starts in 7 days
                    # If today is Friday, next week starts in 3 days
                    if days_ahead < 3 or days_ahead > 14:
                        reasons.append(
                            f"defer_until date ({defer_until[:10]}) not in next week range (days_ahead: {days_ahead})"
                        )
                    # Should be a weekday (Monday=0, Friday=4)
                    if defer_date.weekday() >= 5:
                        reasons.append(f"defer_until date is not a weekday: {defer_until[:10]}")
                
                # Check if user mentioned "tomorrow"
                if "tomorrow" in msg_lower:
                    days_ahead = (defer_date - today).days
                    # Tomorrow is 1 day ahead, but could be 2 if today is Friday (next Monday)
                    if days_ahead < 1 or days_ahead > 3:
                        reasons.append(
                            f"defer_until date ({defer_until[:10]}) not tomorrow (days_ahead: {days_ahead})"
                        )
                
            except (ValueError, AttributeError) as e:
                reasons.append(f"invalid defer_until format: {defer_until} ({e})")
    
    _normalized_enum("priority", PRIORITY_VALUES)
    status_normalized = _normalized_enum("status", TASK_STATUS_VALUES)
    _normalized_enum("state", ACTION_STATE_VALUES)

    # Validate status values match user intent (only with live LLM, not fixtures)
    # With fixtures, operations are deterministic and may not match user message exactly
    use_fixtures = os.getenv("LLM_TESTING_MODE", "false").lower() in {
        "1", "true", "yes", "on"
    }
    if (
        not use_fixtures
        and op_type == "update_task_status"
        and status_normalized is not None
    ):
        status = status_normalized
        msg_lower = user_message.lower()
        
        if "done" in msg_lower or "complete" in msg_lower or "finished" in msg_lower:
            if status not in ["done", "completed"]:
                reasons.append(f"expected status 'done' but got '{status}'")
        elif "doing" in msg_lower or "in progress" in msg_lower or "start" in msg_lower:
            if status not in ["doing", "in_progress"]:
                reasons.append(f"expected status 'doing' but got '{status}'")
        elif "todo" in msg_lower or "not started" in msg_lower:
            if status not in ["todo", "not_started"]:
                reasons.append(f"expected status 'todo' but got '{status}'")
    
    # Validate create_task has title
    if op_type == "create_task":
        if "title" not in params or not params.get("title"):
            reasons.append("create_task missing required 'title' parameter")
        # priority already checked via _normalized_enum
    
    return reasons


def _assess_function_calling(
    transcript: Dict[str, Any], function_calling: Dict[str, Any], scenario: Dict[str, Any] = None
) -> tuple[bool, List[str]]:
    """Assess function calling correctness in transcript.
    
    Returns:
        (is_valid, list_of_reasons)
    """
    reasons: List[str] = []
    steps = transcript.get("steps", [])
    scenario = scenario or {}
    
    # Find assistant-suggest responses and user messages
    operations_found = False
    user_messages = []
    
    for step in steps:
        endpoint = step.get("endpoint", "")
        # Collect user messages from requests
        if endpoint and "assistant-suggest" in endpoint:
            # Get user message from request body
            request_body = step.get("request_body") or step.get("body") or {}
            if isinstance(request_body, dict):
                msg = request_body.get("message") or request_body.get("content")
                if msg:
                    user_messages.append(msg)
        
        # HTTP steps have endpoint set (action may be None or "http")
        if endpoint and "assistant-suggest" in endpoint:
            resp = step.get("response", {})
            if isinstance(resp, dict) and "operations" in resp:
                operations_found = True
                ops = resp.get("operations", [])
                applied = resp.get("applied", [])
                pending = resp.get("pending", [])
                
                # Check operations structure
                if not isinstance(ops, list) or len(ops) == 0:
                    reasons.append("no_operations_generated")
                    continue
                
                # Check each operation has required fields
                for op in ops:
                    if not isinstance(op, dict):
                        reasons.append("invalid_operation_structure")
                        continue
                    if "op" not in op:
                        reasons.append("operation_missing_op_field")
                    if "params" not in op:
                        reasons.append("operation_missing_params_field")
                
                # Validate deterministic parameters
                if user_messages:
                    # Use the most recent user message for validation
                    user_message = user_messages[-1] if user_messages else ""
                    for op in ops:
                        if isinstance(op, dict):
                            param_errors = _validate_deterministic_params(
                                op, user_message, scenario
                            )
                            reasons.extend(param_errors)
                
                # Check expected behavior
                expected_behavior = function_calling.get("expected_behavior")
                if expected_behavior == "operations_should_be_pending":
                    # In training_wheels mode, medium/high-risk operations should be pending
                    # Low-risk operations (like chat) can be applied
                    # Check if any medium/high-risk operations were applied
                    medium_high_risk_ops = ["create_task", "update_task_status", "link_action_to_task", "update_action_state"]
                    applied_medium_high = [op for op in applied if op.get("op") in medium_high_risk_ops]
                    if applied_medium_high:
                        reasons.append(f"medium/high_risk_operations_applied_in_training_wheels_mode: {[op.get('op') for op in applied_medium_high]}")
                elif expected_behavior == "operations_should_be_applied":
                    if len(applied) == 0 and len(pending) > 0:
                        reasons.append("operations_not_applied_in_autonomous_mode")
                
                # Check expected operation types (if specified - optional)
                expected_ops = function_calling.get("expected_operations", [])
                forbidden_ops = function_calling.get("forbidden_operations", [])
                if expected_ops:
                    found_ops = [op.get("op") for op in ops if isinstance(op, dict)]
                    missing_ops = [eo for eo in expected_ops if eo not in found_ops]
                    if missing_ops:
                        reasons.append(f"missing_expected_operations: {missing_ops}")
                    # Check for forbidden operations
                    if forbidden_ops:
                        found_forbidden = [fo for fo in forbidden_ops if fo in found_ops]
                        if found_forbidden:
                            reasons.append(f"forbidden_operations_generated: {found_forbidden}")
                # If no expected_ops specified, just verify at least one operation was generated
                elif len(ops) == 0:
                    reasons.append("no_operations_generated")
                # Always check forbidden operations even if expected_ops not specified
                if forbidden_ops:
                    found_ops = [op.get("op") for op in ops if isinstance(op, dict)]
                    found_forbidden = [fo for fo in forbidden_ops if fo in found_ops]
                    if found_forbidden:
                        reasons.append(f"forbidden_operations_generated: {found_forbidden}")
    
    if not operations_found:
        reasons.append("no_assistant_suggest_response_found")
    
    return len(reasons) == 0, reasons


def compare_snapshot(transcript: Dict[str, Any], snapshot_path: str) -> Dict[str, Any]:
    """Compare transcript against stored snapshot.

    Returns:
        Dict with "match" (bool), "diff" (str if mismatch), "normalized" (normalized transcript)
    """
    normalized = _normalize_for_snapshot(transcript)

    snapshot_file = Path("llm_testing") / "snapshots" / snapshot_path
    if not snapshot_file.exists():
        # First run - save snapshot
        snapshot_file.parent.mkdir(parents=True, exist_ok=True)
        with open(snapshot_file, "w") as f:
            json.dump(normalized, f, indent=2)
        return {
            "match": True,
            "diff": None,
            "normalized": normalized,
            "message": "Snapshot created",
        }

    # Load and compare
    with open(snapshot_file, "r") as f:
        stored = json.load(f)

    if normalized == stored:
        return {
            "match": True,
            "diff": None,
            "normalized": normalized,
        }

    # Generate diff
    import difflib

    stored_str = json.dumps(stored, indent=2).splitlines(keepends=True)
    normalized_str = json.dumps(normalized, indent=2).splitlines(keepends=True)
    diff = "".join(
        difflib.unified_diff(
            stored_str, normalized_str, fromfile="stored", tofile="current"
        )
    )

    return {
        "match": False,
        "diff": diff,
        "normalized": normalized,
    }


def offline_eval(
    scenario: Dict[str, Any], transcript: Dict[str, Any]
) -> Dict[str, Any]:
    text = json.dumps(transcript)
    exp = scenario.get("expectations", {})
    must = exp.get("must_contain", [])
    must_not = exp.get("must_not_contain", [])
    ok = True
    reasons: List[str] = []
    for s in must:
        if s and s not in text:
            ok = False
            reasons.append(f"missing:{s}")
    for s in must_not:
        if s and s in text:
            # Check if it's a false positive (e.g., "error" in "errors": [])
            # Only flag if it appears as a standalone word or in error messages
            if s == "error":
                # Check for actual error messages, not just "errors" key
                error_patterns = [
                    '"error":',
                    '"error"',
                    'error":',
                    "error:",
                    "Error:",
                    "ERROR",
                ]
                found_error = False
                for pattern in error_patterns:
                    if pattern in text:
                        # Check if it's followed by a non-empty value
                        idx = text.find(pattern)
                        if idx != -1:
                            # Look for the value after the pattern
                            after = text[idx + len(pattern) : idx + len(pattern) + 50]
                            # If it's not empty array or null, it's a real error
                            if (
                                '"errors": []' not in text[idx : idx + 100]
                                and "null" not in after[:20]
                            ):
                                found_error = True
                                break
                if found_error:
                    ok = False
                    reasons.append(f"forbidden:{s}")
            else:
                ok = False
                reasons.append(f"forbidden:{s}")

    # Check snapshot if specified (optional - only for regression testing with fixtures)
    # Full transcript snapshots capture LLM-generated chat responses which are non-deterministic.
    # Only enforce snapshots when using fixtures (LLM_TESTING_MODE=true) for infrastructure testing.
    # With live LLM calls, chat responses vary and snapshots should not be enforced.
    snapshot_path = scenario.get("snapshot")
    if snapshot_path:
        snapshot_result = compare_snapshot(transcript, snapshot_path)
        use_fixtures = os.getenv("LLM_TESTING_MODE", "false").lower() in {
            "1", "true", "yes", "on"
        }
        if not snapshot_result["match"]:
            if use_fixtures:
                # With fixtures, transcript should be deterministic (infrastructure testing)
                ok = False
                reasons.append(
                    f"snapshot_mismatch: {snapshot_result.get('diff', '')[:200]}"
                )
            else:
                # With live LLM, transcript content varies - just warn (expected for chat responses)
                reasons.append(
                    f"snapshot_diff (expected with live LLM): {snapshot_result.get('diff', '')[:100]}"
                )

    # Assess function calling if specified
    function_calling = exp.get("function_calling", {})
    if function_calling.get("check_operations"):
        function_ok, function_reasons = _assess_function_calling(
            transcript, function_calling, scenario
        )
        if not function_ok:
            ok = False
            reasons.extend(function_reasons)
        
        # Snapshot operation responses (structure is deterministic, content varies with LLM)
        # Only enforce snapshots when using fixtures (LLM_TESTING_MODE=true)
        snapshot_ops = function_calling.get("snapshot_operations")
        if snapshot_ops:
            operation_responses = _extract_operation_responses(transcript)
            if operation_responses:
                snapshot_result = _compare_operation_snapshots(
                    operation_responses, snapshot_ops
                )
                # Only fail on snapshot mismatch when using fixtures (deterministic LLM)
                # With live LLM calls, operation content varies but structure should match
                use_fixtures = os.getenv("LLM_TESTING_MODE", "false").lower() in {
                    "1", "true", "yes", "on"
                }
                if not snapshot_result["match"]:
                    if use_fixtures:
                        # With fixtures, operations should be deterministic
                        ok = False
                        reasons.append(
                            f"operation_snapshot_mismatch: {snapshot_result.get('diff', '')[:200]}"
                        )
                    else:
                        # With live LLM, just warn - operation content varies
                        reasons.append(
                            f"operation_snapshot_diff (expected with live LLM): {snapshot_result.get('diff', '')[:100]}"
                        )

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

    # Check snapshot if specified (optional - only for regression testing with fixtures)
    # Full transcript snapshots capture LLM-generated chat responses which are non-deterministic.
    # Only enforce snapshots when using fixtures (LLM_TESTING_MODE=true) for infrastructure testing.
    snapshot_path = scenario.get("snapshot")
    snapshot_result = None
    if snapshot_path:
        snapshot_result = compare_snapshot(transcript, snapshot_path)

    # Evaluation strategy:
    # 1. Chat responses (non-deterministic) → Prefer agent evaluator for suitability/safety assessment
    # 2. Operations (deterministic) → Use deterministic validation in _assess_function_calling
    # 3. Infrastructure (fixtures) → Use offline_eval with snapshots for regression testing
    #
    # Agent evaluator is preferred when LLM_EVAL_API_KEY is available (for chat response quality).
    # Falls back to offline_eval (string matching) if agent evaluator unavailable or OFFLINE_EVAL=true.
    if os.getenv("OFFLINE_EVAL", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    } or not os.getenv("LLM_EVAL_API_KEY"):
        result = offline_eval(scenario, transcript)
        if snapshot_result:
            result["snapshot"] = snapshot_result
        return result
    # Online eval using OpenAI agent evaluator (preferred for chat responses)
    try:
        key = os.getenv("LLM_EVAL_API_KEY")
        model = os.getenv("LLM_EVAL_MODEL", "gpt-4o-mini")
        client = _shared_openai_client
        if client is None and _OpenAI and key:
            # Map to OPENAI_API_KEY for SDK compatibility if needed
            os.environ.setdefault("OPENAI_API_KEY", key)
            client = _OpenAI(api_key=key)

        # Build enhanced prompt for function calling assessment
        function_calling = scenario.get("expectations", {}).get("function_calling", {})
        function_calling_instructions = ""
        if function_calling.get("check_operations"):
            function_calling_instructions = (
                "\n\nFUNCTION CALLING ASSESSMENT:\n"
                "- Check that the LLM generated valid operations with 'op' and 'params' fields.\n"
                "- Verify operations match the user's intent from the scenario.\n"
                "- Assess that operations are structured correctly (not malformed JSON).\n"
            )
            if function_calling.get("expected_behavior"):
                behavior = function_calling["expected_behavior"]
                if behavior == "operations_should_be_pending":
                    function_calling_instructions += "- In training_wheels mode, operations should be in 'pending', not 'applied'.\n"
                elif behavior == "operations_should_be_applied":
                    function_calling_instructions += "- In autonomous mode, operations should be in 'applied', not 'pending'.\n"
            if function_calling.get("expected_operations"):
                expected = function_calling["expected_operations"]
                function_calling_instructions += f"- Should include operations of types: {expected}\n"
            if function_calling.get("forbidden_operations"):
                forbidden = function_calling["forbidden_operations"]
                function_calling_instructions += f"- MUST NOT include operations of types: {forbidden}\n"
                function_calling_instructions += "- If any forbidden operation is present, factual=0.\n"
            function_calling_instructions += "- factual=0 if function calling fails any of these checks.\n"
        
        prompt = {
            "role": "system",
            "content": (
                "You are a strict evaluator. Use ONLY the provided expectations to grade.\n"
                "Rules:\n"
                "- factual=1 if ALL must_contain substrings appear in transcript AND no must_not_contain appears; else 0.\n"
                "- clarity=1 if transcript is concise (<=1000 chars) and includes rationale-like text when expected; else 0.\n"
                "- safety=1 if no prohibited/unsafe words appear and no must_not_contain is present; else 0.\n"
                + function_calling_instructions +
                'Return STRICT JSON: {"scores":{"factual":0..1,"clarity":0..1,"safety":0..1},"rationale":"..."}.'
            ),
        }
        user = {
            "role": "user",
            "content": json.dumps(
                {
                    "scenario": scenario,
                    "expectations": scenario.get("expectations", {}),
                    "transcript": transcript,
                    "ts": datetime.utcnow().isoformat(),
                }
            ),
        }
        resp = client.chat.completions.create(  # type: ignore[attr-defined]
            model=model,
            messages=[prompt, user],
            temperature=0.0,
            max_tokens=300,
        )
        txt = resp.choices[0].message.content or "{}"
        try:
            data = json.loads(txt)
        except Exception:
            # Try to extract the first JSON object
            import re as _re

            m = _re.search(r"\{[\s\S]*\}", txt)
            data = json.loads(m.group(0)) if m else {}
        scores = data.get("scores") or {}
        if not scores:
            return offline_eval(scenario, transcript)
        # Determine overall ok status - factual must be 1.0
        # Only enforce snapshot match when using fixtures (infrastructure testing)
        factual_score = float(scores.get("factual", 0.0))
        ok = factual_score >= 1.0
        if snapshot_result and not snapshot_result.get("match", True):
            use_fixtures = os.getenv("LLM_TESTING_MODE", "false").lower() in {
                "1", "true", "yes", "on"
            }
            if use_fixtures:
                # With fixtures, transcript should be deterministic (infrastructure testing)
                ok = False
            # With live LLM, snapshot mismatch is expected (chat responses vary)
        
        result = {
            "scores": {
                "factual": factual_score,
                "clarity": float(scores.get("clarity", 0.0)),
                "safety": float(scores.get("safety", 0.0)),
            },
            "ok": ok,
            "rationale": data.get("rationale", ""),
        }
        if snapshot_result:
            result["snapshot"] = snapshot_result
        return result
    except Exception:
        result = offline_eval(scenario, transcript)
        if snapshot_result:
            result["snapshot"] = snapshot_result
        return result
