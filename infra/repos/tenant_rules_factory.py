import os
from infra.repos.tenant_rules_interfaces import TenantsRepo, RulesRepo
from infra.memory.tenants_repo import MemoryTenantsRepo
from infra.memory.rules_repo import MemoryRulesRepo


def _use_db() -> bool:
    # Force memory during pytest runs
    if os.getenv("PYTEST_CURRENT_TEST"):
        return False
    return os.getenv("USE_DB", "false").lower() == "true"


def tenants_repo() -> TenantsRepo:
    if _use_db():
        try:
            from infra.supabase.tenants_repo import SupabaseTenantsRepo

            return SupabaseTenantsRepo()
        except Exception:
            pass
    return MemoryTenantsRepo()


def rules_repo() -> RulesRepo:
    if _use_db():
        try:
            from infra.supabase.rules_repo import SupabaseRulesRepo

            return SupabaseRulesRepo()
        except Exception:
            pass
    return MemoryRulesRepo()
