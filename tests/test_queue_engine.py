"""E3.0 — Queue engine."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.config.settings import AppSettings
from app.contracts.queue import INTERRUPTED_EXECUTION_ERROR, QueueItem
from app.contracts.recovery import ResumePlan
from app.contracts.states import STATE_NARRATION_QUEUED, STATE_VC_QUEUED
from app.queue.manager import QueueError, QueueManager
from app.queue.store import QueueStore
from app.recovery.recovery_service import RecoveryService
from app.storage.json_io import read_json
from app.storage.project_store import ProjectStore


@pytest.fixture
def project_store(tmp_path: Path) -> ProjectStore:
    return ProjectStore(settings=AppSettings(projects_root=tmp_path / "projects"))


@pytest.fixture
def queue_store(tmp_path: Path) -> QueueStore:
    return QueueStore(settings=AppSettings(queue_root=tmp_path / "queue"))


@pytest.fixture
def queue(
    queue_store: QueueStore,
    project_store: ProjectStore,
) -> QueueManager:
    return QueueManager(store=queue_store, project_store=project_store)


def _setup_part(store: ProjectStore) -> tuple[str, str]:
    store.create_project("book-1")
    store.create_part("book-1", part_id="part-001")
    store.create_chunk("book-1", "part-001", 31)
    store.create_chunk("book-1", "part-001", 32)
    store.create_chunk("book-1", "part-001", 33)
    return "book-1", "part-001"


def test_queue_item_persistence(queue: QueueManager, queue_store: QueueStore) -> None:
    _setup_part(queue._project_store)  # noqa: SLF001
    item = queue.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="vc",
        chunk_id=31,
    )
    data = read_json(queue_store.layout.queue_path)
    assert data is not None
    assert len(data["items"]) == 1
    assert data["items"][0]["job_id"] == item.job_id
    assert data["items"][0]["status"] == "queued"
    assert data["items"][0]["attempts"] == 0


def test_fifo_ordering(queue: QueueManager) -> None:
    _setup_part(queue._project_store)  # noqa: SLF001
    a = queue.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="narration",
        chunk_id=31,
    )
    b = queue.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="narration",
        chunk_id=32,
    )
    c = queue.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="narration",
        chunk_id=33,
    )
    assert queue.peek() is not None and queue.peek().job_id == a.job_id
    assert queue.dequeue().job_id == a.job_id
    assert queue.dequeue().job_id == b.job_id
    assert queue.dequeue().job_id == c.job_id
    assert queue.dequeue() is None


def test_queue_restore_empty(queue: QueueManager) -> None:
    snap = queue.restore()
    assert snap.queued == 0
    assert snap.running == 0


def test_running_job_recovery_on_restore(
    queue: QueueManager,
    queue_store: QueueStore,
) -> None:
    _setup_part(queue._project_store)  # noqa: SLF001
    item = queue.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="vc",
        chunk_id=31,
    )
    running_item = QueueItem(
        job_id=item.job_id,
        project_id=item.project_id,
        part_id=item.part_id,
        chunk_id=item.chunk_id,
        job_type=item.job_type,
        status="running",
        created_at=item.created_at,
        started_at="2026-01-01T00:00:00+00:00",
    )
    queue_store.save_running(running_item)

    snap = queue.restore()
    assert snap.running == 0
    assert snap.failed == 1
    assert queue_store.load_running() is None
    _, failed, _ = queue_store.load_history()
    assert len(failed) == 1
    assert failed[0].status == "failed"
    assert failed[0].last_error == INTERRUPTED_EXECUTION_ERROR


def test_snapshot_generation(queue: QueueManager) -> None:
    _setup_part(queue._project_store)  # noqa: SLF001
    queue.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="narration",
        chunk_id=31,
    )
    queue.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="narration",
        chunk_id=32,
    )
    snap = queue.snapshot()
    assert snap.queued == 2
    assert snap.running == 0
    assert snap.completed == 0
    assert snap.failed == 0

    job = queue.dequeue()
    queue.mark_running(job)
    snap2 = queue.snapshot()
    assert snap2.queued == 1
    assert snap2.running == 1

    queue.mark_completed(job.job_id)
    snap3 = queue.snapshot()
    assert snap3.running == 0
    assert snap3.completed == 1


def test_queue_cancellation(queue: QueueManager, queue_store: QueueStore) -> None:
    _setup_part(queue._project_store)  # noqa: SLF001
    a = queue.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="vc",
        chunk_id=31,
    )
    queue.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="vc",
        chunk_id=32,
    )
    cancelled = queue.cancel(a.job_id)
    assert cancelled.status == "cancelled"
    assert queue.peek() is not None
    assert queue.peek().chunk_id == 32
    snap = queue.snapshot()
    assert snap.queued == 1
    assert snap.cancelled == 1
    _, _, hist_cancelled = queue_store.load_history()
    assert len(hist_cancelled) == 1
    assert hist_cancelled[0].job_id == a.job_id


def test_history_persistence(queue: QueueManager, queue_store: QueueStore) -> None:
    _setup_part(queue._project_store)  # noqa: SLF001
    job = queue.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="narration",
        chunk_id=31,
    )
    dequeued = queue.dequeue()
    queue.mark_running(dequeued)
    queue.mark_failed(job.job_id, "boom")

    completed, failed, cancelled = queue_store.load_history()
    assert len(completed) == 0
    assert len(failed) == 1
    assert len(cancelled) == 0
    assert failed[0].last_error == "boom"
    assert failed[0].status == "failed"

    job2 = queue.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="narration",
        chunk_id=32,
    )
    d2 = queue.dequeue()
    queue.mark_running(d2)
    queue.mark_completed(job2.job_id)

    completed2, failed2, cancelled2 = queue_store.load_history()
    assert len(completed2) == 1
    assert len(failed2) == 1
    assert len(cancelled2) == 0
    assert completed2[0].status == "completed"

    hist = read_json(queue_store.layout.history_path)
    assert "completed" in hist and "failed" in hist and "cancelled" in hist
    assert len(hist["completed"]) == 1
    assert len(hist["failed"]) == 1
    assert len(hist["cancelled"]) == 0


def test_resume_plan_enqueue_integration(
    queue: QueueManager,
    project_store: ProjectStore,
) -> None:
    _setup_part(project_store)
    recovery = RecoveryService(store=project_store)
    for cid in (31, 32, 33):
        chunk = project_store.load_chunk("book-1", "part-001", cid)
        chunk.state = "Interrupted"
        project_store.save_chunk("book-1", "part-001", chunk)

    plan = recovery.create_resume_plan("book-1", "part-001")
    assert plan.remaining_chunks == [31, 32, 33]

    items = queue.enqueue_resume_plan(plan, job_type="vc")
    assert len(items) == 3
    assert [i.chunk_id for i in items] == [31, 32, 33]
    assert all(i.job_type == "vc" for i in items)

    peek = queue.peek()
    assert peek is not None and peek.chunk_id == 31

    for cid in (31, 32, 33):
        chunk = project_store.load_chunk("book-1", "part-001", cid)
        assert chunk.state == STATE_VC_QUEUED


def test_queue_restart_after_process_restart(
    tmp_path: Path,
    project_store: ProjectStore,
) -> None:
    _setup_part(project_store)
    settings = AppSettings(
        projects_root=tmp_path / "projects",
        queue_root=tmp_path / "queue",
    )
    store_a = QueueStore(settings)
    mgr_a = QueueManager(store=store_a, project_store=project_store)
    mgr_a.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="narration",
        chunk_id=31,
    )
    mgr_a.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="narration",
        chunk_id=32,
    )

    store_b = QueueStore(settings)
    mgr_b = QueueManager(store=store_b, project_store=project_store)
    mgr_b.restore()
    assert mgr_b.peek() is not None
    assert mgr_b.peek().chunk_id == 31
    first = mgr_b.dequeue()
    second = mgr_b.dequeue()
    assert first.chunk_id == 31
    assert second.chunk_id == 32
    assert mgr_b.dequeue() is None


def test_build_job_chunk_id_null(queue: QueueManager) -> None:
    _setup_part(queue._project_store)  # noqa: SLF001
    item = queue.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="build",
        chunk_id=None,
    )
    assert item.chunk_id is None

    with pytest.raises(QueueError):
        queue.enqueue(
            project_id="book-1",
            part_id="part-001",
            job_type="build",
            chunk_id=31,
        )


def test_narration_queued_manifest_state(
    queue: QueueManager,
    project_store: ProjectStore,
) -> None:
    _setup_part(project_store)
    queue.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="narration",
        chunk_id=31,
    )
    chunk = project_store.load_chunk("book-1", "part-001", 31)
    assert chunk.state == STATE_NARRATION_QUEUED


def test_checkpoints_directory_exists(queue_store: QueueStore) -> None:
    queue_store.ensure_tree()
    assert queue_store.layout.checkpoints_dir.is_dir()


def test_mark_failed_requires_running(queue: QueueManager) -> None:
    with pytest.raises(QueueError):
        queue.mark_failed("missing", "err")


def test_resume_plan_narration_enqueue(
    queue: QueueManager,
    project_store: ProjectStore,
) -> None:
    _setup_part(project_store)
    plan = ResumePlan(
        project_id="book-1",
        part_id="part-001",
        start_chunk=31,
        remaining_chunks=[31, 32, 33],
    )
    items = queue.enqueue_resume_plan(plan, job_type="narration")
    assert len(items) == 3
    chunk = project_store.load_chunk("book-1", "part-001", 31)
    assert chunk.state == STATE_NARRATION_QUEUED


def test_cancelled_job_persistence(
    queue: QueueManager,
    queue_store: QueueStore,
) -> None:
    _setup_part(queue._project_store)  # noqa: SLF001
    item = queue.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="vc",
        chunk_id=31,
    )
    queue.cancel(item.job_id)

    hist = read_json(queue_store.layout.history_path)
    assert hist is not None
    assert len(hist["cancelled"]) == 1
    assert hist["cancelled"][0]["job_id"] == item.job_id
    assert hist["cancelled"][0]["status"] == "cancelled"


def test_restore_after_restart_preserves_cancelled_count(
    tmp_path: Path,
    project_store: ProjectStore,
) -> None:
    _setup_part(project_store)
    settings = AppSettings(
        projects_root=tmp_path / "projects",
        queue_root=tmp_path / "queue",
    )
    mgr_a = QueueManager(
        store=QueueStore(settings),
        project_store=project_store,
    )
    job = mgr_a.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="narration",
        chunk_id=31,
    )
    mgr_a.cancel(job.job_id)

    mgr_b = QueueManager(
        store=QueueStore(settings),
        project_store=project_store,
    )
    snap = mgr_b.restore()
    assert snap.cancelled == 1


def test_snapshot_includes_persisted_cancelled_jobs(
    queue: QueueManager,
    queue_store: QueueStore,
) -> None:
    _setup_part(queue._project_store)  # noqa: SLF001
    for cid in (31, 32):
        job = queue.enqueue(
            project_id="book-1",
            part_id="part-001",
            job_type="narration",
            chunk_id=cid,
        )
        queue.cancel(job.job_id)

    snap = queue.snapshot()
    assert snap.cancelled == 2
    _, _, cancelled = queue_store.load_history()
    assert len(cancelled) == 2


def test_backward_compatibility_old_history_format(
    tmp_path: Path,
    project_store: ProjectStore,
) -> None:
    settings = AppSettings(
        projects_root=tmp_path / "projects",
        queue_root=tmp_path / "queue",
    )
    store = QueueStore(settings)
    store.ensure_tree()
    store.layout.history_path.write_text(
        json.dumps({"completed": [], "failed": []}),
        encoding="utf-8",
    )

    completed, failed, cancelled = store.load_history()
    assert completed == []
    assert failed == []
    assert cancelled == []

    mgr = QueueManager(store=store, project_store=project_store)
    snap = mgr.restore()
    assert snap.cancelled == 0
    assert snap.completed == 0
    assert snap.failed == 0


def test_multiple_cancelled_jobs(
    queue: QueueManager,
    queue_store: QueueStore,
) -> None:
    _setup_part(queue._project_store)  # noqa: SLF001
    ids: list[str] = []
    for cid in (31, 32, 33):
        item = queue.enqueue(
            project_id="book-1",
            part_id="part-001",
            job_type="vc",
            chunk_id=cid,
        )
        ids.append(item.job_id)
        queue.cancel(item.job_id)

    _, _, cancelled = queue_store.load_history()
    assert len(cancelled) == 3
    assert {c.job_id for c in cancelled} == set(ids)
    assert queue.snapshot().cancelled == 3
