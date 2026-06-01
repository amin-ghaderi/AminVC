"""E6.1 narration chunk Event Bus publishing."""

from __future__ import annotations

from app.contracts.events import (
    EVENT_NARRATION_CHUNK_COMPLETED,
    EVENT_NARRATION_CHUNK_FAILED,
    EVENT_NARRATION_CHUNK_STARTED,
    ChunkDurationPayload,
    create_event_envelope,
)
from app.events.bus import EventBus
from app.events.helpers import safe_publish


def publish_chunk_started(
    event_bus: EventBus | None,
    *,
    project_id: str,
    part_id: str,
    chunk_id: int,
) -> None:
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_NARRATION_CHUNK_STARTED,
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk_id,
            payload={"chunk_id": chunk_id},
        ),
    )


def publish_chunk_completed(
    event_bus: EventBus | None,
    *,
    project_id: str,
    part_id: str,
    chunk_id: int,
    duration_seconds: float,
) -> None:
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_NARRATION_CHUNK_COMPLETED,
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk_id,
            payload=ChunkDurationPayload(duration_seconds).to_dict(),
        ),
    )


def publish_chunk_failed(
    event_bus: EventBus | None,
    *,
    project_id: str,
    part_id: str,
    chunk_id: int,
    error: str,
) -> None:
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_NARRATION_CHUNK_FAILED,
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk_id,
            payload={"error": error},
        ),
    )
