from datetime import datetime

import pytest

from app.shared.events import Event, EventBus


class TestEvent:
    """Tests for Event class."""

    def test_event_creation(self):
        """Event should be created with name and data."""
        event = Event(
            name="test.event",
            data={"key": "value"},
        )
        assert event.name == "test.event"
        assert event.data == {"key": "value"}
        assert isinstance(event.timestamp, datetime)

    def test_event_to_dict(self):
        """Event should convert to dict."""
        event = Event(
            name="test.event",
            data={"key": "value"},
        )
        result = event.to_dict()
        assert result["name"] == "test.event"
        assert result["data"] == {"key": "value"}
        assert "timestamp" in result


class TestEventBus:
    """Tests for EventBus."""

    @pytest.fixture
    def event_bus(self):
        """Create fresh EventBus instance."""
        return EventBus()

    async def test_subscribe_and_publish(self, event_bus):
        """Handler should be called when event is published."""
        called = []

        async def handler(event: Event):
            called.append(event)

        event_bus.subscribe("test.event", handler)

        event = Event(name="test.event", data={"test": True})
        await event_bus.publish(event)

        assert len(called) == 1
        assert called[0].data["test"] is True

    async def test_unsubscribe(self, event_bus):
        """Handler should stop receiving events after unsubscribe."""
        called = []

        async def handler(event: Event):
            called.append(event)

        event_bus.subscribe("test.event", handler)
        event_bus.unsubscribe("test.event", handler)

        event = Event(name="test.event", data={"test": True})
        await event_bus.publish(event)

        assert len(called) == 0

    async def test_no_handlers(self, event_bus):
        """Publishing to event with no handlers should not raise."""
        event = Event(name="no.handlers", data={})
        await event_bus.publish(event)  # Should not raise

    async def test_multiple_handlers(self, event_bus):
        """Multiple handlers should all be called."""
        results = []

        async def handler1(event: Event):
            results.append("handler1")

        async def handler2(event: Event):
            results.append("handler2")

        event_bus.subscribe("multi.event", handler1)
        event_bus.subscribe("multi.event", handler2)

        event = Event(name="multi.event", data={})
        await event_bus.publish(event)

        assert len(results) == 2
        assert "handler1" in results
        assert "handler2" in results

    def test_get_subscribers(self, event_bus):
        """Should return list of handlers."""

        async def handler1(event: Event):
            pass

        async def handler2(event: Event):
            pass

        event_bus.subscribe("get.test", handler1)
        event_bus.subscribe("get.test", handler2)

        handlers = event_bus.get_subscribers("get.test")
        assert len(handlers) == 2


class TestStatsAuthEventHandlers:
    """Tests for auth event handlers in StatsHandlers."""

    def test_on_user_registered_is_callable(self):
        """on_user_registered handler should exist and be callable."""
        from app.features.stats.events import StatsHandlers

        assert hasattr(StatsHandlers, "on_user_registered")
        assert callable(StatsHandlers.on_user_registered)

    def test_on_user_logged_in_is_callable(self):
        """on_user_logged_in handler should exist and be callable."""
        from app.features.stats.events import StatsHandlers

        assert hasattr(StatsHandlers, "on_user_logged_in")
        assert callable(StatsHandlers.on_user_logged_in)
