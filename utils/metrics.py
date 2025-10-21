from __future__ import annotations
from typing import Any
import logging
import os


def increment(name: str, **tags: Any) -> None:
    """Minimal metrics stub.

    In production, replace with StatsD/OTel.
    """
    if os.getenv("DEV_MODE", "").strip().lower() in {"1", "true", "yes", "on"}:
        try:
            logging.getLogger(__name__).info("metric %s %s", name, tags)
        except Exception:
            pass

