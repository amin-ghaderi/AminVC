"""
E4.0 EventBus — synchronous in-process pub/sub.

No wildcards. Subscriber failures are logged and isolated.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from app.contracts.events import EventEnvelope
from app.events.store import EventStore

logger = logging.getLogger(__name__)

EventCallback = Callable[[EventEnvelope], Any]


class EventBus:
    def __init__(self, store: EventStore | None = None) -> None:
        self._subscribers: dict[str, list[EventCallback]] = defaultdict(list)
        self._store = store if store is not None else EventStore()

    def subscribe(self, event_type: str, callback: EventCallback) -> None:
        if "*" in event_type:
            raise ValueError("wildcard subscriptions are not supported")
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: EventCallback) -> None:
        callbacks = self._subscribers.get(event_type)
        if not callbacks:
            return
        try:
            callbacks.remove(callback)
        except ValueError:
            pass
        if not callbacks:
            del self._subscribers[event_type]

    def subscriber_count(self, event_type: str) -> int:
        return len(self._subscribers.get(event_type, []))

    def publish(self, event: EventEnvelope) -> None:
        try:
            self._store.append(event)
        except Exception as exc:  # noqa: BLE001 — history must never break delivery
            logger.debug("event store append failed: %s", exc)
        self._dispatch(event)

    def publish_now(self, event: EventEnvelope) -> None:
        self._dispatch(event)

    @property
    def store(self) -> EventStore:
        return self._store

    def _dispatch(self, event: EventEnvelope) -> None:
        for callback in list(self._subscribers.get(event.event_type, [])):
            try:
                callback(event)
            except Exception:
                logger.exception(
                    "event subscriber failed: type=%s callback=%r",
                    event.event_type,
                    callback,
                )
