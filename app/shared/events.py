from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Event:
    """Base event class."""

    name: str
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


EventHandler = Callable[[Event], Awaitable[None]]


class EventBus:
    """
    Simple event bus for publish/subscribe pattern.

    Allows features to communicate without direct dependencies.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}
        self._logger = logger

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Subscribe a handler to an event."""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)
        self._logger.debug(f"Subscribed {handler.__name__} to '{event_name}'")

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        """Unsubscribe a handler from an event."""
        if event_name in self._handlers:
            try:
                self._handlers[event_name].remove(handler)
                self._logger.debug(
                    f"Unsubscribed {handler.__name__} from '{event_name}'"
                )
            except ValueError:
                pass

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        self._logger.debug(f"Publishing event '{event.name}': {event.data}")

        if event.name not in self._handlers:
            self._logger.debug(f"No handlers subscribed to '{event.name}'")
            return

        for handler in self._handlers[event.name]:
            try:
                await handler(event)
            except Exception as e:
                self._logger.error(
                    f"Error in handler {handler.__name__} for event '{event.name}': {e}"
                )

    def get_subscribers(self, event_name: str) -> list[EventHandler]:
        """Get all handlers subscribed to an event."""
        return self._handlers.get(event_name, []).copy()


event_bus = EventBus()
