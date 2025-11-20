from fastapi.testclient import TestClient
from presentation.api.app import app


def test_nylas_routes_removed():
    client = TestClient(app)
    assert client.get("/webhooks/nylas").status_code == 404
    assert client.get("/oauth/nylas/start").status_code == 404
