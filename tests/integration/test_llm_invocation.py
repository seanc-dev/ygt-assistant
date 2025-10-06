import pytest
import json
from types import SimpleNamespace
import openai_client

pytestmark = pytest.mark.integration


def test_llm_invocation_calls_client(monkeypatch):
    # Prepare fake function call response
    fake_fc = SimpleNamespace(name="list_events_only", arguments=json.dumps({}))
    fake_msg = SimpleNamespace(function_call=fake_fc)
    fake_choice = SimpleNamespace(message=fake_msg)
    fake_resp = SimpleNamespace(choices=[fake_choice])

    # Fake create method to capture parameters
    def fake_create(model, messages, functions, function_call, temperature, max_tokens):
        # Validate we are using GPT-4o
        assert model == "gpt-4o"
        # The first message should be our system context with date/time
        assert isinstance(messages, list) and len(messages) >= 1
        sys_msg = messages[0]
        assert sys_msg["role"] == "system"
        assert "Today is" in sys_msg["content"]
        # Return our fake response
        return fake_resp

    # Install dummy client
    dummy_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))
    )
    monkeypatch.setattr(openai_client, "client", dummy_client)

    # Call interpret_command (should hit LLM branch)
    result = openai_client.interpret_command("any command")
    assert result["action"] == "list_events_only"
    assert result.get("details") == {}
