from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional


def _default_db_path() -> str:
    base = os.getenv("DATA_DIR", ".data")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "lucidwork.db")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class _SQLite:
    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path or _default_db_path()
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self._conn as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS state_items (
                    bucket TEXT NOT NULL,
                    id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (bucket, id)
                )
                """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS idempotency (
                    tenant_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, kind, external_id)
                )
                """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    request_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS client_sessions (
                    token_hash TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def execute(self, sql: str, params: Iterable[Any] = ()) -> sqlite3.Cursor:
        with self._lock:
            cur = self._conn.execute(sql, params)
            self._conn.commit()
            return cur

    def query(self, sql: str, params: Iterable[Any] = ()) -> List[sqlite3.Row]:
        with self._lock:
            cur = self._conn.execute(sql, params)
            rows = cur.fetchall()
            return rows


class WorkflowStateRepo:
    def __init__(self, path: Optional[str] = None) -> None:
        self._db = _SQLite(path)

    def upsert(self, bucket: str, item: Dict[str, Any]) -> None:
        item_id = item.get("id")
        if not item_id:
            raise ValueError("state items require an 'id' field")
        ts = _utc_now_iso()
        payload = json.dumps(item)
        self._db.execute(
            """
            INSERT INTO state_items(bucket, id, payload, created_at, updated_at)
            VALUES(?,?,?,?,?)
            ON CONFLICT(bucket, id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at
            """,
            (bucket, item_id, payload, ts, ts),
        )

    def get(self, bucket: str, item_id: str) -> Optional[Dict[str, Any]]:
        rows = self._db.query(
            "SELECT payload FROM state_items WHERE bucket=? AND id=?", (bucket, item_id)
        )
        if not rows:
            return None
        return json.loads(rows[0]["payload"])

    def list(self, bucket: str) -> List[Dict[str, Any]]:
        rows = self._db.query(
            "SELECT payload FROM state_items WHERE bucket=? ORDER BY updated_at DESC",
            (bucket,),
        )
        return [json.loads(r["payload"]) for r in rows]

    def update(self, bucket: str, item_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        current = self.get(bucket, item_id)
        if not current:
            return None
        current.update(updates)
        self.upsert(bucket, current)
        return current

    def clear(self, bucket: str) -> None:
        self._db.execute("DELETE FROM state_items WHERE bucket=?", (bucket,))

    def delete(self, bucket: str, item_id: str) -> None:
        self._db.execute(
            "DELETE FROM state_items WHERE bucket=? AND id=?", (bucket, item_id)
        )

    # History helpers
    def append_history(self, entry: Dict[str, Any]) -> None:
        payload = json.dumps(entry)
        self._db.execute(
            "INSERT INTO history(payload, created_at) VALUES(?,?)",
            (payload, _utc_now_iso()),
        )

    def list_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        rows = self._db.query(
            "SELECT payload FROM history ORDER BY id DESC LIMIT ?", (max(0, limit),)
        )
        return [json.loads(r["payload"]) for r in rows]


class IdempotencyRepo:
    def __init__(self, path: Optional[str] = None) -> None:
        self._db = _SQLite(path)

    def seen(self, tenant_id: str, kind: str, ext: str) -> bool:
        rows = self._db.query(
            "SELECT 1 FROM idempotency WHERE tenant_id=? AND kind=? AND external_id=?",
            (tenant_id, kind, ext),
        )
        return bool(rows)

    def record(self, tenant_id: str, kind: str, ext: str) -> None:
        self._db.execute(
            "INSERT OR IGNORE INTO idempotency(tenant_id, kind, external_id, created_at) VALUES(?,?,?,?)",
            (tenant_id, kind, ext, _utc_now_iso()),
        )


class AuditRepo:
    def __init__(self, path: Optional[str] = None) -> None:
        self._db = _SQLite(path)

    def write(self, entry: Dict[str, Any]) -> str:
        rid = entry.get("request_id") or str(uuid.uuid4())
        payload = json.dumps(entry)
        self._db.execute(
            "INSERT OR REPLACE INTO audit_log(request_id, payload, created_at) VALUES(?,?,?)",
            (rid, payload, _utc_now_iso()),
        )
        return rid

    def get(self, request_id: str) -> Optional[Dict[str, Any]]:
        rows = self._db.query("SELECT payload FROM audit_log WHERE request_id=?", (request_id,))
        if not rows:
            return None
        return json.loads(rows[0]["payload"])


class ClientSessionRepo:
    def __init__(self, path: Optional[str] = None) -> None:
        self._db = _SQLite(path)

    def create(self, *, token_hash: str, user_id: str, expires_at: str) -> None:
        self._db.execute(
            "INSERT OR REPLACE INTO client_sessions(token_hash, user_id, expires_at, created_at) VALUES(?,?,?,?)",
            (token_hash, user_id, expires_at, _utc_now_iso()),
        )

    def get(self, token_hash: str) -> Optional[Dict[str, Any]]:
        rows = self._db.query(
            "SELECT user_id, expires_at FROM client_sessions WHERE token_hash=?",
            (token_hash,),
        )
        if not rows:
            return None
        row = rows[0]
        return {"user_id": row["user_id"], "expires_at": row["expires_at"]}

