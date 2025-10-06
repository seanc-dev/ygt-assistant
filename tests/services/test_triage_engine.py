from core.services.triage_engine import EmailEnvelope, triage_email


def test_rule_match_subject_and_from():
    env = EmailEnvelope(
        message_id="m1",
        sender="alice@client.com",
        subject="invoice and update",
        body_text="Please see attached invoice",
        received_at="2025-09-06T00:00:00Z",
    )
    res = triage_email(env, rules_path="config/rules.sample.yaml")
    assert any(a.type == "create_task" for a in res.actions)
    assert any("create_task" in r for r in res.rules_applied)
