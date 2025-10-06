try:  # pragma: no cover - allow lint to pass without fastapi installed locally
    from fastapi.testclient import TestClient  # type: ignore
except Exception:  # pragma: no cover
    TestClient = None  # type: ignore
from presentation.api.app import app


def test_profile_endpoint_authentication():
    if TestClient is None:
        return
    client = TestClient(app)
    r = client.get("/api/profile")
    # Must be protected
    assert r.status_code == 401


def test_profile_patch_endpoint_exists():
    if TestClient is None:
        return
    client = TestClient(app)
    r = client.patch("/api/profile", json={"name": "Test"})
    # Protected as well
    assert r.status_code == 401
