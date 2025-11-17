import logging

from core.services import llm_executor


def test_normalize_enum_value_accepts_valid_case_insensitive():
    value = llm_executor._normalize_enum_value(
        "HIGH",
        allowed=llm_executor.PRIORITY_VALUES,
        field="priority",
        op_type="create_task",
        default="medium",
    )
    assert value == "high"


def test_normalize_enum_value_coerces_invalid(caplog):
    caplog.set_level(logging.WARNING)
    value = llm_executor._normalize_enum_value(
        "urgent-ish",
        allowed=llm_executor.PRIORITY_VALUES,
        field="priority",
        op_type="create_task",
        default="medium",
    )
    assert value == "medium"
    assert "Invalid priority" in caplog.text

