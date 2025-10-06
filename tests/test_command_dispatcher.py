import pytest
from utils.command_dispatcher import HANDLERS, dispatch


class TestHandlerRegistration:
    def test_all_expected_actions_present(self):
        expected = [
            "list_todays_events",
            "list_all",
            "list_events_only",
            "list_reminders_only",
            "create_event",
            "delete_event",
            "move_event",
            "add_notification",
        ]
        for action in expected:
            assert action in HANDLERS, f"Handler for '{action}' not registered"


class TestDispatchFunction:
    def test_dispatch_unknown_raises(self):
        with pytest.raises(KeyError):
            dispatch("nonexistent_action", {})

    @pytest.mark.parametrize(
        "action, details",
        [
            ("list_all", {}),
            ("list_todays_events", {}),
        ],
    )
    def test_dispatch_calls_handler(self, action, details):
        # Should not raise for registered handlers
        assert dispatch(action, details) is None
