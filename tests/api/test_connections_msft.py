from __future__ import annotations
from typing import Any, Dict
import os
import types
import contextlib

import pytest
from fastapi.testclient import TestClient

from presentation.api.app import app


@pytest.fixture(autouse=True)
def _env_for_msft(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DEV_MODE", "true")
    monkeypatch.setenv("MS_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("MS_REDIRECT_URI", "http://localhost:8000/connections/ms/oauth/callback")
    # Secret may be empty for public clients in dev
    monkeypatch.setenv("MS_CLIENT_SECRET", "")
    yield


@pytest.fixture()
def client():
    return TestClient(app)


def test_oauth_start_builds_url(client: TestClient):
    r = client.get(
        "/connections/ms/oauth/start",
        params={"user_id": "u1", "tenant": "common"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    loc = r.headers.get("location", "")
    assert "login.microsoftonline.com" in loc
    assert "client_id=test-client-id" in loc
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fconnections%2Fms%2Foauth%2Fcallback" in loc
    assert "state=u1" in loc


def test_status_disconnected_when_store_unavailable(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    import services.ms_auth as ms_auth

    def _raise():
        raise RuntimeError("no store")

    monkeypatch.setattr(ms_auth, "token_store_from_env", _raise)
    r = client.get("/connections/ms/status", params={"user_id": "u1"})
    assert r.status_code == 200
    assert r.json() == {"connected": False}


def test_status_connected_when_row_present(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    import presentation.api.routes.connections_msft as routes

    class StubStore:
        def get(self, user_id: str):
            return {
                "provider": "microsoft",
                "tenant_id": "common",
                "expiry": "2099-01-01T00:00:00+00:00",
                "scopes": ["User.Read"],
            }

    monkeypatch.setattr(routes, "token_store_from_env", lambda: StubStore())
    r = client.get("/connections/ms/status", params={"user_id": "u1"})
    assert r.status_code == 200
    body = r.json()
    assert body["connected"] is True
    assert body["provider"] == "microsoft"
    assert body["tenant_id"] == "common"


def test_disconnect_deletes_token(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    import presentation.api.routes.connections_msft as routes
    calls: Dict[str, int] = {"delete": 0}

    class StubStore:
        def delete(self, user_id: str):
            calls["delete"] += 1

    monkeypatch.setattr(routes, "token_store_from_env", lambda: StubStore())
    r = client.post("/connections/ms/disconnect", params={"user_id": "u1"})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert calls["delete"] == 1


def test_oauth_callback_persists_tokens(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    import presentation.api.routes.connections_msft as routes
    saved: Dict[str, Any] = {}

    class StubStore:
        def upsert(self, user_id: str, data: Dict[str, Any]) -> None:
            saved["user_id"] = user_id
            saved.update(data)

    # Patch token store
    monkeypatch.setattr(routes, "token_store_from_env", lambda: StubStore())

    # Patch AsyncClient.post to return a fake token response
    class FakeResp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "access_token": "at",
                "refresh_token": "rt",
                "expires_in": 3600,
                "scope": "User.Read offline_access",
            }

    class FakeAsyncClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url: str, data: Dict[str, Any]):  # type: ignore[override]
            return FakeResp()

    monkeypatch.setattr(routes.httpx, "AsyncClient", FakeAsyncClient)

    r = client.get(
        "/connections/ms/oauth/callback",
        params={"code": "c", "state": "u1", "tenant": "common"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert saved.get("user_id") == "u1"
    # Encrypted tokens present
    assert "access_token" in saved and isinstance(saved["access_token"], str)
    assert "refresh_token" in saved and isinstance(saved["refresh_token"], str)
    assert saved.get("provider") == "microsoft"

