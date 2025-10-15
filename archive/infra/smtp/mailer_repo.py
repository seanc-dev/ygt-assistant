import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


class SMTPMailer:
    def __init__(self) -> None:
        self.host = os.getenv("SMTP_HOST") or ""
        _raw_port = os.getenv("SMTP_PORT") or "587"
        try:
            self.port = int(_raw_port)
        except ValueError:
            self.port = 587
        self.user = os.getenv("SMTP_USER", "")
        self.passw = os.getenv("SMTP_PASS", "")
        self.sender = os.getenv("SMTP_FROM") or "no-reply@ygt.local"
        # Use SMTPS (implicit TLS) when requested or when port is 465
        self.use_ssl = (
            os.getenv("SMTP_USE_SSL", "false").strip().lower()
            in {"1", "true", "yes", "on"}
        ) or self.port == 465

    def send(self, to: str, subject: str, html: str, text: str) -> None:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = to
        # If using Postmark SMTP, include message stream header
        stream = os.getenv("POSTMARK_MESSAGE_STREAM", "outbound")
        if stream:
            msg["X-PM-Message-Stream"] = stream
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))
        if self.use_ssl:
            with smtplib.SMTP_SSL(self.host, self.port) as s:
                if self.user:
                    s.login(self.user, self.passw)
                s.sendmail(self.sender, [to], msg.as_string())
        else:
            with smtplib.SMTP(self.host, self.port) as s:
                # Explicit EHLO before and after STARTTLS for better compatibility
                try:
                    s.ehlo()
                except Exception:
                    pass
                s.starttls()
                try:
                    s.ehlo()
                except Exception:
                    pass
                if self.user:
                    s.login(self.user, self.passw)
                s.sendmail(self.sender, [to], msg.as_string())


class PostmarkMailer:
    """Sends email via Postmark HTTP API."""

    def __init__(self) -> None:
        import httpx

        self.token = os.getenv("POSTMARK_SERVER_TOKEN", "")
        self.from_email = os.getenv(
            "POSTMARK_FROM_EMAIL", os.getenv("SMTP_FROM", "no-reply@ygt.local")
        )
        self.api_base = os.getenv("POSTMARK_API_BASE", "https://api.postmarkapp.com")
        self.client = httpx.Client(timeout=30)

    def send(self, to: str, subject: str, html: str, text: str) -> None:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Postmark-Server-Token": self.token,
        }
        # Include MessageStream for routing; default to 'outbound'
        message_stream = os.getenv("POSTMARK_MESSAGE_STREAM", "outbound")
        payload = {
            "From": self.from_email,
            "To": to,
            "Subject": subject,
            "HtmlBody": html,
            "TextBody": text,
            "MessageStream": message_stream,
        }
        resp = self.client.post(
            f"{self.api_base}/email",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
