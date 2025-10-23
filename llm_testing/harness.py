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
