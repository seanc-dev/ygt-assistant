from __future__ import annotations
from typing import Any, Dict
import json
import os
import time
import uuid
from pathlib import Path
import yaml  # type: ignore


def _is_true(v: str | None) -> bool:
    return (v or "").strip().lower() in {"1", "true", "yes", "on"}


def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def run_scenario(scn_path: str) -> Dict[str, Any]:
    os.environ["USE_MOCK_GRAPH"] = "true"
    os.environ.setdefault("DEV_MODE", "true")
    scn = load_yaml(scn_path)
    # Import after env is prepared so FastAPI app can initialize in dev mode
    from llm_testing.backends.inprocess import InProcessBackend  # type: ignore

    backend = InProcessBackend()

    run_id = uuid.uuid4().hex[:8]
    name = scn.get("name") or Path(scn_path).stem
    reports_dir = Path("llm_testing") / "reports" / run_id
    reports_dir.mkdir(parents=True, exist_ok=True)
    transcript: Dict[str, Any] = {"scenario": name, "steps": []}

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
        transcript["steps"].append({"endpoint": "/calendar/plan-today", "response": p})
    elif name == "token_expired_reconnect":
        # Simulate via expectations in evaluator fallback; mocks won't 401
        resp = backend.actions_scan(["email"])
        transcript["steps"].append({"endpoint": "/actions/scan", "response": resp})
    elif name == "live_inbox":
        # Enable live flags for inbox; with mocks this returns not_supported
        os.environ["FEATURE_GRAPH_LIVE"] = "true"
        os.environ["FEATURE_LIVE_LIST_INBOX"] = "true"
        import httpx

        r = httpx.get(
            f"http://testserver/actions/live/inbox", params={"user_id": "default", "limit": 5}
        )
        transcript["steps"].append({"endpoint": "/actions/live/inbox", "response": r.json()})
    elif name == "live_send":
        os.environ["FEATURE_GRAPH_LIVE"] = "true"
        os.environ["FEATURE_LIVE_SEND_MAIL"] = "true"
        import httpx

        r = httpx.post(
            f"http://testserver/actions/live/send",
            params={"user_id": "default"},
            json={"to": ["user@example.com"], "subject": "[YGT Test]", "body": "Hi"},
        )
        transcript["steps"].append({"endpoint": "/actions/live/send", "response": r.json()})
    elif name == "live_create_events":
        os.environ["FEATURE_GRAPH_LIVE"] = "true"
        os.environ["FEATURE_LIVE_CREATE_EVENTS"] = "true"
        import httpx

        ev = {"title": "Block", "start": "2025-10-25T09:00:00Z", "end": "2025-10-25T09:30:00Z"}
        r = httpx.post(
            f"http://testserver/actions/live/create-events",
            params={"user_id": "default"},
            json={"events": [ev]},
        )
        transcript["steps"].append({"endpoint": "/actions/live/create-events", "response": r.json()})
    else:
        # default: just run scan
        resp = backend.actions_scan([])
        transcript["steps"].append({"endpoint": "/actions/scan", "response": resp})

    out_path = reports_dir / f"{name}.json"
    with open(out_path, "w") as f:
        json.dump(
            {"scenario": scn, "transcript": transcript, "ts": time.time()}, f, indent=2
        )
    return {"run_id": run_id, "report": str(out_path)}
