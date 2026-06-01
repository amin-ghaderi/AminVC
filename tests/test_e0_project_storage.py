"""E0 canonical project storage."""

from __future__ import annotations

import json
import wave
from pathlib import Path

import pytest

from app.config.settings import AppSettings
from app.contracts.events import VcProgressEvent
from app.contracts.manifests import AssetSlot, ChunkManifest
from app.contracts.queue import QueueItemIdentity
from app.contracts.recovery_rules import detect_interrupted_vc
from app.contracts.states import (
    STATE_DRAFT,
    STATE_VC_PROCESSING,
    VALID_CHUNK_STATES,
)
from app.storage.json_io import read_json
from app.storage.project_store import ProjectStore
from app.storage.serialization import InvalidStateError, chunk_to_dict, project_to_dict


@pytest.fixture
def store(tmp_path: Path) -> ProjectStore:
    return ProjectStore(settings=AppSettings(projects_root=tmp_path / "projects"))


def test_canonical_layout(store: ProjectStore) -> None:
    store.create_project("book-1", title="Test")
    store.create_part("book-1", part_id="part-001", title="فصل اول")
    pl = store.part_layout("book-1", "part-001")
    assert pl.manifest_path.name == "manifest.json"
    assert pl.chunk_manifest_path(1) == pl.chunks_dir / "0001.json"
    assert pl.narration_wav_path(1).name == "0001.wav"
    assert pl.vc_wav_path(1).parent.name == "vc"
    assert pl.source_pdf_path.as_posix().endswith("source/source.pdf")


def test_project_manifest_schema(store: ProjectStore) -> None:
    store.create_project("book-1", title="زمان انتخاب")
    data = read_json(store.layout("book-1").project_manifest_path)
    assert set(data.keys()) == {
        "project_id",
        "title",
        "created_at",
        "updated_at",
        "status",
        "parts",
    }
    assert data["status"] == "active"
    assert data["parts"] == []


def test_part_and_chunk_manifests(store: ProjectStore) -> None:
    store.create_project("book-1")
    store.create_part("book-1", part_id="part-001")
    chunk = store.create_chunk("book-1", "part-001", 1, text="Hello")
    data = read_json(store.part_layout("book-1", "part-001").chunk_manifest_path(1))
    assert data["chunk_id"] == 1
    assert "narration" in data and "vc" in data
    assert data["narration"]["file"] == "narration/0001.wav"
    assert data["vc"]["file"] == "vc/0001.wav"
    assert chunk.state == STATE_DRAFT

    project = store.load_project("book-1")
    assert project.parts == ["part-001"]


def test_invalid_state_rejected(store: ProjectStore) -> None:
    store.create_project("book-1")
    store.create_part("book-1", part_id="part-001")
    store.create_chunk("book-1", "part-001", 1)
    chunk = store.load_chunk("book-1", "part-001", 1)
    chunk.state = "NotARealState"
    with pytest.raises(InvalidStateError):
        store.save_chunk("book-1", "part-001", chunk)


def test_recovery_rule_detect_interrupted(tmp_path: Path) -> None:
    chunk = ChunkManifest(chunk_id=1, state=STATE_VC_PROCESSING, vc=AssetSlot(file="vc/0001.wav"))
    missing = tmp_path / "vc" / "0001.wav"
    assert detect_interrupted_vc(chunk, missing) is True
    missing.parent.mkdir(parents=True)
    missing.write_bytes(b"wav")
    assert detect_interrupted_vc(chunk, missing) is True
    valid = tmp_path / "vc" / "0002.wav"
    with wave.open(str(valid), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(24000)
        handle.writeframes(b"\x00\x00" * 100)
    chunk_ok = ChunkManifest(
        chunk_id=2,
        state=STATE_VC_PROCESSING,
        vc=AssetSlot(file="vc/0002.wav"),
    )
    assert detect_interrupted_vc(chunk_ok, valid) is False


def test_event_and_queue_contracts() -> None:
    event = VcProgressEvent(
        type="vc_progress",
        project_id="p",
        part_id="part-001",
        chunk_id=1,
        current_step=5,
        total_steps=30,
        elapsed_seconds=10.0,
        estimated_remaining_seconds=50.0,
    )
    restored = VcProgressEvent.from_dict(event.to_dict())
    assert restored.total_steps == 30

    item = QueueItemIdentity(
        project_id="p",
        part_id="part-001",
        chunk_id=1,
        job_type="vc",
    )
    assert item.to_dict()["job_type"] == "vc"


def test_all_valid_states_count() -> None:
    assert len(VALID_CHUNK_STATES) == 14
