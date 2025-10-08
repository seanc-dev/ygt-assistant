import os
import json
import pytest
from fastapi.testclient import TestClient
from presentation.api.app import app

pytestmark = pytest.mark.e2e


def test_whatsapp_verify_and_message_parse(monkeypatch):
    client = TestClient(app)
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "secret")
    # Verify challenge
    r = client.get("/whatsapp/webhook", params={"mode": "subscribe", "token": "secret", "challenge": "123"})
    assert r.status_code == 200
    assert r.text == "123"
    # Message parse
    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{"type": "text", "text": {"body": "approve 123"}}],
                    "contacts": [{"wa_id": "123"}],
                    "metadata": {"phone_number_id": "pnid"}
                }
            }]
        }]
    }
    r2 = client.post("/whatsapp/webhook", json=payload)
    assert r2.status_code == 200
    data = r2.json()
    assert data["ok"] is True
    assert data["parsed"]["type"] == "text"
    assert data["parsed"]["user_id"] in {"123", "pnid"}
