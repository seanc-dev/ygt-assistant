from __future__ import annotations
from typing import Any, Dict, List, Optional
import json
import os
import time
import uuid
from pathlib import Path
import yaml  # type: ignore
import re


def _is_true(v: str | None) -> bool:
    return (v or "").strip().lower() in {"1", "true", "yes", "on"}


def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def _assert_status(response: Any, expected: int) -> None:
    """Assert HTTP response status code."""
    status = getattr(response, "status_code", None)
    if status != expected:
        raise AssertionError(f"Expected status {expected}, got {status}")


def _assert_contains(payload: Any, patterns: List[str]) -> None:
    """Assert that payload (as JSON string) contains all patterns."""
    text = json.dumps(payload) if not isinstance(payload, str) else payload
    missing = [p for p in patterns if p not in text]
    if missing:
        raise AssertionError(f"Missing patterns: {missing}")


def _assert_jsonpath(payload: Any, path: str, expected: Any) -> None:
    """Assert JSONPath expression matches expected value.

    Supports:
    - Simple paths: "pending.0.op"
    - Array filtering: "pending[?(@.op == 'create_task')].op" - finds first matching item's field
    """
    # Handle array filtering syntax: "pending[?(@.op == 'create_task')].op"
    if "[?(@" in path:
        # Extract array path, filter condition, and optional field access
        array_path, rest = path.split("[?", 1)
        filter_expr, field_path = rest.split("]", 1) if "]" in rest else (rest, "")
        if field_path.startswith("."):
            field_path = field_path[1:]  # Remove leading dot

        # Parse filter like "@.op == 'create_task'"
        if ".op ==" in filter_expr:
            op_value = (
                filter_expr.split("'")[1]
                if "'" in filter_expr
                else filter_expr.split('"')[1]
            )
            field = filter_expr.split("@.")[1].split("==")[0].strip()

            # Navigate to array
            parts = array_path.split(".")
            current = payload
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                elif isinstance(current, list):
                    try:
                        idx = int(part)
                        current = current[idx] if idx < len(current) else None
                    except ValueError:
                        current = None
                else:
                    current = None
                if current is None:
                    raise ValueError(f"Path not found: {array_path}")

            # Find matching item in array
            if not isinstance(current, list):
                raise ValueError(f"Path {array_path} is not an array")

            matching = next(
                (
                    item
                    for item in current
                    if isinstance(item, dict) and item.get(field) == op_value
                ),
                None,
            )
            if matching is None:
                raise ValueError(
                    f"No item found matching {filter_expr} in {array_path}"
                )

            # Access field if specified
            if field_path:
                parts = field_path.split(".")
                current = matching
                for part in parts:
                    if isinstance(current, dict):
                        current = current.get(part)
                    else:
                        raise ValueError(f"Path not found: {path}")
                if current != expected:
                    raise AssertionError(
                        f"JSONPath {path}: expected {expected}, got {current}"
                    )
            else:
                # Just checking that matching item exists
                if expected and not matching:
                    raise AssertionError(
                        f"JSONPath {path}: expected matching item, got None"
                    )
        else:
            raise ValueError(f"Unsupported filter expression: {filter_expr}")
        return

    # Standard JSONPath extraction
    parts = path.split(".")
    current = payload
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                idx = int(part)
                current = current[idx] if idx < len(current) else None
            except ValueError:
                raise ValueError(f"Invalid JSONPath: {path}")
        else:
            raise ValueError(f"Path not found: {path}")
    if current != expected:
        raise AssertionError(f"JSONPath {path}: expected {expected}, got {current}")


def _apply_env_vars(env: Dict[str, Any]) -> None:
    """Apply environment variables from scenario."""
    for key, value in env.items():
        os.environ[key] = str(value)


def run_scenario(scn_path: str) -> Dict[str, Any]:
    os.environ["USE_MOCK_GRAPH"] = "true"
    os.environ.setdefault("DEV_MODE", "true")
    scn = load_yaml(scn_path)
    run_id = uuid.uuid4().hex[:8]
    name = scn.get("name") or Path(scn_path).stem

    # Apply scenario-specific env vars first (so they can override defaults)
    if "env" in scn:
        _apply_env_vars(scn["env"])

    # Enable LLM_TESTING_MODE by default, but allow scenarios to opt-out
    # Priority: env var > scenario use_llm_fixtures > default (true)
    # Set LLM_TESTING_MODE=false in env or use_llm_fixtures: false to test actual LLM behavior
    if os.getenv("LLM_TESTING_MODE") is not None:
        # Environment variable takes precedence (e.g., from Makefile or CI)
        pass  # Already set, don't override
    elif "use_llm_fixtures" in scn:
        # Explicit scenario-level control
        if scn["use_llm_fixtures"] is False:
            os.environ["LLM_TESTING_MODE"] = "false"
        else:
            os.environ.setdefault("LLM_TESTING_MODE", "true")
    else:
        # Default to fixtures if not explicitly set
        os.environ.setdefault("LLM_TESTING_MODE", "true")

    # For live_* scenarios, set flags before creating the backend so routes see them at import time
    if name in {"live_inbox", "live_send", "live_create_events"}:
        os.environ["FEATURE_GRAPH_LIVE"] = "true"
        # Per-action flags toggled below per scenario

    # Import after env is prepared so FastAPI app can initialize in dev mode
    from llm_testing.backends.inprocess import InProcessBackend  # type: ignore
    from llm_testing.mock_db import get_mock_client, reset_mock_db

    backend = InProcessBackend()

    # Always use mock database for tests (independent of LLM_TESTING_MODE)
    # LLM_TESTING_MODE controls whether we use LLM fixtures or live calls
    # Mock DB ensures we don't hit real Supabase during testing
    reset_mock_db()
    mock_db = get_mock_client()

    # Seed database if scenario needs it
    if "seed_workroom" in str(scn.get("steps", [])):
        # Will be seeded via /dev/workroom/seed endpoint
        pass
    if "seed_queue" in str(scn.get("steps", [])):
        # Will be seeded via /dev/queue/seed endpoint
        pass

    reports_dir = Path("llm_testing") / "reports" / run_id
    reports_dir.mkdir(parents=True, exist_ok=True)
    transcript: Dict[str, Any] = {"scenario": name, "steps": []}

    # If scenario defines explicit steps, execute them generically
    if scn.get("steps"):
        expectations: Dict[str, Any] = scn.get("expectations") or {}
        text_chunks: list[str] = []
        variables: Dict[str, Any] = {}  # Store extracted variables for substitution
        raw_variables: Dict[str, Any] = {}

        def _extract_variables(payload: Any, extract: Dict[str, str]) -> None:
            """Extract variables from response using JSONPath.

            Supports:
            - Simple paths: "pending.0.op"
            - Array filtering: "pending[?(@.op == 'create_task')]" - finds first matching item
            """
            for var_name, jsonpath in extract.items():
                # Handle array filtering syntax: "pending[?(@.op == 'create_task')]"
                if "[?(@" in jsonpath:
                    # Extract array path and filter condition
                    array_path, filter_expr = jsonpath.split("[?", 1)
                    filter_expr = filter_expr.rstrip("]")

                    # Parse filter like "@.op == 'create_task'"
                    if ".op ==" in filter_expr:
                        op_value = (
                            filter_expr.split("'")[1]
                            if "'" in filter_expr
                            else filter_expr.split('"')[1]
                        )
                        field = filter_expr.split("@.")[1].split("==")[0].strip()

                        # Navigate to array
                        parts = array_path.split(".")
                        current = payload
                        for part in parts:
                            if isinstance(current, dict):
                                current = current.get(part)
                            elif isinstance(current, list):
                                try:
                                    idx = int(part)
                                    current = (
                                        current[idx] if idx < len(current) else None
                                    )
                                except ValueError:
                                    current = None
                            else:
                                current = None
                            if current is None:
                                break

                        # Find matching item in array
                        if isinstance(current, list):
                            matching = next(
                                (
                                    item
                                    for item in current
                                    if isinstance(item, dict)
                                    and item.get(field) == op_value
                                ),
                                None,
                            )
                            if matching is not None:
                                variables[var_name] = json.dumps(matching)
                                raw_variables[var_name] = matching
                    continue

                # Standard JSONPath extraction
                parts = jsonpath.split(".")
                current = payload
                for part in parts:
                    if isinstance(current, dict):
                        current = current.get(part)
                    elif isinstance(current, list):
                        try:
                            idx = int(part)
                            current = current[idx] if idx < len(current) else None
                        except ValueError:
                            current = None
                    else:
                        current = None
                    if current is None:
                        break
                if current is not None:
                    variables[var_name] = str(current)
                    raw_variables[var_name] = current

        def _substitute_vars(text: str) -> str:
            """Substitute variables in text."""
            for var_name, var_value in variables.items():
                text = text.replace(f"<{var_name}>", var_value)
            return text

        def _resolve_body_vars(obj: Any) -> Any:
            if isinstance(obj, dict):
                if "__var__" in obj and len(obj) == 1:
                    var_name = obj["__var__"]
                    return raw_variables.get(var_name)
                return {k: _resolve_body_vars(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_resolve_body_vars(item) for item in obj]
            return obj

        def _substitute_expectations(expect: Dict[str, Any]) -> Dict[str, Any]:
            """Substitute variables inside expectation directives."""
            substituted = dict(expect)
            if "contains" in substituted:
                substituted["contains"] = [
                    _substitute_vars(item) if isinstance(item, str) else item
                    for item in substituted["contains"]
                ]
            if "must_contain" in substituted:
                substituted["must_contain"] = [
                    _substitute_vars(item) if isinstance(item, str) else item
                    for item in substituted["must_contain"]
                ]
            if "must_not_contain" in substituted:
                substituted["must_not_contain"] = [
                    _substitute_vars(item) if isinstance(item, str) else item
                    for item in substituted["must_not_contain"]
                ]
            if "jsonpath" in substituted:
                substituted["jsonpath"] = {
                    path: (_substitute_vars(val) if isinstance(val, str) else val)
                    for path, val in substituted["jsonpath"].items()
                }
            return substituted

        for step in scn.get("steps", []):
            act = (step or {}).get("action")
            if act == "reset_state":
                # Reset in-memory state
                r = backend.client.post("/dev/state/reset")
                try:
                    payload = r.json()
                except Exception:
                    payload = {"text": r.text}
                transcript["steps"].append(
                    {"action": "reset_state", "response": payload}
                )
                text_chunks.append(str(payload))
            elif act == "http":
                method = (step.get("method") or "GET").upper()
                url = step.get("url") or "/"
                # Substitute variables in URL
                url = _substitute_vars(url)

                params = step.get("params") or {}
                # Substitute variables in params
                params = {
                    k: _substitute_vars(str(v)) if isinstance(v, str) else v
                    for k, v in params.items()
                }

                body = step["json"] if "json" in step else step.get("body")
                # Substitute variables in body (recursively)
                if body:
                    body_str = json.dumps(body)
                    body_str = _substitute_vars(body_str)
                    body = json.loads(body_str)
                    body = _resolve_body_vars(body)

                if method == "GET":
                    r = backend.client.get(url, params=params)
                elif method == "POST":
                    r = backend.client.post(url, params=params, json=body)
                elif method == "PUT":
                    r = backend.client.put(url, params=params, json=body)
                elif method == "DELETE":
                    r = backend.client.delete(url, params=params)
                else:
                    r = backend.client.request(method, url, params=params, json=body)
                try:
                    payload = r.json()
                except Exception:
                    payload = {"text": r.text}

                # Extract variables if specified
                if "extract" in step:
                    _extract_variables(payload, step["extract"])

                # Step-level assertions
                expect = _substitute_expectations(step.get("expect", {}))
                if "status" in expect:
                    _assert_status(r, expect["status"])
                if "contains" in expect:
                    _assert_contains(payload, expect["contains"])
                if "jsonpath" in expect:
                    for path, expected in expect["jsonpath"].items():
                        if (
                            expected == "<task_id>"
                            or expected == "<action_id>"
                            or expected == "<operations>"
                        ):
                            # Just verify path exists, don't assert value
                            parts = path.split(".")
                            current = payload
                            for part in parts:
                                if isinstance(current, dict):
                                    current = current.get(part)
                                elif isinstance(current, list):
                                    try:
                                        idx = int(part)
                                        current = (
                                            current[idx] if idx < len(current) else None
                                        )
                                    except ValueError:
                                        current = None
                                else:
                                    current = None
                                if current is None:
                                    break
                            if current is None:
                                raise AssertionError(f"JSONPath {path} not found")
                        else:
                            _assert_jsonpath(payload, path, expected)

                step_data = {
                    "endpoint": url,
                    "method": method,
                    "response": payload,
                    "status": getattr(r, "status_code", None),
                }
                # Include request body for deterministic parameter validation
                if body:
                    step_data["request_body"] = body
                transcript["steps"].append(step_data)
                text_chunks.append(str(payload))
            elif act == "grade":
                rubric = step.get("rubric") or {}
                must = rubric.get("must_include") or []
                dis = rubric.get("disallow") or []
                # map to evaluator expectations for offline/online scoring
                exp = expectations or {}
                exp.setdefault("must_contain", [])
                exp.setdefault("must_not_contain", [])
                exp["must_contain"].extend(must)
                exp["must_not_contain"].extend(dis)
                expectations = exp
        # attach synthesized expectations
        if expectations:
            scn["expectations"] = expectations
        # minimal concatenated text for simple grep evaluators
        transcript["text"] = "\n".join(text_chunks)
    else:
        # Apply fixtures is implicit via mock providers reading from llm_testing/fixtures
        # Execute primary action per scenario by name
        if name == "plan_today":
            resp = backend.calendar_plan_today()
            transcript["steps"].append(
                {"endpoint": "/calendar/plan-today", "response": resp}
            )
        elif name == "approve_send":
            d = backend.email_create_draft(["user@example.com"], "Hello", "Body")
            transcript["steps"].append({"endpoint": "/email/drafts", "response": d})
            s = backend.email_send(d.get("id"))
            transcript["steps"].append({"endpoint": "/email/send/{id}", "response": s})
        elif name == "triage_inbox":
            resp = backend.actions_scan(["email"])
            transcript["steps"].append({"endpoint": "/actions/scan", "response": resp})
        elif name == "undo_event":
            # Minimal: create then undo by approvals flow placeholder
            p = backend.calendar_plan_today()
            transcript["steps"].append(
                {"endpoint": "/calendar/plan-today", "response": p}
            )
        elif name == "token_expired_reconnect":
            # Simulate via expectations in evaluator fallback; mocks won't 401
            resp = backend.actions_scan(["email"])
            transcript["steps"].append({"endpoint": "/actions/scan", "response": resp})
        elif name == "live_inbox":
            os.environ["FEATURE_LIVE_LIST_INBOX"] = "true"
            r = backend.client.get(
                "/actions/live/inbox", params={"user_id": "default", "limit": 5}
            )
            transcript["steps"].append(
                {"endpoint": "/actions/live/inbox", "response": r.json()}
            )
        elif name == "live_send":
            os.environ["FEATURE_LIVE_SEND_MAIL"] = "true"
            r = backend.client.post(
                "/actions/live/send",
                params={"user_id": "default"},
                json={
                    "to": ["user@example.com"],
                    "subject": "[YGT Test]",
                    "body": "Hi",
                },
            )
            transcript["steps"].append(
                {"endpoint": "/actions/live/send", "response": r.json()}
            )
        elif name == "live_create_events":
            os.environ["FEATURE_LIVE_CREATE_EVENTS"] = "true"
            ev = {
                "title": "Block",
                "start": "2025-10-25T09:00:00Z",
                "end": "2025-10-25T09:30:00Z",
            }
            r = backend.client.post(
                "/actions/live/create-events",
                params={"user_id": "default"},
                json={"events": [ev]},
            )
            transcript["steps"].append(
                {"endpoint": "/actions/live/create-events", "response": r.json()}
            )
        else:
            # default: just run scan
            resp = backend.actions_scan([])
            transcript["steps"].append({"endpoint": "/actions/scan", "response": resp})
    # (legacy block removed; scenarios are executed only once)

    out_path = reports_dir / f"{name}.json"
    with open(out_path, "w") as f:
        json.dump(
            {"scenario": scn, "transcript": transcript, "ts": time.time()}, f, indent=2
        )
    return {"run_id": run_id, "report": str(out_path)}
