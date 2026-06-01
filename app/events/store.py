"""E4.0 in-memory event history with optional jsonl persistence."""

from __future__ import annotations

import json
import logging
from collections import deque

from app.config.settings import AppSettings
from app.contracts.events import MAX_EVENT_HISTORY, EventEnvelope
from app.events.layout import EventsLayoutService

logger = logging.getLogger(__name__)


class EventStore:
    def __init__(
        self,
        settings: AppSettings | None = None,
        *,
        max_events: int = MAX_EVENT_HISTORY,
    ) -> None:
        self._max_events = max_events
        self._history: deque[EventEnvelope] = deque(maxlen=max_events)
        self._layout = EventsLayoutService(settings).layout()

    def append(self, event: EventEnvelope) -> None:
        self._history.append(event)
        self._persist_optional(event)

    def recent(self, limit: int) -> list[EventEnvelope]:
        if limit <= 0:
            return []
        items = list(self._history)
        return items[-limit:]

    def clear(self) -> None:
        self._history.clear()

    def __len__(self) -> int:
        return len(self._history)

    def _persist_optional(self, event: EventEnvelope) -> None:
        try:
            self._layout.ensure_tree()
            line = json.dumps(event.to_dict(), ensure_ascii=False) + "\n"
            with self._layout.latest_path.open("a", encoding="utf-8") as handle:
                handle.write(line)
        except OSError as exc:
            logger.debug("event history write skipped: %s", exc)
