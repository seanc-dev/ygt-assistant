import os
from infra.repos.interfaces import (
    IdempotencyRepo,
    AuditRepo,
    UsersRepo,
    ClientSessionsRepo,
)
from infra.memory.idempotency_repo import MemoryIdempotencyRepo
from infra.memory.audit_repo import MemoryAuditRepo


def _use_db() -> bool:
    # Prefer memory repos during pytest runs
    if os.getenv("PYTEST_CURRENT_TEST"):
        return False
    return os.getenv("USE_DB", "false").lower() == "true"


_memory_idempotency_repo: IdempotencyRepo | None = None
_memory_audit_repo: AuditRepo | None = None
_memory_users_repo: UsersRepo | None = None
_memory_client_sessions_repo: ClientSessionsRepo | None = None


def idempotency_repo() -> IdempotencyRepo:
    if _use_db():
        try:
            from infra.supabase.idempotency_repo import SupabaseIdempotencyRepo

            return SupabaseIdempotencyRepo()
        except Exception:
            pass
    global _memory_idempotency_repo
    if _memory_idempotency_repo is None:
        _memory_idempotency_repo = MemoryIdempotencyRepo()
    return _memory_idempotency_repo


def audit_repo() -> AuditRepo:
    if _use_db():
        try:
            from infra.supabase.audit_repo import SupabaseAuditRepo

            return SupabaseAuditRepo()
        except Exception:
            pass
    global _memory_audit_repo
    if _memory_audit_repo is None:
        _memory_audit_repo = MemoryAuditRepo()
    return _memory_audit_repo


def users_repo() -> UsersRepo:
    if _use_db():
        try:
            from infra.supabase.users_repo import SupabaseUsersRepo

            return SupabaseUsersRepo()
        except Exception:
            pass
    from infra.memory.users_repo import MemoryUsersRepo

    global _memory_users_repo
    if _memory_users_repo is None:
        _memory_users_repo = MemoryUsersRepo()
    return _memory_users_repo


def client_sessions_repo() -> ClientSessionsRepo:
    if _use_db():
        try:
            from infra.supabase.client_sessions_repo import SupabaseClientSessionsRepo

            return SupabaseClientSessionsRepo()
        except Exception:
            pass
    from infra.memory.client_sessions_repo import MemoryClientSessionsRepo

    global _memory_client_sessions_repo
    if _memory_client_sessions_repo is None:
        _memory_client_sessions_repo = MemoryClientSessionsRepo()
    return _memory_client_sessions_repo
