"""E4.1 safe event publishing — never break callers."""

from __future__ import annotations

import logging

from app.contracts.events import EventEnvelope
from app.events.bus import EventBus

logger = logging.getLogger(__name__)


def safe_publish(event_bus: EventBus | None, event: EventEnvelope) -> None:
    if event_bus is None:
        return
    try:
        event_bus.publish(event)
    except Exception:
        logger.exception(
            "event publish failed: type=%s event_id=%s",
            event.event_type,
            event.event_id,
        )
