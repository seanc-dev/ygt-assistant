import pytest
import openai_client

pytestmark = pytest.mark.integration

# Test duration extraction in fallback logic


def test_nlp_duration_extraction_hours(monkeypatch):
    # Ensure fallback mapping is used
    monkeypatch.setattr(openai_client, "client", None)
    res = openai_client.interpret_command(
        "schedule team meeting for 2-hour tomorrow at 14:00"
    )
    assert res["action"] == "create_event"
    assert "duration" in res["details"]
    assert res["details"]["duration"] == 120  # type: ignore


def test_nlp_duration_extraction_minutes(monkeypatch):
    monkeypatch.setattr(openai_client, "client", None)
    res = openai_client.interpret_command(
        "schedule quick call for 45min today at 16:30"
    )
    assert res["action"] == "create_event"
    assert "duration" in res["details"]
    assert res["details"]["duration"] == 45  # type: ignore


def test_nlp_location_extraction(monkeypatch):
    monkeypatch.setattr(openai_client, "client", None)
    res = openai_client.interpret_command(
        "schedule coffee break tomorrow at 10:00 at the cafe"
    )
    assert res["action"] == "create_event"
    assert "location" in res["details"]
    assert res["details"]["location"] == "the cafe"  # type: ignore
