"""E6.1 — Narration engine integration (Gemini executor + worker)."""

from __future__ import annotations

import struct
import wave
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.config.settings import AppSettings
from app.contracts.events import (
    EVENT_NARRATION_CHUNK_COMPLETED,
    EVENT_NARRATION_CHUNK_FAILED,
    EVENT_NARRATION_CHUNK_STARTED,
    EVENT_WORKER_JOB_COMPLETED,
)
from app.contracts.queue import QueueItem
from app.contracts.states import STATE_NARRATION_QUEUED, STATE_NARRATION_READY
from app.events.bus import EventBus
from app.narration.bridge import NarrationEngineStatus
from app.narration.exceptions import (
    NarrationChunkExecutionError,
    NarrationEngineUnavailableError,
)
from app.queue.manager import QueueManager
from app.queue.store import QueueStore
from app.services.build_service import BuildService
from app.services.narration_chunk_executor import (
    GeminiNarrationChunkExecutor,
    WaveNarrationChunkExecutor,
)
from app.storage.project_store import ProjectStore
from app.worker.execution_engine import WorkerExecutionEngine
from app.worker.job_runner import JobRunner
from tests.lifecycle_helpers import mark_narration_approved_for_vc


@pytest.fixture
def project_store(tmp_path: Path) -> ProjectStore:
    return ProjectStore(settings=AppSettings(projects_root=tmp_path / "projects"))


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


def _write_speech_like_wav(path: Path, *, amplitude: int = 5000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = 4800
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(24000)
        payload = b"".join(struct.pack("<h", amplitude) for _ in range(frames))
        handle.writeframes(payload)


def _setup_part(store: ProjectStore) -> tuple[str, str]:
    store.create_project("book-1")
    store.create_part("book-1", part_id="part-001")
    return "book-1", "part-001"


def test_gemini_executor_creation() -> None:
    executor = GeminiNarrationChunkExecutor(event_bus=EventBus())
    assert executor is not None


def test_chunk_text_passed_to_synthesize(
    project_store: ProjectStore,
    tmp_path: Path,
) -> None:
    pid, part = _setup_part(project_store)
    project_store.create_chunk(pid, part, 1, text="Persian sample line")
    chunk = project_store.load_chunk(pid, part, 1)
    out = project_store.part_layout(pid, part).narration_wav_path(1)

    with patch(
        "app.narration.bridge.check_narration_engine_ready",
        return_value=NarrationEngineStatus(ready=True),
    ), patch(
        "app.narration.bridge.synthesize_chunk_text",
    ) as synth:
        _write_speech_like_wav(out)
        synth.side_effect = lambda text, path: _write_speech_like_wav(path)

        GeminiNarrationChunkExecutor().generate_chunk(
            project_id=pid,
            part_id=part,
            chunk=chunk,
            output_path=out,
        )
        synth.assert_called_once()
        assert synth.call_args[0][0] == "Persian sample line"
        assert synth.call_args[0][1] == out


def test_output_path_correctness(project_store: ProjectStore, tmp_path: Path) -> None:
    pid, part = _setup_part(project_store)
    project_store.create_chunk(pid, part, 2, text="hello")
    chunk = project_store.load_chunk(pid, part, 2)
    expected = project_store.part_layout(pid, part).narration_wav_path(2)

    with patch(
        "app.narration.bridge.check_narration_engine_ready",
        return_value=NarrationEngineStatus(ready=True),
    ), patch(
        "app.narration.bridge.synthesize_chunk_text",
        side_effect=lambda _text, path: _write_speech_like_wav(path),
    ):
        result = GeminiNarrationChunkExecutor().generate_chunk(
            project_id=pid,
            part_id=part,
            chunk=chunk,
            output_path=expected,
        )
    assert result == expected
    assert expected.is_file()


def test_worker_narration_execution(
    project_store: ProjectStore,
    tmp_path: Path,
) -> None:
    from app.queue.manager import QueueManager
    from app.queue.store import QueueStore

    pid, part = _setup_part(project_store)
    project_store.create_chunk(pid, part, 1, text="worker text")
    chunk = project_store.load_chunk(pid, part, 1)
    chunk.state = STATE_NARRATION_QUEUED
    project_store.save_chunk(pid, part, chunk)

    queue = QueueManager(
        store=QueueStore(settings=AppSettings(queue_root=tmp_path / "queue")),
        project_store=project_store,
        event_bus=EventBus(),
    )

    def fake_synth(text: str, path: Path) -> None:
        _write_speech_like_wav(path)

    with patch(
        "app.narration.bridge.check_narration_engine_ready",
        return_value=NarrationEngineStatus(ready=True),
    ), patch(
        "app.narration.bridge.synthesize_chunk_text",
        side_effect=fake_synth,
    ):
        engine = WorkerExecutionEngine(
            queue=queue,
            project_store=project_store,
            event_bus=EventBus(),
        )
        engine.startup()
        queue.enqueue(project_id=pid, part_id=part, job_type="narration", chunk_id=1)
        assert engine.run_once() is True

    updated = project_store.load_chunk(pid, part, 1)
    assert updated.state == STATE_NARRATION_READY
    assert updated.narration.file == "narration/0001.wav"


def test_narration_ready_state_transition(project_store: ProjectStore) -> None:
    pid, part = _setup_part(project_store)
    project_store.create_chunk(pid, part, 1, text="x")
    chunk = project_store.load_chunk(pid, part, 1)
    chunk.state = STATE_NARRATION_QUEUED
    project_store.save_chunk(pid, part, chunk)
    out = project_store.part_layout(pid, part).narration_wav_path(1)

    with patch(
        "app.narration.bridge.check_narration_engine_ready",
        return_value=NarrationEngineStatus(ready=True),
    ), patch(
        "app.narration.bridge.synthesize_chunk_text",
        side_effect=lambda _t, p: _write_speech_like_wav(p),
    ):
        JobRunner(
            project_store,
            GeminiNarrationChunkExecutor(),
            MagicMock(),
            BuildService(project_store),
        ).execute(
            QueueItem(
                job_id="j1",
                project_id=pid,
                part_id=part,
                chunk_id=1,
                job_type="narration",
            )
        )

    assert project_store.load_chunk(pid, part, 1).state == STATE_NARRATION_READY


def test_failure_propagation(
    project_store: ProjectStore,
    tmp_path: Path,
) -> None:
    pid, part = _setup_part(project_store)
    project_store.create_chunk(pid, part, 1, text="fail me")
    chunk = project_store.load_chunk(pid, part, 1)
    chunk.state = STATE_NARRATION_QUEUED
    project_store.save_chunk(pid, part, chunk)

    queue = QueueManager(
        store=QueueStore(settings=AppSettings(queue_root=tmp_path / "queue")),
        project_store=project_store,
        event_bus=EventBus(),
    )

    with patch(
        "app.narration.bridge.check_narration_engine_ready",
        return_value=NarrationEngineStatus(ready=True),
    ), patch(
        "app.narration.bridge.synthesize_chunk_text",
        side_effect=RuntimeError("quota exhausted"),
    ):
        engine = WorkerExecutionEngine(
            queue=queue,
            project_store=project_store,
            event_bus=EventBus(),
        )
        engine.startup()
        queue.enqueue(project_id=pid, part_id=part, job_type="narration", chunk_id=1)
        engine.run_once()

    _, failed, _ = queue._store.load_history()
    assert len(failed) == 1
    assert "quota" in (failed[0].last_error or "").lower()


def test_missing_narration_engine(project_store: ProjectStore) -> None:
    pid, part = _setup_part(project_store)
    project_store.create_chunk(pid, part, 1, text="x")
    chunk = project_store.load_chunk(pid, part, 1)
    out = project_store.part_layout(pid, part).narration_wav_path(1)

    with patch(
        "app.narration.bridge.check_narration_engine_ready",
        return_value=NarrationEngineStatus(
            ready=False,
            message="Narration engine unavailable",
        ),
    ):
        with pytest.raises(NarrationEngineUnavailableError):
            GeminiNarrationChunkExecutor().generate_chunk(
                project_id=pid,
                part_id=part,
                chunk=chunk,
                output_path=out,
            )
    assert not out.exists()


def test_event_emission(project_store: ProjectStore, event_bus: EventBus) -> None:
    pid, part = _setup_part(project_store)
    project_store.create_chunk(pid, part, 1, text="events")
    chunk = project_store.load_chunk(pid, part, 1)
    out = project_store.part_layout(pid, part).narration_wav_path(1)

    received: list[str] = []

    def collect(env: Any) -> None:
        received.append(env.event_type)

    for event_type in (
        EVENT_NARRATION_CHUNK_STARTED,
        EVENT_NARRATION_CHUNK_COMPLETED,
        EVENT_NARRATION_CHUNK_FAILED,
    ):
        event_bus.subscribe(event_type, collect)

    with patch(
        "app.narration.bridge.check_narration_engine_ready",
        return_value=NarrationEngineStatus(ready=True),
    ), patch(
        "app.narration.bridge.synthesize_chunk_text",
        side_effect=lambda _t, p: _write_speech_like_wav(p),
    ):
        GeminiNarrationChunkExecutor(event_bus=event_bus).generate_chunk(
            project_id=pid,
            part_id=part,
            chunk=chunk,
            output_path=out,
        )

    assert EVENT_NARRATION_CHUNK_STARTED in received
    assert EVENT_NARRATION_CHUNK_COMPLETED in received
    assert EVENT_NARRATION_CHUNK_FAILED not in received


def test_vc_path_unaffected(project_store: ProjectStore) -> None:
    from app.contracts.states import STATE_VC_QUEUED, STATE_VC_READY  # noqa: F401

    pid, part = _setup_part(project_store)
    ref = project_store.part_layout(pid, part).root / "reference.wav"
    _write_speech_like_wav(ref)
    part_m = project_store.load_part(pid, part)
    part_m.processing_profile = "reference.wav"
    project_store.save_part(part_m)

    project_store.create_chunk(pid, part, 1)
    _write_speech_like_wav(project_store.part_layout(pid, part).narration_wav_path(1))
    mark_narration_approved_for_vc(project_store, pid, part, 1)

    speaker = MagicMock()
    speaker.convert_chunk = MagicMock(
        return_value=project_store.part_layout(pid, part).vc_wav_path(1)
    )

    chunk = project_store.load_chunk(pid, part, 1)
    chunk.state = STATE_VC_QUEUED
    project_store.save_chunk(pid, part, chunk)

    with patch(
        "app.narration.bridge.check_narration_engine_ready",
        return_value=NarrationEngineStatus(ready=False),
    ):
        JobRunner(
            project_store,
            GeminiNarrationChunkExecutor(),
            speaker,
            BuildService(project_store),
        ).execute(
            QueueItem(
                job_id="vc-1",
                project_id=pid,
                part_id=part,
                chunk_id=1,
                job_type="vc",
            )
        )

    speaker.convert_chunk.assert_called_once()
    assert project_store.load_chunk(pid, part, 1).state == STATE_VC_READY


def test_build_path_unaffected(project_store: ProjectStore) -> None:
    pid, part = _setup_part(project_store)
    pl = project_store.part_layout(pid, part)
    for cid in (1, 2):
        project_store.create_chunk(pid, part, cid)
        _write_speech_like_wav(pl.vc_wav_path(cid))
    build = project_store.create_build(
        pid, part, name="full", chunks=[1, 2], build_id="build-001"
    )

    JobRunner(
        project_store,
        GeminiNarrationChunkExecutor(),
        MagicMock(),
        BuildService(project_store),
    ).execute(
        QueueItem(
            job_id=build.build_id,
            project_id=pid,
            part_id=part,
            chunk_id=None,
            job_type="build",
        )
    )
    assert pl.build_output_path(build.build_id).is_file()


def test_empty_chunk_text_rejected(project_store: ProjectStore) -> None:
    pid, part = _setup_part(project_store)
    project_store.create_chunk(pid, part, 1, text="")
    chunk = project_store.load_chunk(pid, part, 1)
    out = project_store.part_layout(pid, part).narration_wav_path(1)

    with pytest.raises(NarrationChunkExecutionError, match="empty"):
        GeminiNarrationChunkExecutor().generate_chunk(
            project_id=pid,
            part_id=part,
            chunk=chunk,
            output_path=out,
        )


def test_wave_executor_still_available_for_tests(project_store: ProjectStore) -> None:
    pid, part = _setup_part(project_store)
    project_store.create_chunk(pid, part, 1, text="ignored by wave")
    chunk = project_store.load_chunk(pid, part, 1)
    out = project_store.part_layout(pid, part).narration_wav_path(1)
    WaveNarrationChunkExecutor().generate_chunk(
        project_id=pid,
        part_id=part,
        chunk=chunk,
        output_path=out,
    )
    assert out.is_file()
