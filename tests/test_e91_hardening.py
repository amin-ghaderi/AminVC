"""E9.1 production hardening tests."""

from __future__ import annotations

import json
import wave
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.api.services import ApplicationServices
from app.config.settings import AppSettings
from app.contracts.events import MAX_EVENT_LOG_SIZE_BYTES
from app.contracts.manifests import AssetSlot, ChunkManifest
from app.contracts.queue import MAX_QUEUE_HISTORY, QueueItem
from app.contracts.recovery_rules import (
    detect_interrupted_narration,
    detect_interrupted_vc,
)
from app.contracts.states import STATE_NARRATION_PROCESSING, STATE_VC_PROCESSING
from app.contracts.wav_validation import is_valid_wav
from app.events.store import EventStore
from app.contracts.events import (
    EVENT_QUEUE_SNAPSHOT_UPDATED,
    QueueSnapshotPayload,
    create_event_envelope,
)
from app.queue.manager import QueueManager
from app.queue.store import QueueStore
from app.services.audiobook_service import WAV_MERGE_CHUNK_FRAMES, merge_pcm_wavs
from app.storage.project_store import ProjectStore


def _write_pcm_wav(path: Path, *, nframes: int = 2400) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(24000)
        handle.writeframes(b"\x00\x00" * nframes)


def _queue_item(index: int, *, status: str = "completed") -> QueueItem:
    return QueueItem(
        job_id=f"job-{index:04d}",
        project_id="book-1",
        part_id="part-001",
        chunk_id=index,
        job_type="narration",
        status=status,  # type: ignore[arg-type]
    )


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


@pytest.fixture
def queue_store(tmp_path: Path) -> QueueStore:
    settings = AppSettings(
        projects_root=tmp_path / "projects",
        queue_root=tmp_path / "queue",
    )
    store = QueueStore(settings)
    store.ensure_tree()
    return store


@pytest.fixture
def project_store(tmp_path: Path) -> ProjectStore:
    return ProjectStore(settings=AppSettings(projects_root=tmp_path / "projects"))


def test_history_trimming_completed(queue_store: QueueStore) -> None:
    over = MAX_QUEUE_HISTORY + 50
    completed = [_queue_item(i) for i in range(over)]
    queue_store.save_history(completed, [], [])
    loaded, failed, cancelled = queue_store.load_history()
    assert len(loaded) == MAX_QUEUE_HISTORY
    assert loaded[0].job_id == f"job-{50:04d}"
    assert loaded[-1].job_id == f"job-{over - 1:04d}"
    assert failed == []
    assert cancelled == []


def test_history_trimming_failed(queue_store: QueueStore) -> None:
    failed = [_queue_item(i, status="failed") for i in range(MAX_QUEUE_HISTORY + 10)]
    queue_store.save_history([], failed, [])
    _, loaded_failed, _ = queue_store.load_history()
    assert len(loaded_failed) == MAX_QUEUE_HISTORY
    assert loaded_failed[0].job_id == "job-0010"


def test_history_trimming_cancelled(queue_store: QueueStore) -> None:
    cancelled = [_queue_item(i, status="cancelled") for i in range(MAX_QUEUE_HISTORY + 5)]
    queue_store.save_history([], [], cancelled)
    _, _, loaded_cancelled = queue_store.load_history()
    assert len(loaded_cancelled) == MAX_QUEUE_HISTORY
    assert loaded_cancelled[0].job_id == "job-0005"


def test_history_trimming_backward_compatibility(
    queue_store: QueueStore,
    project_store: ProjectStore,
) -> None:
    queue_store.layout.history_path.write_text(
        json.dumps({"completed": [], "failed": []}),
        encoding="utf-8",
    )
    completed, failed, cancelled = queue_store.load_history()
    assert completed == failed == cancelled == []

    mgr = QueueManager(store=queue_store, project_store=project_store)
    snap = mgr.restore()
    assert snap.cancelled == snap.completed == snap.failed == 0


def test_event_rotation_occurs(tmp_path: Path) -> None:
    settings = AppSettings(events_root=tmp_path / "events")
    store = EventStore(settings)
    latest = tmp_path / "events" / "latest.jsonl"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_bytes(b"x" * (MAX_EVENT_LOG_SIZE_BYTES + 1))

    event = create_event_envelope(
        EVENT_QUEUE_SNAPSHOT_UPDATED,
        payload=QueueSnapshotPayload(1, 0, 0, 0, 0).to_dict(),
    )
    store.append(event)

    archives = list((tmp_path / "events" / "archive").glob("events-*.jsonl"))
    assert len(archives) == 1
    assert archives[0].stat().st_size == MAX_EVENT_LOG_SIZE_BYTES + 1
    assert latest.is_file()
    assert latest.stat().st_size > 0


def test_event_rotation_new_file_created_and_append_continues(tmp_path: Path) -> None:
    settings = AppSettings(events_root=tmp_path / "events")
    store = EventStore(settings)
    latest = tmp_path / "events" / "latest.jsonl"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_bytes(b"y" * (MAX_EVENT_LOG_SIZE_BYTES + 100))

    event = create_event_envelope(
        EVENT_QUEUE_SNAPSHOT_UPDATED,
        payload=QueueSnapshotPayload(2, 0, 0, 0, 0).to_dict(),
    )
    store.append(event)

    text = latest.read_text(encoding="utf-8").strip()
    assert text
    parsed = json.loads(text)
    assert parsed["event_type"] == EVENT_QUEUE_SNAPSHOT_UPDATED


def test_event_rotation_archive_preserved(tmp_path: Path) -> None:
    settings = AppSettings(events_root=tmp_path / "events")
    store = EventStore(settings)
    latest = tmp_path / "events" / "latest.jsonl"
    latest.parent.mkdir(parents=True, exist_ok=True)
    payload = b"archive-marker" + b"z" * MAX_EVENT_LOG_SIZE_BYTES
    latest.write_bytes(payload)

    store.append(
        create_event_envelope(
            EVENT_QUEUE_SNAPSHOT_UPDATED,
            payload=QueueSnapshotPayload(0, 0, 0, 0, 0).to_dict(),
        )
    )

    archive = next((tmp_path / "events" / "archive").glob("events-*.jsonl"))
    assert payload in archive.read_bytes()


def test_is_valid_wav_missing(tmp_path: Path) -> None:
    assert is_valid_wav(tmp_path / "missing.wav") is False


def test_is_valid_wav_zero_byte(tmp_path: Path) -> None:
    path = tmp_path / "empty.wav"
    path.write_bytes(b"")
    assert is_valid_wav(path) is False


def test_is_valid_wav_corrupt(tmp_path: Path) -> None:
    path = tmp_path / "bad.wav"
    path.write_bytes(b"not-a-wav")
    assert is_valid_wav(path) is False


def test_is_valid_wav_valid(tmp_path: Path) -> None:
    path = tmp_path / "ok.wav"
    _write_pcm_wav(path)
    assert is_valid_wav(path) is True


def test_detect_interrupted_narration_invalid_wav(tmp_path: Path) -> None:
    chunk = ChunkManifest(chunk_id=1, state=STATE_NARRATION_PROCESSING)
    path = tmp_path / "narration.wav"
    path.write_bytes(b"corrupt")
    assert detect_interrupted_narration(chunk, path) is True


def test_detect_interrupted_vc_invalid_wav(tmp_path: Path) -> None:
    chunk = ChunkManifest(chunk_id=1, state=STATE_VC_PROCESSING)
    path = tmp_path / "vc.wav"
    path.write_bytes(b"corrupt")
    assert detect_interrupted_vc(chunk, path) is True


def test_recovery_report_route_exists(api_client: TestClient) -> None:
    api_client.post("/api/v1/projects", json={"project_id": "book-1", "title": ""})
    api_client.post(
        "/api/v1/projects/book-1/parts",
        json={"part_id": "part-001", "title": ""},
    )
    response = api_client.get(
        "/api/v1/projects/book-1/recovery-report",
        params={"part_id": "part-001"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == "book-1"
    assert data["part_id"] == "part-001"
    assert "completed_chunks" in data


def test_recovery_report_project_not_found(api_client: TestClient) -> None:
    response = api_client.get(
        "/api/v1/projects/missing/recovery-report",
        params={"part_id": "part-001"},
    )
    assert response.status_code == 404


def test_recovery_report_openapi_contains_route(api_client: TestClient) -> None:
    schema = api_client.get("/openapi.json").json()
    assert "/api/v1/projects/{project_id}/recovery-report" in schema["paths"]


def test_merge_pcm_wavs_small_output(tmp_path: Path) -> None:
    a = tmp_path / "a.wav"
    b = tmp_path / "b.wav"
    _write_pcm_wav(a, nframes=100)
    _write_pcm_wav(b, nframes=200)
    out = tmp_path / "merged.wav"
    merge_pcm_wavs([a, b], out)
    with wave.open(str(out), "rb") as merged:
        assert merged.getnframes() == 300


def test_merge_pcm_wavs_large_many_chunks(tmp_path: Path) -> None:
    paths: list[Path] = []
    for i in range(50):
        path = tmp_path / f"{i:04d}.wav"
        _write_pcm_wav(path, nframes=400)
        paths.append(path)
    out = tmp_path / "large-merged.wav"
    merge_pcm_wavs(paths, out)
    with wave.open(str(out), "rb") as merged:
        assert merged.getnframes() == 50 * 400


def test_merge_pcm_wavs_output_equality_streaming(tmp_path: Path) -> None:
    paths = []
    for i in range(3):
        path = tmp_path / f"chunk{i}.wav"
        _write_pcm_wav(path, nframes=500 + i * 100)
        paths.append(path)

    expected = b""
    for path in paths:
        with wave.open(str(path), "rb") as src:
            expected += src.readframes(src.getnframes())

    out = tmp_path / "out.wav"
    merge_pcm_wavs(paths, out)

    with wave.open(str(out), "rb") as merged:
        got = merged.readframes(merged.getnframes())
    assert got == expected


def test_merge_pcm_wavs_memory_safe_chunked_reads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "one.wav"
    _write_pcm_wav(path, nframes=WAV_MERGE_CHUNK_FRAMES * 3 + 100)
    sizes: list[int] = []
    original = wave.Wave_read.readframes

    def spy(self: wave.Wave_read, nframes: int) -> bytes:
        sizes.append(nframes)
        return original(self, nframes)

    monkeypatch.setattr(wave.Wave_read, "readframes", spy)
    out = tmp_path / "streamed.wav"
    merge_pcm_wavs([path], out)
    assert max(sizes) <= WAV_MERGE_CHUNK_FRAMES
    assert sum(sizes) >= WAV_MERGE_CHUNK_FRAMES * 3
