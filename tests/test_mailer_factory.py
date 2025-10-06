from infra.memory.mailer_repo import MemoryMailer
from infra.repos import mailer_factory
import infra.smtp.mailer_repo as smtp_module
from infra.smtp.mailer_repo import PostmarkMailer, SMTPMailer


def test_mailer_factory_prefers_postmark_over_smtp(monkeypatch):
    monkeypatch.delenv("USE_POSTMARK", raising=False)
    monkeypatch.setenv("POSTMARK_SERVER_TOKEN", "pm-token")
    monkeypatch.setenv("USE_SMTP", "true")

    m = mailer_factory.mailer()

    assert isinstance(m, PostmarkMailer)


def test_mailer_factory_accepts_truthy_use_postmark_flag(monkeypatch):
    monkeypatch.delenv("POSTMARK_SERVER_TOKEN", raising=False)
    monkeypatch.setenv("USE_POSTMARK", "1")
    monkeypatch.setenv("USE_SMTP", "true")

    m = mailer_factory.mailer()

    assert isinstance(m, PostmarkMailer)


def test_mailer_factory_falls_back_to_smtp_then_memory(monkeypatch):
    monkeypatch.delenv("POSTMARK_SERVER_TOKEN", raising=False)
    monkeypatch.delenv("USE_POSTMARK", raising=False)
    monkeypatch.setenv("USE_SMTP", "true")

    smtp_mailer = mailer_factory.mailer()

    assert isinstance(smtp_mailer, SMTPMailer)

    monkeypatch.setenv("USE_SMTP", "false")

    memory_mailer = mailer_factory.mailer()

    assert isinstance(memory_mailer, MemoryMailer)

    monkeypatch.delenv("USE_SMTP", raising=False)
    memory_again = mailer_factory.mailer()
    assert isinstance(memory_again, MemoryMailer)


def test_mailer_factory_falls_back_to_smtp_when_postmark_init_fails(monkeypatch):
    monkeypatch.delenv("USE_POSTMARK", raising=False)
    monkeypatch.setenv("POSTMARK_SERVER_TOKEN", "pm-token")
    monkeypatch.setenv("USE_SMTP", "true")

    def boom(self):
        raise RuntimeError("postmark boom")

    monkeypatch.setattr(smtp_module.PostmarkMailer, "__init__", boom, raising=False)

    smtp_called: dict[str, bool] = {}

    def smtp_init(self):
        smtp_called["called"] = True

    monkeypatch.setattr(smtp_module.SMTPMailer, "__init__", smtp_init, raising=False)

    m = mailer_factory.mailer()

    assert isinstance(m, SMTPMailer)
    assert smtp_called.get("called") is True
