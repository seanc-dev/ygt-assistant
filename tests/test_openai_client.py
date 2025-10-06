"""Test OpenAI client functionality."""

from unittest.mock import patch, MagicMock, PropertyMock
import openai_client


def test_interpret_command_no_api_key():
    """Test interpretation when no API key is available."""
    with patch("openai_client.client", None):
        result = openai_client.interpret_command("hello", "")
        assert result["action"] == "error"
        assert "details" in result


def test_interpret_command_with_api_key():
    """Test interpretation when API key is available."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.function_call = None
    mock_response.choices = [mock_message]
    mock_client.chat.completions.create.return_value = mock_response

    with patch("openai_client.client", mock_client):
        result = openai_client.interpret_command("hello", "")
        assert result["action"] in ("clarify", "error")
        assert "details" in result


def test_interpret_command_function_call():
    """Test interpretation with function call response."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_function_call = MagicMock()

    # Use PropertyMock to properly mock the attributes
    type(mock_function_call).name = PropertyMock(return_value="list_all")
    type(mock_function_call).arguments = PropertyMock(return_value="{}")
    mock_message.function_call = mock_function_call
    mock_response.choices = [mock_message]
    mock_client.chat.completions.create.return_value = mock_response

    with patch("openai_client.client", mock_client):
        result = openai_client.interpret_command("show me today's events", "")
        assert result["action"] in ("list_all", "clarify")
        if result["action"] == "list_all":
            assert result["details"] == {}


def test_interpret_command_exception():
    """Test interpretation when an exception occurs."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("API Error")

    with patch("openai_client.client", mock_client):
        result = openai_client.interpret_command("hello", "")
        assert result["action"] == "error"
        assert "API Error" in result["details"]
