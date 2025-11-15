"""Tests for JSON-only fallback parsing in LLM operations."""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.llm import _extract_json_from_text


def test_extract_clean_json():
    """Test extraction of clean JSON."""
    text = '{"operations": [{"op": "chat", "params": {"message": "Hello"}}]}'
    result = _extract_json_from_text(text)
    assert result is not None
    assert result["operations"][0]["op"] == "chat"


def test_extract_json_with_code_fences():
    """Test extraction of JSON wrapped in code fences."""
    text = """```json
{"operations": [{"op": "chat", "params": {"message": "Hello"}}]}
```"""
    result = _extract_json_from_text(text)
    assert result is not None
    assert result["operations"][0]["op"] == "chat"


def test_extract_json_with_stray_text():
    """Test extraction of JSON with stray text around it."""
    text = """Here's the response:
{"operations": [{"op": "chat", "params": {"message": "Hello"}}]}
That's all."""
    result = _extract_json_from_text(text)
    assert result is not None
    assert result["operations"][0]["op"] == "chat"


def test_extract_json_irrecoverable():
    """Test that irrecoverable JSON returns None."""
    text = "This is not JSON at all"
    result = _extract_json_from_text(text)
    assert result is None


def test_extract_json_malformed():
    """Test that malformed JSON returns None."""
    text = '{"operations": [{"op": "chat"}'  # Missing closing braces
    result = _extract_json_from_text(text)
    assert result is None
