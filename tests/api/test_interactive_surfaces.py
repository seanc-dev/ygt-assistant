import pytest

from presentation.api.services.interactive_surfaces import validate_workroom_surfaces


def test_validate_workroom_surfaces_filters_and_limits():
    surface_input = {
        "tasks": [{"id": "task-1"}, {"id": "task-2"}],
        "events": [{"id": "event-1"}],
        "docs": [{"id": "doc-1"}],
        "queueItems": [{"id": "queue-1"}],
    }

    surfaces = [
        {
            "surface_id": "s1",
            "kind": "priority_list_v1",
            "title": "Priorities",
            "payload": {
                "items": [
                    {"rank": 1, "taskId": "task-1", "label": "Do it"},
                    {"rank": 2, "taskId": "task-2", "label": "Then this"},
                ]
            },
        },
        {
            "surface_id": "s2",
            "kind": "priority_list_v1",
            "title": "Unknown task",
            "payload": {"items": [{"rank": 1, "taskId": "missing", "label": "Nope"}]},
        },
        {
            "surface_id": "s3",
            "kind": "triage_table_v1",
            "title": "Triage",
            "payload": {
                "groups": [
                    {
                        "groupId": "g1",
                        "label": "Inbox",
                        "items": [
                            {
                                "queueItemId": "queue-1",
                                "source": "email",
                                "subject": "Email from CFO",
                                "approveOp": "approve",
                                "declineOp": "decline",
                            }
                        ],
                    }
                ]
            },
        },
        {
            "surface_id": "s4",
            "kind": "today_schedule_v1",
            "title": "Schedule",
            "payload": {
                "blocks": [
                    {
                        "blockId": "b1",
                        "type": "event",
                        "eventId": "unknown-event",
                        "label": "Unknown",
                        "start": "",
                        "end": "",
                        "isLocked": False,
                    }
                ]
            },
        },
    ]

    validated = validate_workroom_surfaces(surfaces, surface_input, limit=2)

    assert [s["surface_id"] for s in validated] == ["s1", "s3"]


def test_validate_workroom_surfaces_rejects_bad_navigation():
    surface_input = {"tasks": [{"id": "task-1"}], "events": []}
    surfaces = [
        {
            "surface_id": "s1",
            "kind": "what_next_v1",
            "title": "Next",
            "payload": {
                "primary": {
                    "headline": "Focus",
                    "target": {"destination": "calendar_event", "eventId": "missing"},
                }
            },
        },
        {
            "surface_id": "s2",
            "kind": "what_next_v1",
            "title": "Valid",
            "payload": {
                "primary": {
                    "headline": "Do task",
                    "target": {"destination": "workroom_task", "taskId": "task-1"},
                }
            },
        },
    ]

    validated = validate_workroom_surfaces(surfaces, surface_input, limit=5)

    assert [s["surface_id"] for s in validated] == ["s2"]
