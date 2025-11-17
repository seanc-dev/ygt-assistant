"""Tests for snapshot diff helper."""

import pytest
import json
import tempfile
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llm_testing.evaluator import _normalize_for_snapshot, compare_snapshot


def test_normalize_timestamps():
    """Test that timestamps are normalized."""
    obj = {
        "created_at": "2025-01-15T10:30:00Z",
        "updated_at": "2025-01-15T11:45:00.123Z",
        "message": "Hello",
    }
    normalized = _normalize_for_snapshot(obj)
    assert normalized["created_at"] == "<timestamp>"
    assert normalized["updated_at"] == "<timestamp>"
    assert normalized["message"] == "Hello"


def test_normalize_uuids():
    """Test that UUIDs are normalized."""
    obj = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "task_id": "abc123def456",
        "name": "Test",
    }
    normalized = _normalize_for_snapshot(obj)
    assert normalized["id"] == "<uuid>"
    assert normalized["task_id"] == "<uuid>"
    assert normalized["name"] == "Test"


def test_normalize_nested():
    """Test normalization of nested structures."""
    obj = {
        "user": {
            "id": "user-123",
            "created_at": "2025-01-15T10:00:00Z",
        },
        "items": [
            {"id": "item-1", "timestamp": "2025-01-15T11:00:00Z"},
            {"id": "item-2", "timestamp": "2025-01-15T12:00:00Z"},
        ],
    }
    normalized = _normalize_for_snapshot(obj)
    assert normalized["user"]["id"] == "<uuid>"
    assert normalized["user"]["created_at"] == "<timestamp>"
    assert normalized["items"][0]["id"] == "<uuid>"
    assert normalized["items"][0]["timestamp"] == "<timestamp>"


def test_compare_snapshot_first_run(tmp_path):
    """Test snapshot creation on first run."""
    # Change to temp directory
    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        Path("llm_testing/snapshots").mkdir(parents=True, exist_ok=True)
        
        transcript = {
            "scenario": "test",
            "steps": [
                {"endpoint": "/test", "response": {"id": "123", "created_at": "2025-01-15T10:00:00Z"}},
            ],
        }
        
        result = compare_snapshot(transcript, "test.json")
        assert result["match"] is True
        assert result["message"] == "Snapshot created"
        assert Path("llm_testing/snapshots/test.json").exists()
    finally:
        os.chdir(original_cwd)


def test_compare_snapshot_match(tmp_path):
    """Test snapshot comparison when they match."""
    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        Path("llm_testing/snapshots").mkdir(parents=True, exist_ok=True)
        
        # Create initial snapshot
        snapshot_file = Path("llm_testing/snapshots/test.json")
        normalized = {
            "scenario": "test",
            "steps": [{"endpoint": "/test", "response": {"id": "<uuid>", "created_at": "<timestamp>"}}],
        }
        with open(snapshot_file, "w") as f:
            json.dump(normalized, f)
        
        # Compare with matching transcript (different IDs/timestamps but normalized same)
        transcript = {
            "scenario": "test",
            "steps": [
                {"endpoint": "/test", "response": {"id": "different-id", "created_at": "2025-01-16T11:00:00Z"}},
            ],
        }
        
        result = compare_snapshot(transcript, "test.json")
        assert result["match"] is True
        assert result["diff"] is None
    finally:
        os.chdir(original_cwd)


def test_compare_snapshot_mismatch(tmp_path):
    """Test snapshot comparison when they don't match."""
    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        Path("llm_testing/snapshots").mkdir(parents=True, exist_ok=True)
        
        # Create initial snapshot
        snapshot_file = Path("llm_testing/snapshots/test.json")
        normalized = {
            "scenario": "test",
            "steps": [{"endpoint": "/test", "response": {"status": "ok"}}],
        }
        with open(snapshot_file, "w") as f:
            json.dump(normalized, f)
        
        # Compare with different transcript
        transcript = {
            "scenario": "test",
            "steps": [
                {"endpoint": "/test", "response": {"status": "error", "message": "Failed"}},
            ],
        }
        
        result = compare_snapshot(transcript, "test.json")
        assert result["match"] is False
        assert result["diff"] is not None
        assert "error" in result["diff"] or "Failed" in result["diff"]
    finally:
        os.chdir(original_cwd)

