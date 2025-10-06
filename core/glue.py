from __future__ import annotations
from typing import Any, Dict, List
from .retrieval import recall_by_key


def inject_prompt(base_prompt: str, keys: List[str]) -> str:
    lines = [base_prompt, "\nContext:"]
    for key in keys:
        items = recall_by_key(key)
        for it in items[:3]:
            lines.append(f"- [{it.level}] {it.key} -> {it.value}")
    return "\n".join(lines)
