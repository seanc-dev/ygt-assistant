import pytest
from core.chat.tokens import parse_message_with_tokens
from core.chat.validation import (
    validate_parsed_message,
    ValidationErrorCode,
    ValidationOk,
)


USER_CONTEXT = {"userId": "user-1", "tenantId": "tenant-1", "threadContext": {}}


def test_validate_parsed_message_success(monkeypatch):
    parsed = parse_message_with_tokens(
        'Link this [ref v:1 type:"task" id:task-1 name:"Sample"] please.'
    )

    def fake_lookup(ref_type, identifier, user_id):
        return {"id": identifier, "type": ref_type}

    monkeypatch.setattr(
        "core.chat.validation._lookup_reference_record", fake_lookup
    )

    result = validate_parsed_message(parsed, user_context=USER_CONTEXT)
    assert isinstance(result, ValidationOk)
    assert len(result.resolved_references) == 1


def test_validate_parsed_message_ref_not_found(monkeypatch):
    parsed = parse_message_with_tokens(
        'Here is [ref v:1 type:"task" id:missing name:"Missing"]'
    )

    def fake_lookup(ref_type, identifier, user_id):
        raise ValueError("not found")

    monkeypatch.setattr(
        "core.chat.validation._lookup_reference_record", fake_lookup
    )

    result = validate_parsed_message(parsed, user_context=USER_CONTEXT)
    assert not result.ok
    assert getattr(result, "error_code", None) == ValidationErrorCode.REF_NOT_FOUND


def test_validate_parsed_message_invalid_op_args(monkeypatch):
    parsed = parse_message_with_tokens(
        '[op v:1 type:"update_task_status" task:"missing" status:"doing"]'
    )

    def fake_lookup(ref_type, identifier, user_id):
        raise ValueError("not found")

    monkeypatch.setattr(
        "core.chat.validation._lookup_reference_record", fake_lookup
    )

    result = validate_parsed_message(parsed, user_context=USER_CONTEXT)
    assert not result.ok
    assert getattr(result, "error_code", None) == ValidationErrorCode.OP_INVALID_ARGS
