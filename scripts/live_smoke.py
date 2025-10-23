from __future__ import annotations
import os
import json
import requests  # type: ignore


def _is_true(v: str | None) -> bool:
    return (v or "").strip().lower() in {"1", "true", "yes", "on"}


def main() -> None:
    api = os.getenv("NEXT_PUBLIC_ADMIN_API_BASE", "http://localhost:8000")
    user = os.getenv("SMOKE_USER_ID", "local-user")
    if not _is_true(os.getenv("FEATURE_GRAPH_LIVE")):
        print("Live flags disabled; enable FEATURE_GRAPH_LIVE to run smoke.")
        return
    # 1) Inbox
    if _is_true(os.getenv("FEATURE_LIVE_LIST_INBOX")):
        r = requests.get(f"{api}/actions/live/inbox", params={"user_id": user, "limit": 5}, timeout=10)
        print("INBOX", r.status_code, r.json())
    # 2) Send
    if _is_true(os.getenv("FEATURE_LIVE_SEND_MAIL")):
        r = requests.post(
            f"{api}/actions/live/send",
            params={"user_id": user},
            json={"to": [os.getenv("SMOKE_TO", "you@example.com")], "subject": "[YGT Live Smoke]", "body": "Test"},
            timeout=10,
        )
        print("SEND", r.status_code, r.json())
    # 3) Create+Undo event
    if _is_true(os.getenv("FEATURE_LIVE_CREATE_EVENTS")):
        ev = {"title": "YGT Smoke", "start": "2025-10-25T09:00:00Z", "end": "2025-10-25T09:30:00Z"}
        r = requests.post(f"{api}/actions/live/create-events", params={"user_id": user}, json={"events": [ev]}, timeout=10)
        data = r.json()
        print("CREATE", r.status_code, data)
        if (data.get("events") or []) and (data["events"][0].get("id")):
            ev_id = data["events"][0]["id"]
            r2 = requests.post(f"{api}/actions/live/undo-event/{ev_id}", params={"user_id": user}, timeout=10)
            print("UNDO", r2.status_code, r2.json())


if __name__ == "__main__":
    main()


