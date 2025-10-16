from __future__ import annotations
import os
import sys
from pathlib import Path


def main() -> int:
    db_url = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
    if not db_url:
        print("SUPABASE_DB_URL not set; cannot apply migrations. Set it to a Postgres connection string.")
        return 2
    try:
        import psycopg
    except Exception:
        print("psycopg not installed. Add 'psycopg[binary]' to requirements and reinstall.")
        return 3

    migrations_dir = Path(__file__).parent.parent / "supabase" / "migrations"
    files = sorted(p for p in migrations_dir.glob("*.sql"))
    if not files:
        print("No migration files found.")
        return 0

    applied = 0
    with psycopg.connect(db_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            for f in files:
                sql = f.read_text()
                try:
                    cur.execute(sql)
                    applied += 1
                    print(f"applied: {f.name}")
                except Exception as e:
                    # Continue on idempotent failures
                    print(f"warning: failed {f.name}: {e}")
    print(f"completed. attempted={len(files)} applied={applied}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


