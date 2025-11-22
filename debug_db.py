import os
import sys
from typing import Any, Dict, Optional

# Add project root to path
sys.path.append(os.getcwd())

from archive.infra.supabase.client import client

def _select(table: str, params: Optional[Dict[str, Any]] = None) -> Any:
    qp = dict(params or {})
    qp.setdefault("select", "*")
    with client() as c:
        resp = c.get(f"/{table}", params=qp)
        resp.raise_for_status()
        return resp.json()

def check_tasks():
    print("Checking for tasks in Supabase...")
    try:
        tasks = _select("tasks", {"limit": "10"})
        print(f"Found {len(tasks)} tasks.")
        for t in tasks:
            print(f" - {t.get('title')} (ID: {t.get('id')}, Project: {t.get('project_id')})")
            
        if not tasks:
            print("WARNING: No tasks found!")
            
    except Exception as e:
        print(f"ERROR: Failed to fetch tasks: {e}")

if __name__ == "__main__":
    check_tasks()
