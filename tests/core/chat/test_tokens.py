"""Tests for structured token parsing."""
from core.chat.tokens import parse_message_with_tokens
import pytest


def test_parse_single_reference_token():
    text = 'Please update [ref v:1 type:"task" id:123 name:"Review brief"] today.'
    parsed = parse_message_with_tokens(text)

    assert parsed.llm_text == 'Please update <<REF_1>> today.'
    assert len(parsed.references) == 1
    ref = parsed.references[0]
    assert ref.id == "123"
    assert ref.type == "task"
    assert ref.meta["name"] == "Review brief"
    assert parsed.operations == []


def test_parse_single_operation_token():
    text = 'Run [op v:1 type:"update_task_status" task:123 status:"doing"].'
    parsed = parse_message_with_tokens(text)

    assert parsed.llm_text == 'Run <<OP_1>>.'
    assert len(parsed.operations) == 1
    op = parsed.operations[0]
    assert op.type == "update_task_status"
    assert op.args["task"] == "123"
    assert op.args["status"] == "doing"
    assert parsed.references == []


def test_parse_multiple_mixed_tokens():
    text = (
        'Link [ref v:1 type:"task" id:task-1 name:"Launch"] with '
        '[op v:1 type:"link_action_to_task" action:"a-1" task:"task-1"].'
    )
    parsed = parse_message_with_tokens(text)

    assert parsed.llm_text == 'Link <<REF_1>> with <<OP_1>>.'
    assert parsed.references[0].placeholder == "<<REF_1>>"
    assert parsed.operations[0].placeholder == "<<OP_1>>"


@pytest.mark.parametrize(
    "text",
    [
        "[ref type:\"task\" id:123] missing version",
        "[op v:1 status:doing] missing type",
        "[ref v:1 type:\"task\"] missing id",
    ],
)
def test_malformed_tokens_raise(text):
    with pytest.raises(ValueError):
        parse_message_with_tokens(text)
