"""E4.1 — Queue & Recovery Event Bus integration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from app.config.settings import AppSettings
from app.contracts.events import (
    EVENT_QUEUE_JOB_CANCELLED,
    EVENT_QUEUE_JOB_COMPLETED,
    EVENT_QUEUE_JOB_FAILED,
    EVENT_QUEUE_JOB_QUEUED,
    EVENT_QUEUE_JOB_STARTED,
    EVENT_QUEUE_SNAPSHOT_UPDATED,
    EVENT_RECOVERY_INTERRUPTED_DETECTED,
    EVENT_RECOVERY_RESTART_PLAN_CREATED,
    EVENT_RECOVERY_RESUME_PLAN_CREATED,
    EventEnvelope,
)
from app.contracts.states import STATE_VC_PROCESSING
from app.events.bus import EventBus
from app.queue.manager import QueueManager
from app.queue.store import QueueStore
from app.recovery.recovery_service import RecoveryService
from app.storage.project_store import ProjectStore


@pytest.fixture
def project_store(tmp_path: Path) -> ProjectStore:
    return ProjectStore(settings=AppSettings(projects_root=tmp_path / "projects"))


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def queue(
    tmp_path: Path,
    project_store: ProjectStore,
    event_bus: EventBus,
) -> QueueManager:
    settings = AppSettings(
        projects_root=tmp_path / "projects",
        queue_root=tmp_path / "queue",
    )
    return QueueManager(
        store=QueueStore(settings),
        project_store=project_store,
        event_bus=event_bus,
    )


@pytest.fixture
def recovery(
    project_store: ProjectStore,
    event_bus: EventBus,
) -> RecoveryService:
    return RecoveryService(store=project_store, event_bus=event_bus)


def _collect(bus: EventBus, event_type: str) -> list[EventEnvelope]:
    received: list[EventEnvelope] = []
    bus.subscribe(event_type, received.append)
    return received


def _setup_part(store: ProjectStore) -> tuple[str, str]:
    store.create_project("book-1")
    store.create_part("book-1", part_id="part-001")
    store.create_chunk("book-1", "part-001", 17)
    return "book-1", "part-001"


def test_queue_job_queued(
    queue: QueueManager,
    event_bus: EventBus,
    project_store: ProjectStore,
) -> None:
    _setup_part(project_store)
    received = _collect(event_bus, EVENT_QUEUE_JOB_QUEUED)
    item = queue.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="vc",
        chunk_id=17,
    )
    assert len(received) == 1
    assert received[0].event_type == EVENT_QUEUE_JOB_QUEUED
    assert received[0].chunk_id == 17
    assert received[0].payload == {"job_id": item.job_id, "job_type": "vc"}


def test_queue_job_started(
    queue: QueueManager,
    event_bus: EventBus,
    project_store: ProjectStore,
) -> None:
    _setup_part(project_store)
    received = _collect(event_bus, EVENT_QUEUE_JOB_STARTED)
    item = queue.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="vc",
        chunk_id=17,
    )
    job = queue.dequeue()
    queue.mark_running(job)
    assert len(received) == 1
    assert received[0].payload == {"job_id": item.job_id, "job_type": "vc"}


def test_queue_job_completed(
    queue: QueueManager,
    event_bus: EventBus,
    project_store: ProjectStore,
) -> None:
    _setup_part(project_store)
    received = _collect(event_bus, EVENT_QUEUE_JOB_COMPLETED)
    item = queue.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="vc",
        chunk_id=17,
    )
    job = queue.dequeue()
    queue.mark_running(job)
    queue.mark_completed(item.job_id)
    assert len(received) == 1
    assert received[0].payload["job_id"] == item.job_id


def test_queue_job_failed(
    queue: QueueManager,
    event_bus: EventBus,
    project_store: ProjectStore,
) -> None:
    _setup_part(project_store)
    received = _collect(event_bus, EVENT_QUEUE_JOB_FAILED)
    item = queue.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="vc",
        chunk_id=17,
    )
    job = queue.dequeue()
    queue.mark_running(job)
    queue.mark_failed(item.job_id, "vc error")
    assert len(received) == 1
    assert received[0].payload["error"] == "vc error"


def test_queue_job_cancelled(
    queue: QueueManager,
    event_bus: EventBus,
    project_store: ProjectStore,
) -> None:
    _setup_part(project_store)
    received = _collect(event_bus, EVENT_QUEUE_JOB_CANCELLED)
    item = queue.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="vc",
        chunk_id=17,
    )
    queue.cancel(item.job_id)
    assert len(received) == 1
    assert received[0].payload["job_type"] == "vc"


def test_queue_snapshot_updated(
    queue: QueueManager,
    event_bus: EventBus,
    project_store: ProjectStore,
) -> None:
    _setup_part(project_store)
    received = _collect(event_bus, EVENT_QUEUE_SNAPSHOT_UPDATED)
    queue.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="narration",
        chunk_id=17,
    )
    assert len(received) >= 1
    payload = received[-1].payload
    assert payload == {
        "queued": 1,
        "running": 0,
        "completed": 0,
        "failed": 0,
        "cancelled": 0,
    }


def test_recovery_interrupted_detected(
    recovery: RecoveryService,
    project_store: ProjectStore,
    event_bus: EventBus,
) -> None:
    _setup_part(project_store)
    chunk = project_store.load_chunk("book-1", "part-001", 17)
    chunk.state = STATE_VC_PROCESSING
    project_store.save_chunk("book-1", "part-001", chunk)

    received = _collect(event_bus, EVENT_RECOVERY_INTERRUPTED_DETECTED)
    recovery.scan_part("book-1", "part-001")
    assert len(received) == 1
    assert received[0].chunk_id == 17
    assert received[0].payload == {"chunk_id": 17, "state": STATE_VC_PROCESSING}


def test_recovery_resume_plan_created(
    recovery: RecoveryService,
    project_store: ProjectStore,
    event_bus: EventBus,
) -> None:
    _setup_part(project_store)
    project_store.create_chunk("book-1", "part-001", 18)
    for cid in (17, 18):
        chunk = project_store.load_chunk("book-1", "part-001", cid)
        chunk.state = "Interrupted"
        project_store.save_chunk("book-1", "part-001", chunk)

    received = _collect(event_bus, EVENT_RECOVERY_RESUME_PLAN_CREATED)
    plan = recovery.create_resume_plan("book-1", "part-001")
    assert len(received) == 1
    assert received[0].payload["start_chunk"] == plan.start_chunk
    assert received[0].payload["remaining_chunks"] == plan.remaining_chunks


def test_recovery_restart_plan_created(
    recovery: RecoveryService,
    project_store: ProjectStore,
    event_bus: EventBus,
) -> None:
    _setup_part(project_store)
    project_store.create_chunk("book-1", "part-001", 18)
    received = _collect(event_bus, EVENT_RECOVERY_RESTART_PLAN_CREATED)
    plan = recovery.create_restart_plan("book-1", "part-001")
    assert len(received) == 1
    assert received[0].payload["chunks"] == plan.chunks


def test_event_bus_failure_isolation(
    queue: QueueManager,
    project_store: ProjectStore,
    event_bus: EventBus,
) -> None:
    _setup_part(project_store)

    def boom(_: EventEnvelope) -> None:
        raise RuntimeError("subscriber down")

    event_bus.subscribe(EVENT_QUEUE_JOB_QUEUED, boom)

    with patch.object(event_bus, "publish", side_effect=RuntimeError("bus broken")):
        item = queue.enqueue(
            project_id="book-1",
            part_id="part-001",
            job_type="vc",
            chunk_id=17,
        )

    assert item.job_id
    assert queue.peek() is not None
    assert queue.peek().job_id == item.job_id


def test_no_event_bus_unchanged_behavior(
    tmp_path: Path,
    project_store: ProjectStore,
) -> None:
    _setup_part(project_store)
    settings = AppSettings(
        projects_root=tmp_path / "projects",
        queue_root=tmp_path / "queue",
    )
    mgr = QueueManager(
        store=QueueStore(settings),
        project_store=project_store,
        event_bus=None,
    )
    item = mgr.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="vc",
        chunk_id=17,
    )
    assert item.status == "queued"
    assert mgr.snapshot().queued == 1
