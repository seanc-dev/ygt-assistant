import base64
import hmac
import hashlib
import json
import time
from typing import Optional
from settings import ENCRYPTION_KEY, ADMIN_EMAIL, ADMIN_SECRET, SESSION_TTL_MIN, COOKIE_NAME


def _key() -> bytes:
    key = (ENCRYPTION_KEY or ADMIN_SECRET).encode()
    return hashlib.sha256(key).digest()


def issue_session(email: str, ttl_min: int = SESSION_TTL_MIN) -> str:
    payload = {"sub": email, "exp": int(time.time()) + ttl_min * 60}
    b = json.dumps(payload, separators=(",", ":")).encode()
    sig = hmac.new(_key(), b, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(b).decode() + "." + base64.urlsafe_b64encode(sig).decode()


def verify_session(token: str) -> Optional[str]:
    try:
        b64p, b64s = token.split(".")
        payload = base64.urlsafe_b64decode(b64p.encode())
        sig = base64.urlsafe_b64decode(b64s.encode())
        if not hmac.compare_digest(sig, hmac.new(_key(), payload, hashlib.sha256).digest()):
            return None
        data = json.loads(payload.decode())
        if data.get("exp", 0) < int(time.time()):
            return None
        return data.get("sub")
    except Exception:
        return None


def cookie_name() -> str:
    return COOKIE_NAME


