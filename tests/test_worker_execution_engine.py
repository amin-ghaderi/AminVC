"""E6.0 — Worker execution engine."""

from __future__ import annotations

import wave
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.config.settings import AppSettings
from app.contracts.events import (
    EVENT_VC_CHUNK_STARTED,
    EVENT_VC_PROGRESS,
    EVENT_WORKER_JOB_COMPLETED,
    EVENT_WORKER_JOB_FAILED,
    EVENT_WORKER_JOB_STARTED,
    EventEnvelope,
)
from app.contracts.queue import QueueItem
from app.contracts.states import (
    STATE_NARRATION_QUEUED,
    STATE_NARRATION_READY,
    STATE_VC_QUEUED,
    STATE_VC_READY,
)
from app.events.bus import EventBus
from app.queue.manager import QueueManager
from app.queue.store import QueueStore
from app.recovery.recovery_service import RecoveryService
from app.services.build_service import BuildService
from app.services.narration_chunk_executor import WaveNarrationChunkExecutor
from app.storage.project_store import ProjectStore
from app.worker.execution_engine import WorkerExecutionEngine
from app.worker.job_runner import JobExecutionError, JobRunner
from app.worker.state import WorkerState


@pytest.fixture
def project_store(tmp_path: Path) -> ProjectStore:
    return ProjectStore(settings=AppSettings(projects_root=tmp_path / "projects"))


@pytest.fixture
def queue_store(tmp_path: Path) -> QueueStore:
    return QueueStore(settings=AppSettings(queue_root=tmp_path / "queue"))


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def queue(
    queue_store: QueueStore,
    project_store: ProjectStore,
    event_bus: EventBus,
) -> QueueManager:
    return QueueManager(
        store=queue_store,
        project_store=project_store,
        event_bus=event_bus,
    )


def _write_wav(path: Path, *, duration_frames: int = 2400) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(24000)
        handle.writeframes(b"\x00\x00" * duration_frames)


def _setup_part(store: ProjectStore, *, with_reference: bool = True) -> tuple[str, str]:
    store.create_project("book-1")
    store.create_part("book-1", part_id="part-001")
    if with_reference:
        ref = store.part_layout("book-1", "part-001").root / "reference.wav"
        _write_wav(ref)
        part = store.load_part("book-1", "part-001")
        part.processing_profile = "reference.wav"
        store.save_part(part)
    return "book-1", "part-001"


def _collect(bus: EventBus, *types: str) -> list[EventEnvelope]:
    received: list[EventEnvelope] = []
    for event_type in types:
        bus.subscribe(event_type, received.append)
    return received


def test_empty_queue_polling(
    queue: QueueManager,
    project_store: ProjectStore,
    event_bus: EventBus,
) -> None:
    engine = WorkerExecutionEngine(
        queue=queue,
        project_store=project_store,
        event_bus=event_bus,
        poll_interval=0.01,
    )
    engine.startup()
    assert engine.run_once() is False
    assert engine.state == WorkerState.IDLE


def test_narration_job_execution(
    queue: QueueManager,
    project_store: ProjectStore,
    event_bus: EventBus,
) -> None:
    pid, part = _setup_part(project_store, with_reference=False)
    project_store.create_chunk(pid, part, 1, text="Hello")
    chunk = project_store.load_chunk(pid, part, 1)
    chunk.state = STATE_NARRATION_QUEUED
    project_store.save_chunk(pid, part, chunk)

    engine = WorkerExecutionEngine(
        queue=queue,
        project_store=project_store,
        event_bus=event_bus,
        narration=WaveNarrationChunkExecutor(),
    )
    engine.startup()
    queue.enqueue(project_id=pid, part_id=part, job_type="narration", chunk_id=1)
    assert engine.run_once() is True

    updated = project_store.load_chunk(pid, part, 1)
    assert updated.state == STATE_NARRATION_READY
    narr = project_store.part_layout(pid, part).narration_wav_path(1)
    assert narr.is_file()


def test_vc_job_execution(
    queue: QueueManager,
    project_store: ProjectStore,
    event_bus: EventBus,
) -> None:
    pid, part = _setup_part(project_store)
    project_store.create_chunk(pid, part, 1)
    chunk = project_store.load_chunk(pid, part, 1)
    chunk.state = STATE_VC_QUEUED
    project_store.save_chunk(pid, part, chunk)
    _write_wav(project_store.part_layout(pid, part).narration_wav_path(1))

    speaker = MagicMock()
    speaker.convert_chunk = MagicMock(return_value=Path("out.wav"))

    engine = WorkerExecutionEngine(
        queue=queue,
        project_store=project_store,
        event_bus=event_bus,
        speaker=speaker,
    )
    engine.startup()
    queue.enqueue(project_id=pid, part_id=part, job_type="vc", chunk_id=1)
    engine.run_once()

    speaker.convert_chunk.assert_called_once()
    kwargs = speaker.convert_chunk.call_args.kwargs
    assert kwargs["event_bus"] is event_bus
    assert kwargs["chunk_id"] == 1
    assert project_store.load_chunk(pid, part, 1).state == STATE_VC_READY


def test_build_job_execution(
    queue: QueueManager,
    project_store: ProjectStore,
    event_bus: EventBus,
) -> None:
    pid, part = _setup_part(project_store, with_reference=False)
    pl = project_store.part_layout(pid, part)
    for cid in (1, 2):
        project_store.create_chunk(pid, part, cid)
        _write_wav(pl.vc_wav_path(cid))
    build = project_store.create_build(pid, part, name="full", chunks=[1, 2], build_id="build-001")

    engine = WorkerExecutionEngine(
        queue=queue,
        project_store=project_store,
        event_bus=event_bus,
    )
    engine.startup()
    queue.enqueue(
        project_id=pid,
        part_id=part,
        job_type="build",
        chunk_id=None,
        job_id=build.build_id,
    )
    engine.run_once()

    out = pl.build_output_path(build.build_id)
    assert out.is_file()


def test_unknown_job_type_fails(project_store: ProjectStore) -> None:
    pid, part = _setup_part(project_store, with_reference=False)

    class UnknownJob:
        job_type = "unknown"
        job_id = "bad-1"
        project_id = pid
        part_id = part
        chunk_id = 1

    runner = JobRunner(
        project_store,
        WaveNarrationChunkExecutor(),
        MagicMock(),
        BuildService(project_store),
    )
    with pytest.raises(JobExecutionError):
        runner.execute(UnknownJob())  # type: ignore[arg-type]


def test_job_failure_handling(
    queue: QueueManager,
    project_store: ProjectStore,
    event_bus: EventBus,
) -> None:
    pid, part = _setup_part(project_store, with_reference=False)
    project_store.create_chunk(pid, part, 1)
    chunk = project_store.load_chunk(pid, part, 1)
    chunk.state = STATE_NARRATION_QUEUED
    project_store.save_chunk(pid, part, chunk)

    narration = MagicMock()
    narration.generate_chunk = MagicMock(side_effect=RuntimeError("narration boom"))

    engine = WorkerExecutionEngine(
        queue=queue,
        project_store=project_store,
        event_bus=event_bus,
        narration=narration,
    )
    engine.startup()
    queue.enqueue(project_id=pid, part_id=part, job_type="narration", chunk_id=1)
    engine.run_once()

    _, failed, _ = queue._store.load_history()
    assert len(failed) == 1
    assert "narration boom" in (failed[0].last_error or "")


def test_queue_completion_integration(
    queue: QueueManager,
    project_store: ProjectStore,
    event_bus: EventBus,
) -> None:
    pid, part = _setup_part(project_store, with_reference=False)
    project_store.create_chunk(pid, part, 1, text="x")
    chunk = project_store.load_chunk(pid, part, 1)
    chunk.state = STATE_NARRATION_QUEUED
    project_store.save_chunk(pid, part, chunk)

    engine = WorkerExecutionEngine(
        queue=queue,
        project_store=project_store,
        event_bus=event_bus,
        narration=WaveNarrationChunkExecutor(),
    )
    engine.startup()
    job = queue.enqueue(project_id=pid, part_id=part, job_type="narration", chunk_id=1)
    engine.run_once()
    completed, failed, _ = queue._store.load_history()
    assert len(completed) == 1
    assert completed[0].job_id == job.job_id
    assert len(failed) == 0


def test_queue_failure_integration(
    queue: QueueManager,
    project_store: ProjectStore,
    event_bus: EventBus,
) -> None:
    pid, part = _setup_part(project_store)
    project_store.create_chunk(pid, part, 1)
    chunk = project_store.load_chunk(pid, part, 1)
    chunk.state = STATE_VC_QUEUED
    project_store.save_chunk(pid, part, chunk)

    speaker = MagicMock()
    speaker.convert_chunk = MagicMock(side_effect=RuntimeError("vc fail"))
    engine = WorkerExecutionEngine(
        queue=queue,
        project_store=project_store,
        event_bus=event_bus,
        speaker=speaker,
    )
    engine.startup()
    queue.enqueue(project_id=pid, part_id=part, job_type="vc", chunk_id=1)
    engine.run_once()
    _, failed, _ = queue._store.load_history()
    assert len(failed) == 1


def test_worker_start_stop_lifecycle(
    queue: QueueManager,
    project_store: ProjectStore,
    event_bus: EventBus,
) -> None:
    engine = WorkerExecutionEngine(
        queue=queue,
        project_store=project_store,
        event_bus=event_bus,
        poll_interval=0.01,
    )
    assert engine.is_running() is False
    engine.start()
    assert engine.is_running() is True
    assert engine.state in (WorkerState.IDLE, WorkerState.POLLING)
    engine.stop()
    assert engine.is_running() is False
    assert engine.state == WorkerState.STOPPED


def test_recovery_before_start_runs_scan(
    queue: QueueManager,
    project_store: ProjectStore,
    event_bus: EventBus,
) -> None:
    pid, part = _setup_part(project_store, with_reference=False)
    project_store.create_chunk(pid, part, 1)
    recovery = RecoveryService(store=project_store, event_bus=event_bus)
    engine = WorkerExecutionEngine(
        queue=queue,
        recovery=recovery,
        project_store=project_store,
        event_bus=event_bus,
    )
    with patch.object(recovery, "scan_project", wraps=recovery.scan_project) as spy:
        engine.startup()
        spy.assert_called_once_with(pid)


def test_state_validation_blocks_completed(
    project_store: ProjectStore,
) -> None:
    pid, part = _setup_part(project_store)
    project_store.create_chunk(pid, part, 1)
    chunk = project_store.load_chunk(pid, part, 1)
    chunk.state = STATE_VC_READY
    project_store.save_chunk(pid, part, chunk)

    runner = JobRunner(
        project_store,
        WaveNarrationChunkExecutor(),
        MagicMock(),
        BuildService(project_store),
    )
    job = QueueItem(
        job_id="j1",
        project_id=pid,
        part_id=part,
        chunk_id=1,
        job_type="vc",
    )
    with pytest.raises(JobExecutionError):
        runner.execute(job)


def test_worker_survives_bad_job(
    queue: QueueManager,
    project_store: ProjectStore,
    event_bus: EventBus,
) -> None:
    pid, part = _setup_part(project_store, with_reference=False)
    project_store.create_chunk(pid, part, 1)
    c1 = project_store.load_chunk(pid, part, 1)
    c1.state = STATE_NARRATION_QUEUED
    project_store.save_chunk(pid, part, c1)
    project_store.create_chunk(pid, part, 2, text="ok")
    c2 = project_store.load_chunk(pid, part, 2)
    c2.state = STATE_NARRATION_QUEUED
    project_store.save_chunk(pid, part, c2)

    call_count = 0

    class FlakyNarration(WaveNarrationChunkExecutor):
        def generate_chunk(self, **kwargs: Any) -> Path:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("first fails")
            return super().generate_chunk(**kwargs)

    engine = WorkerExecutionEngine(
        queue=queue,
        project_store=project_store,
        event_bus=event_bus,
        narration=FlakyNarration(),
    )
    engine.startup()
    queue.enqueue(project_id=pid, part_id=part, job_type="narration", chunk_id=1)
    queue.enqueue(project_id=pid, part_id=part, job_type="narration", chunk_id=2)
    engine.run_once()
    engine.run_once()
    assert project_store.load_chunk(pid, part, 2).state == STATE_NARRATION_READY


def test_vc_progress_path_kwarg(
    queue: QueueManager,
    project_store: ProjectStore,
    event_bus: EventBus,
) -> None:
    pid, part = _setup_part(project_store)
    project_store.create_chunk(pid, part, 1)
    chunk = project_store.load_chunk(pid, part, 1)
    chunk.state = STATE_VC_QUEUED
    project_store.save_chunk(pid, part, chunk)
    _write_wav(project_store.part_layout(pid, part).narration_wav_path(1))

    speaker = MagicMock()

    def fake_convert(*_args: Any, **kwargs: Any) -> Path:
        bus = kwargs["event_bus"]
        assert bus is event_bus
        from app.vc.progress_adapter import VcProgressAdapter

        adapter = VcProgressAdapter(
            project_id=kwargs["project_id"],
            part_id=kwargs["part_id"],
            event_bus=bus,
            total_steps=4,
        )
        adapter.start_chunk(kwargs["chunk_id"])
        adapter.update_step(1)
        adapter.complete_chunk()
        return project_store.part_layout(pid, part).vc_wav_path(1)

    speaker.convert_chunk = fake_convert

    received = _collect(event_bus, EVENT_VC_CHUNK_STARTED, EVENT_VC_PROGRESS)
    engine = WorkerExecutionEngine(
        queue=queue,
        project_store=project_store,
        event_bus=event_bus,
        speaker=speaker,
    )
    engine.startup()
    queue.enqueue(project_id=pid, part_id=part, job_type="vc", chunk_id=1)
    engine.run_once()
    assert any(e.event_type == EVENT_VC_PROGRESS for e in received)


def test_worker_events_published(
    queue: QueueManager,
    project_store: ProjectStore,
    event_bus: EventBus,
) -> None:
    pid, part = _setup_part(project_store, with_reference=False)
    project_store.create_chunk(pid, part, 1, text="hi")
    chunk = project_store.load_chunk(pid, part, 1)
    chunk.state = STATE_NARRATION_QUEUED
    project_store.save_chunk(pid, part, chunk)

    received = _collect(
        event_bus,
        EVENT_WORKER_JOB_STARTED,
        EVENT_WORKER_JOB_COMPLETED,
    )
    engine = WorkerExecutionEngine(
        queue=queue,
        project_store=project_store,
        event_bus=event_bus,
        narration=WaveNarrationChunkExecutor(),
    )
    engine.startup()
    queue.enqueue(project_id=pid, part_id=part, job_type="narration", chunk_id=1)
    engine.run_once()
    types = [e.event_type for e in received]
    assert EVENT_WORKER_JOB_STARTED in types
    assert EVENT_WORKER_JOB_COMPLETED in types


def test_diffusion_steps_from_settings(
    project_store: ProjectStore,
) -> None:
    pid, part = _setup_part(project_store)
    project_store.create_chunk(pid, part, 1)
    chunk = project_store.load_chunk(pid, part, 1)
    chunk.state = STATE_VC_QUEUED
    project_store.save_chunk(pid, part, chunk)
    _write_wav(project_store.part_layout(pid, part).narration_wav_path(1))

    speaker = MagicMock()
    out = project_store.part_layout(pid, part).vc_wav_path(1)

    def capture(*_args: Any, **_kwargs: Any) -> Path:
        _write_wav(out)
        return out

    speaker.convert_chunk.side_effect = capture
    job = QueueItem(
        job_id="j",
        project_id=pid,
        part_id=part,
        chunk_id=1,
        job_type="vc",
    )
    JobRunner(
        project_store,
        WaveNarrationChunkExecutor(),
        speaker,
        BuildService(project_store),
        event_bus=None,
    ).execute(job)
    assert speaker.convert_chunk.call_args.kwargs["settings"]["diffusion_steps"] == 30
