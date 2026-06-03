"""E6.2 — Approval, rebuild, and lifecycle enforcement."""

from __future__ import annotations

import wave
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.narration.bridge import NarrationEngineStatus

from app.config.settings import AppSettings
from app.contracts.events import (
    EVENT_NARRATION_APPROVED,
    EVENT_NARRATION_REBUILD_REQUESTED,
    EVENT_NARRATION_UNAPPROVED,
    EVENT_VC_APPROVED,
    EVENT_VC_REBUILD_REQUESTED,
    EVENT_VC_UNAPPROVED,
    EventEnvelope,
)
from app.contracts.states import (
    STATE_INTERRUPTED,
    STATE_NARRATION_APPROVED,
    STATE_NARRATION_QUEUED,
    STATE_NARRATION_READY,
    STATE_VC_APPROVED,
    STATE_VC_QUEUED,
    STATE_VC_READY,
)
from app.events.bus import EventBus
from app.lifecycle import (
    ApprovalRequiredError,
    ApprovalService,
    InvalidStateTransitionError,
    LifecycleService,
    RebuildService,
)
from app.queue.manager import QueueManager
from app.queue.store import QueueStore
from app.recovery.recovery_service import RecoveryService
from app.services.build_service import BuildService
from app.services.narration_chunk_executor import WaveNarrationChunkExecutor
from app.storage.project_store import ProjectStore
from app.worker.execution_engine import WorkerExecutionEngine
from app.worker.job_runner import JobRunner


@pytest.fixture
def project_store(tmp_path: Path) -> ProjectStore:
    return ProjectStore(settings=AppSettings(projects_root=tmp_path / "projects"))


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def approval(project_store: ProjectStore, event_bus: EventBus) -> ApprovalService:
    return ApprovalService(project_store, event_bus=event_bus)


@pytest.fixture
def rebuild(project_store: ProjectStore, event_bus: EventBus) -> RebuildService:
    return RebuildService(project_store, event_bus=event_bus)


def _setup(project_store: ProjectStore) -> tuple[str, str, int]:
    project_store.create_project("book-1")
    project_store.create_part("book-1", part_id="part-001")
    project_store.create_chunk("book-1", "part-001", 1, text="original")
    return "book-1", "part-001", 1


def _collect(bus: EventBus, *types: str) -> list[EventEnvelope]:
    received: list[EventEnvelope] = []
    for event_type in types:
        bus.subscribe(event_type, received.append)
    return received


def _write_wav(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(24000)
        handle.writeframes(b"\x00\x01" * 1200)


def _ready_narration(store: ProjectStore, pid: str, part: str, cid: int) -> None:
    chunk = store.load_chunk(pid, part, cid)
    chunk.state = STATE_NARRATION_READY
    chunk.narration.file = f"narration/{cid:04d}.wav"
    store.save_chunk(pid, part, chunk)
    _write_wav(store.part_layout(pid, part).narration_wav_path(cid))


def _ready_vc(store: ProjectStore, pid: str, part: str, cid: int) -> None:
    chunk = store.load_chunk(pid, part, cid)
    chunk.state = STATE_VC_READY
    chunk.vc.file = f"vc/{cid:04d}.wav"
    store.save_chunk(pid, part, chunk)
    _write_wav(store.part_layout(pid, part).vc_wav_path(cid))


def test_narration_approval(
    project_store: ProjectStore,
    approval: ApprovalService,
) -> None:
    pid, part, cid = _setup(project_store)
    _ready_narration(project_store, pid, part, cid)

    updated = approval.approve_narration(pid, part, cid)
    assert updated.state == STATE_NARRATION_APPROVED
    assert updated.narration_approved is True
    persisted = project_store.load_chunk(pid, part, cid)
    assert persisted.narration_approved is True


def test_vc_approval(project_store: ProjectStore, approval: ApprovalService) -> None:
    pid, part, cid = _setup(project_store)
    _ready_vc(project_store, pid, part, cid)

    updated = approval.approve_vc(pid, part, cid)
    assert updated.state == STATE_VC_APPROVED
    assert updated.vc_approved is True


def test_narration_unapproval(
    project_store: ProjectStore,
    approval: ApprovalService,
) -> None:
    pid, part, cid = _setup(project_store)
    _ready_narration(project_store, pid, part, cid)
    approval.approve_narration(pid, part, cid)

    updated = approval.unapprove_narration(pid, part, cid)
    assert updated.state == STATE_NARRATION_READY
    assert updated.narration_approved is False


def test_vc_unapproval(project_store: ProjectStore, approval: ApprovalService) -> None:
    pid, part, cid = _setup(project_store)
    _ready_vc(project_store, pid, part, cid)
    approval.approve_vc(pid, part, cid)

    updated = approval.unapprove_vc(pid, part, cid)
    assert updated.state == STATE_VC_READY
    assert updated.vc_approved is False


def test_vc_blocked_without_narration_approval(
    project_store: ProjectStore,
    tmp_path: Path,
) -> None:
    pid, part, cid = _setup(project_store)
    _ready_narration(project_store, pid, part, cid)

    queue = QueueManager(
        store=QueueStore(settings=AppSettings(queue_root=tmp_path / "queue")),
        project_store=project_store,
    )
    with pytest.raises(ApprovalRequiredError):
        queue.enqueue(project_id=pid, part_id=part, job_type="vc", chunk_id=cid)


def test_narration_rebuild(project_store: ProjectStore, rebuild: RebuildService) -> None:
    pid, part, cid = _setup(project_store)
    _ready_narration(project_store, pid, part, cid)
    narr_path = project_store.part_layout(pid, part).narration_wav_path(cid)

    updated = rebuild.request_narration_rebuild(pid, part, cid)
    assert updated.state == STATE_NARRATION_QUEUED
    assert updated.narration_approved is False
    assert narr_path.is_file()


def test_vc_rebuild(project_store: ProjectStore, rebuild: RebuildService) -> None:
    pid, part, cid = _setup(project_store)
    _ready_vc(project_store, pid, part, cid)
    vc_path = project_store.part_layout(pid, part).vc_wav_path(cid)

    updated = rebuild.request_vc_rebuild(pid, part, cid)
    assert updated.state == STATE_VC_QUEUED
    assert updated.vc_approved is False
    assert vc_path.is_file()


def test_text_edit_invalidation(
    project_store: ProjectStore,
    rebuild: RebuildService,
) -> None:
    pid, part, cid = _setup(project_store)
    _ready_narration(project_store, pid, part, cid)
    approval = ApprovalService(project_store)
    approval.approve_narration(pid, part, cid)

    updated = rebuild.update_chunk_text(pid, part, cid, "edited transcript")
    assert updated.text == "edited transcript"
    assert updated.state == STATE_NARRATION_QUEUED
    assert updated.narration_approved is False
    assert updated.vc_approved is False


def test_approval_flag_persistence(
    project_store: ProjectStore,
    approval: ApprovalService,
) -> None:
    pid, part, cid = _setup(project_store)
    _ready_narration(project_store, pid, part, cid)
    approval.approve_narration(pid, part, cid)

    reloaded = project_store.load_chunk(pid, part, cid)
    assert reloaded.state == STATE_NARRATION_APPROVED
    assert reloaded.narration_approved is True


def test_event_emission(
    project_store: ProjectStore,
    event_bus: EventBus,
) -> None:
    pid, part, cid = _setup(project_store)
    _ready_narration(project_store, pid, part, cid)

    received = _collect(
        event_bus,
        EVENT_NARRATION_APPROVED,
        EVENT_NARRATION_UNAPPROVED,
        EVENT_NARRATION_REBUILD_REQUESTED,
        EVENT_VC_APPROVED,
        EVENT_VC_UNAPPROVED,
        EVENT_VC_REBUILD_REQUESTED,
    )
    approval = ApprovalService(project_store, event_bus=event_bus)
    rebuild = RebuildService(project_store, event_bus=event_bus)

    approval.approve_narration(pid, part, cid)
    approval.unapprove_narration(pid, part, cid)
    _ready_narration(project_store, pid, part, cid)
    approval.approve_narration(pid, part, cid)
    rebuild.request_narration_rebuild(pid, part, cid)

    _ready_vc(project_store, pid, part, cid)
    approval.approve_vc(pid, part, cid)
    approval.unapprove_vc(pid, part, cid)
    rebuild.request_vc_rebuild(pid, part, cid)

    types = {e.event_type for e in received}
    assert EVENT_NARRATION_APPROVED in types
    assert EVENT_NARRATION_UNAPPROVED in types
    assert EVENT_NARRATION_REBUILD_REQUESTED in types
    assert EVENT_VC_APPROVED in types
    assert EVENT_VC_UNAPPROVED in types
    assert EVENT_VC_REBUILD_REQUESTED in types


def test_worker_full_approval_workflow(
    project_store: ProjectStore,
    tmp_path: Path,
    event_bus: EventBus,
) -> None:
    pid, part, cid = _setup(project_store)
    pl = project_store.part_layout(pid, part)
    ref = pl.root / "reference.wav"
    _write_wav(ref)
    part_m = project_store.load_part(pid, part)
    part_m.processing_profile = "reference.wav"
    project_store.save_part(part_m)

    chunk = project_store.load_chunk(pid, part, cid)
    chunk.state = STATE_NARRATION_QUEUED
    chunk.text = "hello workflow"
    project_store.save_chunk(pid, part, chunk)

    queue = QueueManager(
        store=QueueStore(settings=AppSettings(queue_root=tmp_path / "queue")),
        project_store=project_store,
        event_bus=event_bus,
    )

    with patch(
        "app.narration.bridge.check_narration_engine_ready",
        return_value=NarrationEngineStatus(ready=True),
    ), patch(
        "app.narration.bridge.synthesize_chunk_text",
        side_effect=lambda _t, p: _write_wav(p),
    ):
        engine = WorkerExecutionEngine(
            queue=queue,
            project_store=project_store,
            event_bus=event_bus,
        )
        engine.startup()
        queue.enqueue(project_id=pid, part_id=part, job_type="narration", chunk_id=cid)
        assert engine.run_once() is True

    approval = ApprovalService(project_store)
    approval.approve_narration(pid, part, cid)

    speaker = MagicMock()
    speaker.convert_chunk = MagicMock(side_effect=lambda *_a, **_k: pl.vc_wav_path(cid))

    engine = WorkerExecutionEngine(
        queue=queue,
        project_store=project_store,
        event_bus=event_bus,
        speaker=speaker,
    )
    queue.enqueue(project_id=pid, part_id=part, job_type="vc", chunk_id=cid)
    engine.run_once()

    assert project_store.load_chunk(pid, part, cid).state == STATE_VC_READY
    approval.approve_vc(pid, part, cid)
    assert project_store.load_chunk(pid, part, cid).state == STATE_VC_APPROVED


def test_recovery_compatibility_with_approval(
    project_store: ProjectStore,
    tmp_path: Path,
) -> None:
    pid, part, cid = _setup(project_store)
    chunk = project_store.load_chunk(pid, part, cid)
    chunk.state = STATE_INTERRUPTED
    chunk.narration_approved = True
    project_store.save_chunk(pid, part, chunk)

    recovery = RecoveryService(store=project_store)
    plan = recovery.create_resume_plan(pid, part)
    assert cid in plan.remaining_chunks

    queue = QueueManager(
        store=QueueStore(settings=AppSettings(queue_root=tmp_path / "queue")),
        project_store=project_store,
    )
    items = queue.enqueue_resume_plan(plan, job_type="narration")
    assert len(items) == 1
    assert project_store.load_chunk(pid, part, cid).state == STATE_NARRATION_QUEUED

    chunk = project_store.load_chunk(pid, part, cid)
    chunk.state = STATE_INTERRUPTED
    chunk.narration_approved = True
    project_store.save_chunk(pid, part, chunk)
    _write_wav(project_store.part_layout(pid, part).narration_wav_path(cid))
    _write_wav(project_store.part_layout(pid, part).reference_wav_path())

    vc_items = queue.enqueue_resume_plan(
        recovery.create_resume_plan(pid, part),
        job_type="vc",
    )
    assert len(vc_items) == 1
    assert project_store.load_chunk(pid, part, cid).state == STATE_VC_QUEUED


def test_lifecycle_validation_helpers(project_store: ProjectStore) -> None:
    pid, part, cid = _setup(project_store)
    chunk = project_store.load_chunk(pid, part, cid)
    assert LifecycleService.can_approve_narration(chunk) is False

    _ready_narration(project_store, pid, part, cid)
    chunk = project_store.load_chunk(pid, part, cid)
    assert LifecycleService.can_approve_narration(chunk) is True
    assert LifecycleService.can_queue_vc(chunk) is False

    chunk.narration_approved = True
    chunk.state = STATE_NARRATION_APPROVED
    assert LifecycleService.can_queue_vc(chunk) is True


def test_invalid_approval_raises(project_store: ProjectStore) -> None:
    pid, part, cid = _setup(project_store)
    with pytest.raises(InvalidStateTransitionError):
        ApprovalService(project_store).approve_narration(pid, part, cid)


def test_job_runner_direct_vc_without_queue_unchanged(
    project_store: ProjectStore,
) -> None:
    """JobRunner still accepts VCQueued when invoked directly (enqueue enforces approval)."""
    pid, part, cid = _setup(project_store)
    pl = project_store.part_layout(pid, part)
    ref = pl.root / "reference.wav"
    _write_wav(ref)
    part_m = project_store.load_part(pid, part)
    part_m.processing_profile = "reference.wav"
    project_store.save_part(part_m)
    _ready_narration(project_store, pid, part, cid)
    chunk = project_store.load_chunk(pid, part, cid)
    chunk.state = STATE_VC_QUEUED
    project_store.save_chunk(pid, part, chunk)

    speaker = MagicMock()
    out = project_store.part_layout(pid, part).vc_wav_path(cid)
    speaker.convert_chunk = MagicMock(return_value=out)

    from app.contracts.queue import QueueItem

    JobRunner(
        project_store,
        WaveNarrationChunkExecutor(),
        speaker,
        BuildService(project_store),
    ).execute(
        QueueItem(
            job_id="j",
            project_id=pid,
            part_id=part,
            chunk_id=cid,
            job_type="vc",
        )
    )
    assert project_store.load_chunk(pid, part, cid).state == STATE_VC_READY
