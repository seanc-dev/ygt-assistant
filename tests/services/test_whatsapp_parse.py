from services.whatsapp import parse_webhook


def test_parse_text_message():
    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{"type": "text", "text": {"body": "hello"}}],
                    "contacts": [{"wa_id": "123"}]
                }
            }]
        }]
    }
    out = parse_webhook(payload)
    assert out["type"] == "text"
    assert out["text"] == "hello"
    assert out["user_id"] == "123"
