"""E9.2-A reference audio support tests."""

from __future__ import annotations

import io
import wave
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.api.services import ApplicationServices
from app.config.settings import AppSettings
from app.contracts.queue import QueueItem
from app.contracts.states import (
    STATE_NARRATION_APPROVED,
    STATE_NARRATION_READY,
    STATE_VC_FAILED,
    STATE_VC_PROCESSING,
    STATE_VC_QUEUED,
)
from app.lifecycle.exceptions import ReferenceAudioRequiredError
from tests.lifecycle_helpers import mark_narration_approved_for_vc
from app.queue.manager import QueueManager
from app.services.reference_audio_service import (
    ReferenceAudioInvalidError,
    ReferenceAudioService,
    reference_audio_ready,
    resolve_reference_audio_path,
)
from app.storage.project_store import ProjectStore
from app.worker.job_runner import JobExecutionError, JobRunner


@pytest.fixture
def tmp_settings(tmp_path: Path) -> AppSettings:
    return AppSettings(
        projects_root=tmp_path / "projects",
        queue_root=tmp_path / "queue",
        events_root=tmp_path / "events",
    )


@pytest.fixture
def project_store(tmp_settings: AppSettings) -> ProjectStore:
    return ProjectStore(tmp_settings)


@pytest.fixture
def api_client(tmp_path: Path) -> TestClient:
    settings = AppSettings(
        projects_root=tmp_path / "projects",
        queue_root=tmp_path / "queue",
        events_root=tmp_path / "events",
    )
    services = ApplicationServices.create(settings)
    app = create_app(services)
    client = TestClient(app)
    try:
        yield client
    finally:
        if services.worker.is_running():
            services.worker.stop()


def _write_wav(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(24000)
        handle.writeframes(b"\x00\x01" * 1200)


def _wav_bytes() -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(24000)
        handle.writeframes(b"\x00\x01" * 1200)
    return buffer.getvalue()


def _setup_vc_ready_part(
    store: ProjectStore,
    *,
    with_reference: bool,
) -> tuple[str, str, int]:
    store.create_project("book-1", title="")
    store.create_part("book-1", part_id="part-001", title="")
    store.create_chunk("book-1", "part-001", 1, text="hello")
    pl = store.part_layout("book-1", "part-001")
    _write_wav(pl.narration_wav_path(1))
    chunk = store.load_chunk("book-1", "part-001", 1)
    chunk.state = STATE_NARRATION_READY
    store.save_chunk("book-1", "part-001", chunk)
    mark_narration_approved_for_vc(store, "book-1", "part-001", 1)
    if with_reference:
        _write_wav(pl.reference_wav_path())
    return "book-1", "part-001", 1


def test_reference_wav_path_on_layout(project_store: ProjectStore) -> None:
    project_store.create_project("p1", title="")
    project_store.create_part("p1", part_id="part-01", title="")
    pl = project_store.part_layout("p1", "part-01")
    assert pl.reference_wav_path() == pl.root / "reference.wav"


def test_reference_audio_service_upload_replace_delete(
    project_store: ProjectStore,
) -> None:
    project_store.create_project("p1", title="")
    project_store.create_part("p1", part_id="part-01", title="")
    svc = ReferenceAudioService(project_store)
    pl = project_store.part_layout("p1", "part-01")

    assert not svc.reference_exists("p1", "part-01")

    result = svc.upload_reference_audio("p1", "part-01", _wav_bytes())
    assert result.path == "reference.wav"
    assert pl.reference_wav_path().is_file()

    meta = svc.reference_metadata("p1", "part-01")
    assert meta.exists is True
    assert meta.size_bytes == pl.reference_wav_path().stat().st_size

    svc.upload_reference_audio("p1", "part-01", _wav_bytes())
    assert pl.reference_wav_path().is_file()

    svc.delete_reference_audio("p1", "part-01")
    assert not pl.reference_wav_path().is_file()
    assert not svc.reference_exists("p1", "part-01")


def test_upload_rejects_invalid_wav(project_store: ProjectStore) -> None:
    project_store.create_project("p1", title="")
    project_store.create_part("p1", part_id="part-01", title="")
    svc = ReferenceAudioService(project_store)
    with pytest.raises(ReferenceAudioInvalidError):
        svc.upload_reference_audio("p1", "part-01", b"not-a-wav")


def test_resolve_reference_audio_path_processing_profile(
    project_store: ProjectStore,
) -> None:
    project_store.create_project("p1", title="")
    project_store.create_part("p1", part_id="part-01", title="")
    pl = project_store.part_layout("p1", "part-01")
    custom = pl.root / "voices" / "ref.wav"
    _write_wav(custom)
    part = project_store.load_part("p1", "part-01")
    part.processing_profile = "voices/ref.wav"
    project_store.save_part(part)
    resolved = resolve_reference_audio_path(project_store, "p1", "part-01")
    assert resolved == custom.resolve()


def test_api_upload_download_delete_metadata(api_client: TestClient) -> None:
    api_client.post("/api/v1/projects", json={"project_id": "book-1", "title": ""})
    api_client.post(
        "/api/v1/projects/book-1/parts",
        json={"part_id": "part-001", "title": ""},
    )

    part = api_client.get("/api/v1/projects/book-1/parts/part-001")
    assert part.status_code == 200
    assert part.json()["reference_audio"]["exists"] is False

    upload = api_client.post(
        "/api/v1/projects/book-1/parts/part-001/reference",
        files={"file": ("reference.wav", _wav_bytes(), "audio/wav")},
    )
    assert upload.status_code == 200
    assert upload.json()["path"] == "reference.wav"

    part2 = api_client.get("/api/v1/projects/book-1/parts/part-001")
    assert part2.json()["reference_audio"]["exists"] is True
    assert part2.json()["reference_audio"]["size_bytes"] > 0

    download = api_client.get("/api/v1/projects/book-1/parts/part-001/reference")
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("audio/")

    deleted = api_client.delete("/api/v1/projects/book-1/parts/part-001/reference")
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"

    missing = api_client.get("/api/v1/projects/book-1/parts/part-001/reference")
    assert missing.status_code == 404


def test_vc_queue_blocked_without_reference(
    project_store: ProjectStore,
    tmp_settings: AppSettings,
) -> None:
    from app.events.bus import EventBus
    from app.queue.store import QueueStore

    _setup_vc_ready_part(project_store, with_reference=False)
    queue = QueueManager(
        store=QueueStore(tmp_settings),
        project_store=project_store,
        event_bus=EventBus(),
    )
    with pytest.raises(ReferenceAudioRequiredError) as exc_info:
        queue.enqueue(
            project_id="book-1",
            part_id="part-001",
            job_type="vc",
            chunk_id=1,
        )
    assert "Reference voice not configured" in str(exc_info.value)


def test_vc_queue_succeeds_with_reference(
    project_store: ProjectStore,
    tmp_settings: AppSettings,
) -> None:
    from app.events.bus import EventBus
    from app.queue.store import QueueStore

    _setup_vc_ready_part(project_store, with_reference=True)
    queue = QueueManager(
        store=QueueStore(tmp_settings),
        project_store=project_store,
        event_bus=EventBus(),
    )
    item = queue.enqueue(
        project_id="book-1",
        part_id="part-001",
        job_type="vc",
        chunk_id=1,
    )
    assert item.job_type == "vc"
    chunk = project_store.load_chunk("book-1", "part-001", 1)
    assert chunk.state == STATE_VC_QUEUED


def test_worker_missing_reference_sets_vcfailed_not_processing(
    project_store: ProjectStore,
) -> None:
    pid, part, cid = _setup_vc_ready_part(project_store, with_reference=False)
    chunk = project_store.load_chunk(pid, part, cid)
    chunk.state = STATE_VC_QUEUED
    project_store.save_chunk(pid, part, chunk)

    speaker = MagicMock()
    runner = JobRunner(
        project_store,
        narration=MagicMock(),
        speaker=speaker,
        build_service=MagicMock(),
    )
    job = QueueItem(
        job_id="vc-1",
        project_id=pid,
        part_id=part,
        chunk_id=cid,
        job_type="vc",
        status="running",
    )

    with pytest.raises(JobExecutionError):
        runner.execute(job)

    speaker.convert_chunk.assert_not_called()
    updated = project_store.load_chunk(pid, part, cid)
    assert updated.state == STATE_VC_FAILED
    assert updated.last_error is not None
    assert "Reference voice" in updated.last_error
    assert updated.state != STATE_VC_PROCESSING


def test_reference_audio_ready_helper(project_store: ProjectStore) -> None:
    pid, part, _ = _setup_vc_ready_part(project_store, with_reference=False)
    assert not reference_audio_ready(project_store, project_id=pid, part_id=part)
    _write_wav(project_store.part_layout(pid, part).reference_wav_path())
    assert reference_audio_ready(project_store, project_id=pid, part_id=part)
