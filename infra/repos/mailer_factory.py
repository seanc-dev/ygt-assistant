import os
from infra.memory.mailer_repo import MemoryMailer


def _is_true(value: str | None) -> bool:
    """Interpret common truthy string values."""

    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def mailer():
    # Prefer Postmark HTTP API if configured via flag or token
    use_postmark = _is_true(os.getenv("USE_POSTMARK"))
    if use_postmark or os.getenv("POSTMARK_SERVER_TOKEN"):
        try:
            from infra.smtp.mailer_repo import PostmarkMailer

            return PostmarkMailer()
        except ImportError:
            # PostmarkMailer not available
            pass
        except Exception:
            # Fall back silently when Postmark init fails for other reasons
            pass
    # Fallback to SMTP if flag is truthy
    if _is_true(os.getenv("USE_SMTP")):
        try:
            from infra.smtp.mailer_repo import SMTPMailer

            return SMTPMailer()
        except ImportError:
            # SMTPMailer not available
            pass
        except Exception:
            # Fall back to memory mailer if SMTP initialization fails
            pass
    # Default to in-memory mailer
    return MemoryMailer()
