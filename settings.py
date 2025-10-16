import os
from cryptography.fernet import Fernet


def _is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _is_testing() -> bool:
    # PYTEST_CURRENT_TEST is populated while tests are executing; allow TESTING flag for early imports.
    return bool(os.getenv("PYTEST_CURRENT_TEST")) or _is_truthy(os.getenv("TESTING"))


def _is_dev() -> bool:
    return _is_truthy(os.getenv("DEV_MODE"))


# Feature flags and defaults
ENABLE_ADMIN = os.getenv("ENABLE_ADMIN", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
USE_PORTS = os.getenv("USE_PORTS", "false").lower() == "true"
VERIFY_NYLAS = os.getenv("VERIFY_NYLAS", "false").lower() == "true"
NYLAS_SIGNING_SECRET = os.getenv("NYLAS_SIGNING_SECRET", "")
DEFAULT_TZ = os.getenv("TZ", "Pacific/Auckland")
DRY_RUN_DEFAULT = os.getenv("DRY_RUN_DEFAULT", "true").lower() == "true"
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_TASKS_DB_ID = os.getenv("NOTION_TASKS_DB_ID", "")
NOTION_CRM_DB_ID = os.getenv("NOTION_CRM_DB_ID", "")
TENANT_DEFAULT = os.getenv("TENANT_DEFAULT", "tenant-default")
USE_DB = os.getenv("USE_DB", "false").lower() == "true"
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
# Prefer project convention SUPABASE_API_SECRET, fallback to SUPABASE_SERVICE_KEY for legacy
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_API_SECRET") or os.getenv(
    "SUPABASE_SERVICE_KEY", ""
)
NOTION_CLIENT_ID = os.getenv("NOTION_CLIENT_ID", "")
NOTION_CLIENT_SECRET = os.getenv("NOTION_CLIENT_SECRET", "")
NOTION_REDIRECT_URI = os.getenv(
    "NOTION_REDIRECT_URI", "http://localhost:8000/oauth/callback?provider=notion"
)
NYLAS_CLIENT_ID = os.getenv("NYLAS_CLIENT_ID", "")
NYLAS_CLIENT_SECRET = os.getenv("NYLAS_CLIENT_SECRET", "")
NYLAS_API_URL = os.getenv("NYLAS_API_URL", "https://api.us.nylas.com")
NYLAS_REDIRECT_URI = os.getenv(
    "NYLAS_REDIRECT_URI", "https://api.coachflow.nz/oauth/nylas/callback"
)
MOCK_OAUTH = os.getenv("MOCK_OAUTH", "true").lower() == "true"
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
_ADMIN_SECRET_DEFAULT = "change-me-long-random"
ADMIN_SECRET = os.getenv("ADMIN_SECRET", _ADMIN_SECRET_DEFAULT)
SESSION_TTL_MIN = int(os.getenv("SESSION_TTL_MIN", "60"))
COOKIE_NAME = os.getenv("COOKIE_NAME", "admin_session")
ADMIN_UI_ORIGIN = os.getenv("ADMIN_UI_ORIGIN", "http://localhost:3000")
CLIENT_UI_ORIGIN = os.getenv("CLIENT_UI_ORIGIN", "http://localhost:3000")


def _enforce_secret_hardening() -> bool:
    # Permit defaults in explicit dev/test contexts to avoid breaking local setups.
    if _is_testing() or _is_dev():
        return False
    if _is_truthy(os.getenv("ALLOW_INSECURE_DEFAULTS")):
        return False
    return True


def _validate_admin_secret(secret: str) -> str:
    if not _enforce_secret_hardening():
        # In dev/test, auto-generate a strong secret when unset or using the insecure default
        if not secret or secret == _ADMIN_SECRET_DEFAULT:
            import secrets as _secrets
            return _secrets.token_urlsafe(32)
        return secret
    if not secret:
        raise RuntimeError("ADMIN_SECRET must be configured")
    if secret == _ADMIN_SECRET_DEFAULT:
        raise RuntimeError(
            "ADMIN_SECRET uses the insecure default. Set ADMIN_SECRET to a strong random value."
        )
    if len(secret) < 16:
        raise RuntimeError("ADMIN_SECRET must be at least 16 characters long.")
    return secret


def _validate_encryption_key(key: str) -> str:
    if not _enforce_secret_hardening():
        # In dev/test, auto-generate a Fernet key when unset
        if not key:
            return Fernet.generate_key().decode()
        return key
    if not key:
        raise RuntimeError("ENCRYPTION_KEY must be configured with a Fernet key.")
    try:
        Fernet(key.encode())
    except Exception as exc:  # pragma: no cover - defensive programming
        raise RuntimeError(
            "ENCRYPTION_KEY must be a base64-encoded 32 byte Fernet key."
        ) from exc
    return key


ADMIN_SECRET = _validate_admin_secret(ADMIN_SECRET)
ENCRYPTION_KEY = _validate_encryption_key(ENCRYPTION_KEY)
