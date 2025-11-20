"""Structured token parsing for LucidWork LLM Contract.

This module parses `[ref ...]` and `[op ...]` tokens embedded in user
messages. It replaces tokens with deterministic placeholders so the LLM sees
only placeholders, never the raw identifiers.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
import re
from typing import Dict, List

_TOKEN_PATTERN = re.compile(r"\[(ref|op)\s+([^\]]+)\]", re.IGNORECASE)
_PAIR_PATTERN = re.compile(
    r"(\w+):(?:\"((?:\\.|[^\"])*)\"|([^\s]+))",
)


@dataclass
class ParsedRef:
    """A reference token extracted from the message."""

    placeholder: str
    kind: str
    version: int
    type: str
    id: str
    meta: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class ParsedOp:
    """An operation token extracted from the message."""

    placeholder: str
    kind: str
    version: int
    type: str
    args: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class ParsedMessage:
    """Parsed message containing placeholders and structured tokens."""

    raw_text: str
    llm_text: str
    references: List[ParsedRef] = field(default_factory=list)
    operations: List[ParsedOp] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "raw_text": self.raw_text,
            "llm_text": self.llm_text,
            "references": [ref.to_dict() for ref in self.references],
            "operations": [op.to_dict() for op in self.operations],
        }


def _parse_key_values(body: str) -> Dict[str, str]:
    """Parse key/value pairs inside a token body.

    Supports both quoted values with spaces (key:"value with spaces") and
    unquoted values without spaces (key:value).
    """

    pairs: Dict[str, str] = {}
    for match in _PAIR_PATTERN.finditer(body):
        key = match.group(1)
        quoted_value = match.group(2)
        bare_value = match.group(3)
        if quoted_value is not None:
            value = quoted_value.replace("\\\"", "\"")
        else:
            value = bare_value or ""
        pairs[key] = value
    return pairs


def _require_field(pairs: Dict[str, str], field: str, kind: str) -> str:
    value = pairs.get(field)
    if value is None or value == "":
        raise ValueError(f"{kind} token missing required field '{field}'")
    return value


def parse_message_with_tokens(raw_text: str) -> ParsedMessage:
    """Parse a user message for structured tokens.

    Args:
        raw_text: Original message typed by the user.

    Returns:
        ParsedMessage with placeholders inserted for each token.

    Raises:
        ValueError: If a token is malformed or missing required data.
    """

    references: List[ParsedRef] = []
    operations: List[ParsedOp] = []
    llm_parts: List[str] = []

    cursor = 0
    ref_counter = 0
    op_counter = 0

    for match in _TOKEN_PATTERN.finditer(raw_text or ""):
        start, end = match.span()
        llm_parts.append(raw_text[cursor:start])
        cursor = end

        kind = match.group(1).lower()
        body = match.group(2).strip()
        pairs = _parse_key_values(body)

        version_str = _require_field(pairs, "v", kind)
        try:
            version = int(version_str)
        except ValueError as exc:
            raise ValueError(f"{kind} token has invalid version '{version_str}'") from exc

        if kind == "ref":
            ref_counter += 1
            placeholder = f"<<REF_{ref_counter}>>"
            ref_type = _require_field(pairs, "type", kind)
            ref_id = _require_field(pairs, "id", kind)
            meta = {
                k: v
                for k, v in pairs.items()
                if k not in {"v", "type", "id"}
            }
            references.append(
                ParsedRef(
                    placeholder=placeholder,
                    kind="ref",
                    version=version,
                    type=ref_type,
                    id=ref_id,
                    meta=meta,
                )
            )
            llm_parts.append(placeholder)
        else:
            op_counter += 1
            placeholder = f"<<OP_{op_counter}>>"
            op_type = _require_field(pairs, "type", kind)
            args = {
                k: v
                for k, v in pairs.items()
                if k not in {"v", "type"}
            }
            if not args:
                raise ValueError(f"op token '{op_type}' must include arguments")
            operations.append(
                ParsedOp(
                    placeholder=placeholder,
                    kind="op",
                    version=version,
                    type=op_type,
                    args=args,
                )
            )
            llm_parts.append(placeholder)

    llm_parts.append(raw_text[cursor:])
    llm_text = "".join(llm_parts)

    return ParsedMessage(
        raw_text=raw_text,
        llm_text=llm_text,
        references=references,
        operations=operations,
    )


__all__ = [
    "ParsedMessage",
    "ParsedOp",
    "ParsedRef",
    "parse_message_with_tokens",
]
