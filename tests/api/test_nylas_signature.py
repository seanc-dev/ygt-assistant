import hmac
import hashlib
import json
from fastapi.testclient import TestClient
from presentation.api.app import app


def test_nylas_signature_verified(monkeypatch):
    monkeypatch.setenv("VERIFY_NYLAS", "true")
    monkeypatch.setenv("NYLAS_SIGNING_SECRET", "s3cr3t")
    client = TestClient(app)
    body = {"type": "email.created", "data": {"id": "m1", "from": [{"email": "a@b.com"}]}}
    raw = json.dumps(body).encode()
    sig = hmac.new(b"s3cr3t", raw, hashlib.sha256).hexdigest()
    r_ok = client.post("/webhooks/nylas", data=raw, headers={"X-Nylas-Signature": sig})
    assert r_ok.status_code == 200
    r_bad = client.post("/webhooks/nylas", data=raw, headers={"X-Nylas-Signature": "bad"})
    assert r_bad.status_code == 401


