from __future__ import annotations

import json
import os
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _store_path() -> str:
    base = os.getenv("DATA_DIR", ".data")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "core_store.db")


@dataclass
class CoreMemoryItem:
    id: str
    level: str  # episodic | semantic | procedural | narrative
    key: str
    value: Dict[str, Any]
    vector: Optional[List[float]] = None
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime = datetime.now(timezone.utc)
    last_used_at: Optional[datetime] = None


class PersistentCoreStore:
    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path or _store_path()
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self._conn as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS core_memory (
                    id TEXT PRIMARY KEY,
                    level TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    vector TEXT,
                    meta TEXT,
                    created_at TEXT NOT NULL,
                    last_used_at TEXT
                )
                """
            )

    def upsert(self, item: CoreMemoryItem) -> None:
        payload = json.dumps(item.value)
        vector = json.dumps(item.vector) if item.vector is not None else None
        meta = json.dumps(item.meta) if item.meta is not None else None
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO core_memory(id, level, key, value, vector, meta, created_at, last_used_at)
                VALUES(?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                    level=excluded.level,
                    key=excluded.key,
                    value=excluded.value,
                    vector=excluded.vector,
                    meta=excluded.meta,
                    last_used_at=excluded.last_used_at
                """,
                (
                    item.id,
                    item.level,
                    item.key,
                    payload,
                    vector,
                    meta,
                    item.created_at.isoformat(),
                    item.last_used_at.isoformat() if item.last_used_at else None,
                ),
            )
            self._conn.commit()

    def get_by_id(self, item_id: str) -> Optional[CoreMemoryItem]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM core_memory WHERE id=?", (item_id,)
            ).fetchone()
            if not row:
                return None
            self._conn.execute(
                "UPDATE core_memory SET last_used_at=? WHERE id=?",
                (datetime.now(timezone.utc).isoformat(), item_id),
            )
            self._conn.commit()
        return self._row_to_item(row)

    def _row_to_item(self, row: sqlite3.Row) -> CoreMemoryItem:
        return CoreMemoryItem(
            id=row["id"],
            level=row["level"],
            key=row["key"],
            value=json.loads(row["value"]),
            vector=json.loads(row["vector"]) if row["vector"] else None,
            meta=json.loads(row["meta"]) if row["meta"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            last_used_at=datetime.fromisoformat(row["last_used_at"])
            if row["last_used_at"]
            else None,
        )

    def list_by_level(self, level: str) -> List[CoreMemoryItem]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM core_memory WHERE level=? ORDER BY created_at DESC",
                (level,),
            ).fetchall()
        return [self._row_to_item(r) for r in rows]

    def get_by_key(self, key: str, level: Optional[str] = None) -> List[CoreMemoryItem]:
        sql = "SELECT * FROM core_memory WHERE key=?"
        params: List[Any] = [key]
        if level:
            sql += " AND level=?"
            params.append(level)
        sql += " ORDER BY created_at DESC"
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_item(r) for r in rows]


_STORE_SINGLETON: PersistentCoreStore | None = None


def get_store() -> PersistentCoreStore:
    global _STORE_SINGLETON
    if _STORE_SINGLETON is None:
        _STORE_SINGLETON = PersistentCoreStore()
    return _STORE_SINGLETON

