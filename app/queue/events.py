"""E4.1 queue event publishing helpers."""

from __future__ import annotations

from app.contracts.events import (
    EVENT_QUEUE_JOB_CANCELLED,
    EVENT_QUEUE_JOB_COMPLETED,
    EVENT_QUEUE_JOB_FAILED,
    EVENT_QUEUE_JOB_QUEUED,
    EVENT_QUEUE_JOB_STARTED,
    EVENT_QUEUE_SNAPSHOT_UPDATED,
    QueueSnapshotPayload,
    create_event_envelope,
)
from app.contracts.queue import QueueItem, QueueSnapshot
from app.events.bus import EventBus
from app.events.helpers import safe_publish


def publish_job_queued(event_bus: EventBus | None, item: QueueItem) -> None:
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_QUEUE_JOB_QUEUED,
            project_id=item.project_id,
            part_id=item.part_id,
            chunk_id=item.chunk_id,
            payload={"job_id": item.job_id, "job_type": item.job_type},
        ),
    )


def publish_job_started(event_bus: EventBus | None, item: QueueItem) -> None:
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_QUEUE_JOB_STARTED,
            project_id=item.project_id,
            part_id=item.part_id,
            chunk_id=item.chunk_id,
            payload={"job_id": item.job_id, "job_type": item.job_type},
        ),
    )


def publish_job_completed(event_bus: EventBus | None, item: QueueItem) -> None:
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_QUEUE_JOB_COMPLETED,
            project_id=item.project_id,
            part_id=item.part_id,
            chunk_id=item.chunk_id,
            payload={"job_id": item.job_id, "job_type": item.job_type},
        ),
    )


def publish_job_failed(event_bus: EventBus | None, item: QueueItem, error: str) -> None:
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_QUEUE_JOB_FAILED,
            project_id=item.project_id,
            part_id=item.part_id,
            chunk_id=item.chunk_id,
            payload={
                "job_id": item.job_id,
                "job_type": item.job_type,
                "error": error,
            },
        ),
    )


def publish_job_cancelled(event_bus: EventBus | None, item: QueueItem) -> None:
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_QUEUE_JOB_CANCELLED,
            project_id=item.project_id,
            part_id=item.part_id,
            chunk_id=item.chunk_id,
            payload={"job_id": item.job_id, "job_type": item.job_type},
        ),
    )


def publish_snapshot_updated(event_bus: EventBus | None, snapshot: QueueSnapshot) -> None:
    payload = QueueSnapshotPayload(
        queued=snapshot.queued,
        running=snapshot.running,
        completed=snapshot.completed,
        failed=snapshot.failed,
        cancelled=snapshot.cancelled,
    )
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_QUEUE_SNAPSHOT_UPDATED,
            payload=payload.to_dict(),
        ),
    )
