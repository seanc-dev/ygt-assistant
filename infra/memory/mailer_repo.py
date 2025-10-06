from typing import List, Dict

_outbox: List[Dict] = []


class MemoryMailer:
    def send(self, to: str, subject: str, html: str, text: str) -> None:
        _outbox.append({"to": to, "subject": subject, "html": html, "text": text})

    def dump(self) -> List[Dict]:
        return list(_outbox)
