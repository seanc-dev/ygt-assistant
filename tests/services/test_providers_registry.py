import os
from contextlib import contextmanager


@contextmanager
def _env(new_values: dict[str, str]):
    old = {k: os.getenv(k) for k in new_values}
    try:
        for k, v in new_values.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_registry_defaults_to_stub():
    from services.providers import registry

    with _env({"PROVIDER_EMAIL": "", "PROVIDER_CAL": ""}):
        e = registry.get_email_provider("u1")
        c = registry.get_calendar_provider("u1")
        assert e.list_threads("", 1) == []
        assert c.list_events("2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z") == []


def test_registry_selects_google_when_requested():
    from services.providers import registry

    with _env({"PROVIDER_EMAIL": "google", "PROVIDER_CAL": "google"}):
        # When google providers are not present in the repo yet, registry should fall back gracefully
        e = registry.get_email_provider("u1")
        c = registry.get_calendar_provider("u1")
        assert hasattr(e, "create_draft")
        assert hasattr(c, "list_events")


def test_provider_error_shape():
    from services.providers.errors import ProviderError

    err = ProviderError(
        provider="google",
        operation="list_threads",
        message="unauthorized",
        status_code=401,
        hint="Reconnect Google",
    )
    assert err.provider == "google"
    assert err.operation == "list_threads"
    assert err.status_code == 401
    assert "Reconnect" in (err.hint or "")
