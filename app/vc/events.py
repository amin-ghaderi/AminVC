"""E5.0 VC progress Event Bus publishing."""

from __future__ import annotations

from app.contracts.events import (
    EVENT_VC_CHUNK_COMPLETED,
    EVENT_VC_CHUNK_FAILED,
    EVENT_VC_CHUNK_STARTED,
    EVENT_VC_PROGRESS,
    ChunkDurationPayload,
    VcProgressPayload,
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
            EVENT_VC_CHUNK_STARTED,
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk_id,
            payload={"chunk_id": chunk_id},
        ),
    )


def publish_vc_progress(
    event_bus: EventBus | None,
    *,
    project_id: str,
    part_id: str,
    chunk_id: int,
    current_step: int,
    total_steps: int,
    elapsed_seconds: int,
    estimated_remaining_seconds: int,
    segment_index: int | None = None,
    segment_total: int | None = None,
) -> None:
    payload = VcProgressPayload(
        current_step=current_step,
        total_steps=total_steps,
        elapsed_seconds=float(elapsed_seconds),
        estimated_remaining_seconds=float(estimated_remaining_seconds),
        segment_index=segment_index,
        segment_total=segment_total,
    )
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_VC_PROGRESS,
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk_id,
            payload=payload.to_dict(),
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
            EVENT_VC_CHUNK_COMPLETED,
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
            EVENT_VC_CHUNK_FAILED,
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk_id,
            payload={"error": error},
        ),
    )
