"""Tests for audit logging."""
import pytest
from presentation.api.repos import audit_log


def test_audit_write_with_request_id():
    """Test audit write includes request_id."""
    request_id = "test_req_123"
    entry_id = audit_log.write_audit(
        "test_action",
        {"test": "data"},
        request_id=request_id,
    )
    
    log = audit_log.get_audit_log(limit=1)
    assert len(log) >= 1
    latest = log[0]
    assert latest["request_id"] == request_id
    assert latest["action"] == "test_action"
    assert latest["details"]["test"] == "data"


def test_audit_write_generates_request_id():
    """Test audit write generates request_id if not provided."""
    entry_id = audit_log.write_audit(
        "test_action",
        {"test": "data"},
        request_id=None,
    )
    
    log = audit_log.get_audit_log(limit=1)
    assert len(log) >= 1
    latest = log[0]
    assert latest["request_id"] is not None
    assert latest["request_id"] != ""


def test_audit_log_structure():
    """Test audit log entries have correct structure."""
    audit_log.write_audit(
        "test_action",
        {"field": "value"},
        request_id="req_123",
    )
    
    log = audit_log.get_audit_log(limit=1)
    assert len(log) >= 1
    entry = log[0]
    
    assert "id" in entry
    assert "timestamp" in entry
    assert "request_id" in entry
    assert "action" in entry
    assert "details" in entry

