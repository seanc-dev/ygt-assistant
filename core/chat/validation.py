"""Token validation for LucidWork LLM contract."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from core.chat.context import ThreadContext
from core.chat.tokens import ParsedMessage, ParsedOp, ParsedRef


class ValidationErrorCode(str, Enum):
    REF_NOT_FOUND = "REF_NOT_FOUND"
    REF_FORBIDDEN = "REF_FORBIDDEN"
    OP_INVALID_ARGS = "OP_INVALID_ARGS"
    OP_CONFLICT = "OP_CONFLICT"
    SYSTEM_ERROR = "SYSTEM_ERROR"


@dataclass
class ResolvedReference:
    parsed: ParsedRef
    record: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        payload = self.parsed.to_dict()
        payload["record"] = self.record
        return payload


@dataclass
class ValidationOk:
    ok: bool
    resolved_references: List[ResolvedReference]
    parsed_operations: List[ParsedOp]


@dataclass
class ValidationError:
    ok: bool
    error_code: ValidationErrorCode
    details: Optional[Dict[str, Any]] = None


ValidationResult = Union[ValidationOk, ValidationError]


_OP_ID_ARGS: Dict[str, Dict[str, str]] = {
    "create_task": {
        "project": "project",
        "project_id": "project",
        "from_action": "action",
        "from_action_id": "action",
    },
    "update_task_status": {
        "task": "task",
        "task_id": "task",
    },
    "link_action_to_task": {
        "task": "task",
        "task_id": "task",
        "action": "action",
        "action_id": "action",
    },
    "update_action_state": {
        "action": "action",
        "action_id": "action",
    },
    "delete_task": {
        "tasks": "task",
        "task_ids": "task",
    },
    "delete_project": {
        "projects": "project",
        "project_ids": "project",
    },
}


def _lookup_reference_record(ref_type: str, identifier: str, user_id: str) -> Dict[str, Any]:
    ref_type = ref_type.lower()
    try:
        if ref_type == "task":
            from presentation.api.repos import workroom as workroom_repo

            return workroom_repo.get_task(user_id, identifier)
        if ref_type == "project":
            from presentation.api.repos import workroom as workroom_repo

            projects = workroom_repo.get_projects(user_id)
            project = next((p for p in projects if p.get("id") == identifier), None)
            if not project:
                raise ValueError(f"Project {identifier} not found")
            return project
        if ref_type in {"source", "action", "action_item"}:
            from presentation.api.repos import tasks as tasks_repo

            return tasks_repo.get_action_item(user_id, identifier)
    except ValueError as exc:
        raise exc

    raise ValueError(f"Unsupported reference type '{ref_type}'")


def _value_matches_resolved(
    ref_type: str,
    identifier: str,
    resolved_refs: List[ResolvedReference],
) -> bool:
    ref_type = ref_type.lower()
    identifier = str(identifier)
    return any(
        r.parsed.type.lower() == ref_type and r.parsed.id == identifier
        for r in resolved_refs
    )


def _normalize_values(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        if "," in raw:
            return [part.strip() for part in raw.split(",") if part.strip()]
        return [raw]
    if value is None:
        return []
    return [str(value).strip()]


def _validate_operation_args(
    op: ParsedOp,
    user_id: str,
    resolved_refs: List[ResolvedReference],
) -> Optional[ValidationError]:
    arg_map = _OP_ID_ARGS.get(op.type)
    if not arg_map:
        return None

    for arg_name, ref_type in arg_map.items():
        if arg_name not in op.args:
            continue
        values = _normalize_values(op.args[arg_name])
        if not values:
            return ValidationError(
                ok=False,
                error_code=ValidationErrorCode.OP_INVALID_ARGS,
                details={"op": op.type, "arg": arg_name, "reason": "missing value"},
            )
        for value in values:
            if _value_matches_resolved(ref_type, value, resolved_refs):
                continue
            try:
                _lookup_reference_record(ref_type, value, user_id)
            except ValueError:
                return ValidationError(
                    ok=False,
                    error_code=ValidationErrorCode.OP_INVALID_ARGS,
                    details={
                        "op": op.type,
                        "arg": arg_name,
                        "value": value,
                        "reason": "not found",
                    },
                )
    return None


def validate_parsed_message(
    parsed: ParsedMessage,
    *,
    user_context: Dict[str, Any],
) -> ValidationResult:
    """Validate parsed tokens against tenant data."""

    user_id = user_context.get("userId")
    if not user_id:
        return ValidationError(
            ok=False,
            error_code=ValidationErrorCode.SYSTEM_ERROR,
            details={"reason": "userId missing"},
        )

    resolved_refs: List[ResolvedReference] = []

    for ref in parsed.references:
        try:
            record = _lookup_reference_record(ref.type, ref.id, user_id)
        except ValueError as exc:
            return ValidationError(
                ok=False,
                error_code=ValidationErrorCode.REF_NOT_FOUND,
                details={"placeholder": ref.placeholder, "message": str(exc)},
            )
        resolved_refs.append(ResolvedReference(parsed=ref, record=record))

    for op in parsed.operations:
        error = _validate_operation_args(op, user_id, resolved_refs)
        if error:
            return error

    return ValidationOk(
        ok=True,
        resolved_references=resolved_refs,
        parsed_operations=parsed.operations,
    )


__all__ = [
    "ResolvedReference",
    "ValidationError",
    "ValidationErrorCode",
    "ValidationOk",
    "ValidationResult",
    "validate_parsed_message",
]
