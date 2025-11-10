import pytest
from utils.command_dispatcher import HANDLERS, dispatch


class TestHandlerRegistration:
    def test_handlers_dict_exists(self):
        """HANDLERS dict exists for backward compatibility."""
        assert isinstance(HANDLERS, dict)
        # Legacy handlers have been removed - HANDLERS is now empty
        assert len(HANDLERS) == 0


class TestDispatchFunction:
    def test_dispatch_raises_not_implemented(self):
        """All dispatch calls now raise NotImplementedError since legacy handlers are removed."""
        with pytest.raises(NotImplementedError):
            dispatch("nonexistent_action", {})

    @pytest.mark.parametrize(
        "action, details",
        [
            ("list_all", {}),
            ("list_todays_events", {}),
        ],
    )
    def test_dispatch_legacy_actions_raise_not_implemented(self, action, details):
        """Legacy actions raise NotImplementedError."""
        with pytest.raises(NotImplementedError):
            dispatch(action, details)
