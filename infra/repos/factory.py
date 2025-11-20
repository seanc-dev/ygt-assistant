"""Central factory for durable repos used by the API and services."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from infra.repos.sqlite_repos import (
    AuditRepo,
    ClientSessionRepo,
    IdempotencyRepo,
    WorkflowStateRepo,
)


def _db_path() -> Optional[str]:
    return os.getenv("DATA_STORE_PATH")


@lru_cache()
def workflow_state_repo(path: Optional[str] = None) -> WorkflowStateRepo:
    return WorkflowStateRepo(path or _db_path())


@lru_cache()
def idempotency_repo(path: Optional[str] = None) -> IdempotencyRepo:
    return IdempotencyRepo(path or _db_path())


@lru_cache()
def audit_repo(path: Optional[str] = None) -> AuditRepo:
    return AuditRepo(path or _db_path())


@lru_cache()
def client_sessions_repo(path: Optional[str] = None) -> ClientSessionRepo:
    return ClientSessionRepo(path or _db_path())


__all__ = [
    "workflow_state_repo",
    "idempotency_repo",
    "audit_repo",
    "client_sessions_repo",
]

