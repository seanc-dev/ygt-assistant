import os
from infra.repos.settings_interfaces import SettingsRepo
from infra.memory.settings_repo import MemorySettingsRepo


def repo() -> SettingsRepo:
    # Prefer memory during pytest runs
    if os.getenv("PYTEST_CURRENT_TEST"):
        return MemorySettingsRepo()
    if os.getenv("USE_DB", "false").lower() == "true":
        try:
            from infra.supabase.settings_repo import SupabaseSettingsRepo

            return SupabaseSettingsRepo()
        except Exception:
            pass
    return MemorySettingsRepo()
