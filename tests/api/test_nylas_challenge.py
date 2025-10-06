from fastapi.testclient import TestClient
from presentation.api.app import app


def test_nylas_challenge_echo():
    c = TestClient(app)
    r = c.get("/webhooks/nylas", params={"challenge": "abc"})
    assert r.status_code == 200
    assert r.text == "abc"
