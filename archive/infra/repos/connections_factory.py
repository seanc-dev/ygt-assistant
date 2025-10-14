import os
from infra.repos.connections_interfaces import ConnectionsRepo
from infra.memory.connections_repo import MemoryConnectionsRepo


def repo() -> ConnectionsRepo:
    # Prefer memory repo during pytest
    if os.getenv("PYTEST_CURRENT_TEST"):
        return MemoryConnectionsRepo()
    if os.getenv("USE_DB", "false").lower() == "true":
        try:
            from infra.supabase.connections_repo import SupabaseConnectionsRepo

            return SupabaseConnectionsRepo()
        except Exception:
            pass
    return MemoryConnectionsRepo()
