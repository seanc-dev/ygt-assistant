import secrets
import time
import hmac
import hashlib
import json
import base64
from typing import Dict, Any
from settings import ENCRYPTION_KEY, ADMIN_SECRET

_store: Dict[str, Dict[str, Any]] = {}
_ttl_sec = 600


def _key() -> bytes:
    """Derive an HMAC key from ENCRYPTION_KEY or ADMIN_SECRET."""
    key = (ENCRYPTION_KEY or ADMIN_SECRET or "state_fallback_key").encode()
    return hashlib.sha256(key).digest()


def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64u_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode())


def _sign_state(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    sig = hmac.new(_key(), raw, hashlib.sha256).digest()
    return f"{_b64u(raw)}.{_b64u(sig)}"


def _verify_state(token: str) -> Dict[str, Any] | None:
    try:
        p_b64, s_b64 = token.split(".")
        raw = _b64u_decode(p_b64)
        sig = _b64u_decode(s_b64)
        if not hmac.compare_digest(hmac.new(_key(), raw, hashlib.sha256).digest(), sig):
            return None
        data = json.loads(raw.decode())
        ts = float(data.get("ts", 0))
        if time.time() - ts > _ttl_sec:
            return None
        return data
    except Exception:
        return None


def new(provider: str, tenant_id: str, extra: Dict[str, Any] = None) -> str:
    data = {"provider": provider, "tenant_id": tenant_id, "ts": time.time()}
    if extra:
        data.update(extra)
    # Keep a best-effort in-memory fallback for backward compatibility
    token = secrets.token_urlsafe(32)
    _store[token] = data
    # Prefer stateless signed token for cross-instance callbacks
    return _sign_state(data)


def get(key: str) -> Dict[str, Any] | None:
    """Get data by key without removing it."""
    data = _verify_state(key)
    if data:
        return data
    data = _store.get(key)
    if not data:
        return None
    if time.time() - data["ts"] > _ttl_sec:
        _store.pop(key, None)
        return None
    return data


def pop(state: str) -> Dict[str, Any] | None:
    data = _verify_state(state)
    if data:
        return data
    data = _store.pop(state, None)
    if not data:
        return None
    if time.time() - data["ts"] > _ttl_sec:
        return None
    return data
