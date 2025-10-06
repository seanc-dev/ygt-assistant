"""Unit tests for CLI rendering helpers (API-first JSON default)."""

import os
import json

os.environ["CLI_OUTPUT_MODE"] = "json"

from utils.cli_output import render


def test_cli_outputs_json_no_events():
    """JSON mode returns machine-readable payloads."""
    os.environ["CLI_OUTPUT_MODE"] = "json"
    payload = {"type": "find_events", "result": []}
    s = render(payload)
    assert json.loads(s) == payload


def test_cli_pretty_snapshot_no_events():
    """Pretty mode produces human text, not used for core assertions."""

    os.environ["CLI_OUTPUT_MODE"] = "pretty"
    from utils.cli_output import render as pretty_render

    s = pretty_render({"type": "find_events", "result": []})
    assert "No events" in s
