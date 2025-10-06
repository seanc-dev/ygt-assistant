from __future__ import annotations
from typing import Any, Dict

SENSITIVE_KEYS = {"email", "phone", "token"}


def redact(item: Dict[str, Any], *, risk: str | None = None) -> Dict[str, Any]:
    if risk and risk.lower() in {"high", "critical"}:
        redacted = {}
        for k, v in item.items():
            redacted[k] = "[redacted]" if k in SENSITIVE_KEYS else v
        return redacted
    return item
