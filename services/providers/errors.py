from __future__ import annotations
from typing import Optional


class ProviderError(Exception):
    """Domain error raised by provider implementations.

    Attributes:
        provider: Name of the provider (e.g., "google", "stub").
        operation: The operation attempted (e.g., "list_threads", "create_event").
        status_code: Optional HTTP status or numeric code from downstream.
        hint: Optional user-facing hint to resolve the issue (avoid secrets).
    """

    def __init__(
        self,
        provider: str,
        operation: str,
        message: str,
        *,
        status_code: Optional[int] = None,
        hint: Optional[str] = None,
    ) -> None:
        self.provider = provider
        self.operation = operation
        self.status_code = status_code
        self.hint = hint
        super().__init__(message)

    def __str__(self) -> str:  # pragma: no cover - trivial string composition
        base = f"{self.provider}:{self.operation}: {super().__str__()}"
        if self.status_code is not None:
            base += f" (status={self.status_code})"
        if self.hint:
            base += f" | hint: {self.hint}"
        return base
