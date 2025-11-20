"""Durable workflow state facade used by API routes."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional

from infra.repos.factory import workflow_state_repo


def _repo():
    return workflow_state_repo()


class _BucketProxy:
    def __init__(self, bucket: str):
        self.bucket = bucket

    def __setitem__(self, key: str, value: Dict[str, Any]) -> None:
        value = dict(value)
        value.setdefault("id", key)
        _repo().upsert(self.bucket, value)

    def __contains__(self, key: str) -> bool:
        return _repo().get(self.bucket, key) is not None

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Dict[str, Any]]:
        return _repo().get(self.bucket, key) or default

    def values(self) -> Iterable[Dict[str, Any]]:
        return _repo().list(self.bucket)

    def items(self) -> Iterable[Dict[str, Any]]:
        return ((it.get("id"), it) for it in _repo().list(self.bucket))

    def clear(self) -> None:
        _repo().clear(self.bucket)

    def pop(self, key: str, default: Optional[Any] = None) -> Optional[Dict[str, Any]]:
        current = _repo().get(self.bucket, key)
        _repo().delete(self.bucket, key)
        return current if current is not None else default

    def __iter__(self) -> Iterator[str]:
        for item in _repo().list(self.bucket):
            if "id" in item:
                yield item["id"]


class _HistoryProxy:
    def append(self, entry: Dict[str, Any]) -> None:
        _repo().append_history(entry)

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        return iter(_repo().list_history())

    def list(self, limit: int = 100) -> List[Dict[str, Any]]:
        return _repo().list_history(limit)


approvals_store = _BucketProxy("approvals")
drafts_store = _BucketProxy("drafts")
created_events_store = _BucketProxy("created_events")
history_log = _HistoryProxy()

__all__ = [
    "approvals_store",
    "drafts_store",
    "created_events_store",
    "history_log",
]

