"""E6.0 worker Event Bus publishing."""

from __future__ import annotations

from app.contracts.events import (
    EVENT_WORKER_JOB_COMPLETED,
    EVENT_WORKER_JOB_FAILED,
    EVENT_WORKER_JOB_STARTED,
    EVENT_WORKER_STARTED,
    EVENT_WORKER_STOPPED,
    create_event_envelope,
)
from app.contracts.queue import QueueItem
from app.events.bus import EventBus
from app.events.helpers import safe_publish


def publish_worker_started(event_bus: EventBus | None) -> None:
    safe_publish(event_bus, create_event_envelope(EVENT_WORKER_STARTED))


def publish_worker_stopped(event_bus: EventBus | None) -> None:
    safe_publish(event_bus, create_event_envelope(EVENT_WORKER_STOPPED))


def publish_worker_job_started(event_bus: EventBus | None, job: QueueItem) -> None:
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_WORKER_JOB_STARTED,
            project_id=job.project_id,
            part_id=job.part_id,
            chunk_id=job.chunk_id,
            payload={"job_id": job.job_id, "job_type": job.job_type},
        ),
    )


def publish_worker_job_completed(event_bus: EventBus | None, job: QueueItem) -> None:
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_WORKER_JOB_COMPLETED,
            project_id=job.project_id,
            part_id=job.part_id,
            chunk_id=job.chunk_id,
            payload={"job_id": job.job_id, "job_type": job.job_type},
        ),
    )


def publish_worker_job_failed(
    event_bus: EventBus | None,
    job: QueueItem,
    error: str,
) -> None:
    safe_publish(
        event_bus,
        create_event_envelope(
            EVENT_WORKER_JOB_FAILED,
            project_id=job.project_id,
            part_id=job.part_id,
            chunk_id=job.chunk_id,
            payload={"job_id": job.job_id, "job_type": job.job_type, "error": error},
        ),
    )
