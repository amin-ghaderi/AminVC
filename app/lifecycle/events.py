"""E6.2 lifecycle Event Bus publishing."""

from __future__ import annotations

from app.contracts.events import (
    EVENT_NARRATION_APPROVED,
    EVENT_NARRATION_REBUILD_REQUESTED,
    EVENT_NARRATION_UNAPPROVED,
    EVENT_VC_APPROVED,
    EVENT_VC_REBUILD_REQUESTED,
    EVENT_VC_UNAPPROVED,
    create_event_envelope,
)
from app.events.bus import EventBus
from app.events.helpers import safe_publish


def publish_narration_approved(
    event_bus: EventBus | None,
    *,
    project_id: str,
    part_id: str,
    chunk_id: int,
) -> None:
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_NARRATION_APPROVED,
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk_id,
            payload={"chunk_id": chunk_id},
        ),
    )


def publish_narration_unapproved(
    event_bus: EventBus | None,
    *,
    project_id: str,
    part_id: str,
    chunk_id: int,
) -> None:
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_NARRATION_UNAPPROVED,
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk_id,
            payload={"chunk_id": chunk_id},
        ),
    )


def publish_vc_approved(
    event_bus: EventBus | None,
    *,
    project_id: str,
    part_id: str,
    chunk_id: int,
) -> None:
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_VC_APPROVED,
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk_id,
            payload={"chunk_id": chunk_id},
        ),
    )


def publish_vc_unapproved(
    event_bus: EventBus | None,
    *,
    project_id: str,
    part_id: str,
    chunk_id: int,
) -> None:
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_VC_UNAPPROVED,
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk_id,
            payload={"chunk_id": chunk_id},
        ),
    )


def publish_narration_rebuild_requested(
    event_bus: EventBus | None,
    *,
    project_id: str,
    part_id: str,
    chunk_id: int,
) -> None:
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_NARRATION_REBUILD_REQUESTED,
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk_id,
            payload={"chunk_id": chunk_id},
        ),
    )


def publish_vc_rebuild_requested(
    event_bus: EventBus | None,
    *,
    project_id: str,
    part_id: str,
    chunk_id: int,
) -> None:
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_VC_REBUILD_REQUESTED,
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk_id,
            payload={"chunk_id": chunk_id},
        ),
    )
