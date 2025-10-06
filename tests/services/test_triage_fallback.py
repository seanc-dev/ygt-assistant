from core.services.triage_engine import EmailEnvelope, triage_email


def test_triage_fallback_emits_task_when_no_rule_matches():
    env = EmailEnvelope(
        message_id="z1",
        sender="noreply@random.com",
        subject="Hello",
        body_text="Ping",
        received_at="2025-09-06T00:00:00Z",
    )
    res = triage_email(env, rules_path="config/empty_rules.yaml")
    assert any(a.type == "create_task" for a in res.actions)
    assert "fallback_create_task" in res.rules_applied


