"""E2.0 — Recovery engine."""

from __future__ import annotations

from pathlib import Path
import wave

import pytest

from app.config.settings import AppSettings
from app.contracts.manifests import AssetSlot, ChunkManifest
from app.contracts.recovery import RecoveryCategory
from app.contracts.recovery_rules import detect_interrupted_narration, detect_interrupted_vc
from app.contracts.states import (
    STATE_INTERRUPTED,
    STATE_NARRATION_APPROVED,
    STATE_NARRATION_FAILED,
    STATE_NARRATION_PROCESSING,
    STATE_NARRATION_READY,
    STATE_VC_APPROVED,
    STATE_VC_FAILED,
    STATE_VC_PROCESSING,
    STATE_VC_READY,
)
from app.recovery.recovery_service import MAX_CHUNK_RETRIES, RecoveryService
from app.recovery.scanner import RecoveryScanner
from app.storage.project_store import ProjectStore


@pytest.fixture
def store(tmp_path: Path) -> ProjectStore:
    return ProjectStore(settings=AppSettings(projects_root=tmp_path / "projects"))


@pytest.fixture
def recovery(store: ProjectStore) -> RecoveryService:
    return RecoveryService(store=store)


def _setup_part(store: ProjectStore, n_chunks: int = 6) -> tuple[str, str]:
    store.create_project("book-1")
    store.create_part("book-1", part_id="part-001")
    for i in range(1, n_chunks + 1):
        store.create_chunk("book-1", "part-001", i)
    return "book-1", "part-001"


def test_interrupted_vc_detection(tmp_path: Path) -> None:
    chunk = ChunkManifest(
        chunk_id=1,
        state=STATE_VC_PROCESSING,
        vc=AssetSlot(file="vc/0001.wav"),
    )
    assert detect_interrupted_vc(chunk, tmp_path / "missing.wav") is True
    (tmp_path / "vc").mkdir()
    corrupt = tmp_path / "vc" / "0001.wav"
    corrupt.write_bytes(b"x")
    assert detect_interrupted_vc(chunk, corrupt) is True
    valid = tmp_path / "vc" / "0002.wav"
    with wave.open(str(valid), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(24000)
        handle.writeframes(b"\x00\x00" * 100)
    chunk_valid = ChunkManifest(
        chunk_id=2,
        state=STATE_VC_PROCESSING,
        vc=AssetSlot(file="vc/0002.wav"),
    )
    assert detect_interrupted_vc(chunk_valid, valid) is False


def test_interrupted_narration_detection(tmp_path: Path) -> None:
    chunk = ChunkManifest(
        chunk_id=1,
        state=STATE_NARRATION_PROCESSING,
        narration=AssetSlot(file="narration/0001.wav"),
    )
    assert detect_interrupted_narration(chunk, tmp_path / "missing.wav") is True


def test_scan_transitions_vc_to_interrupted(store: ProjectStore) -> None:
    _setup_part(store, 1)
    chunk = store.load_chunk("book-1", "part-001", 1)
    chunk.state = STATE_VC_PROCESSING
    store.save_chunk("book-1", "part-001", chunk)

    result = RecoveryScanner(store).scan_chunk("book-1", "part-001", 1)
    assert result.category == RecoveryCategory.INTERRUPTED
    reloaded = store.load_chunk("book-1", "part-001", 1)
    assert reloaded.state == STATE_INTERRUPTED


def test_scan_transitions_narration_to_interrupted(store: ProjectStore) -> None:
    _setup_part(store, 1)
    chunk = store.load_chunk("book-1", "part-001", 1)
    chunk.state = STATE_NARRATION_PROCESSING
    store.save_chunk("book-1", "part-001", chunk)

    result = RecoveryScanner(store).scan_chunk("book-1", "part-001", 1)
    assert result.category == RecoveryCategory.INTERRUPTED
    assert store.load_chunk("book-1", "part-001", 1).state == STATE_INTERRUPTED


def test_last_completed_and_next_chunk(recovery: RecoveryService, store: ProjectStore) -> None:
    _setup_part(store, 6)
    pl = store.part_layout("book-1", "part-001")

    for i in (1, 2, 3):
        c = store.load_chunk("book-1", "part-001", i)
        c.state = STATE_VC_APPROVED
        (pl.narration_dir / f"{i:04d}.wav").write_bytes(b"n")
        (pl.vc_dir / f"{i:04d}.wav").write_bytes(b"v")
        store.save_chunk("book-1", "part-001", c)

    c4 = store.load_chunk("book-1", "part-001", 4)
    c4.state = STATE_VC_PROCESSING
    store.save_chunk("book-1", "part-001", c4)

    report = recovery.build_recovery_report("book-1", "part-001")
    assert report.last_completed_chunk == 3
    assert report.next_chunk == 4
    assert 4 in report.interrupted_chunks


def test_resume_plan_generation(recovery: RecoveryService, store: ProjectStore) -> None:
    _setup_part(store, 6)
    pl = store.part_layout("book-1", "part-001")

    for i in (1, 2, 3):
        c = store.load_chunk("book-1", "part-001", i)
        c.state = STATE_VC_APPROVED
        (pl.narration_dir / f"{i:04d}.wav").write_bytes(b"n")
        (pl.vc_dir / f"{i:04d}.wav").write_bytes(b"v")
        store.save_chunk("book-1", "part-001", c)

    c4 = store.load_chunk("book-1", "part-001", 4)
    c4.state = STATE_VC_PROCESSING
    store.save_chunk("book-1", "part-001", c4)

    plan = recovery.create_resume_plan("book-1", "part-001")
    assert plan.start_chunk == 4
    assert plan.remaining_chunks == [4, 5, 6]


def test_restart_plan_ignores_completion(recovery: RecoveryService, store: ProjectStore) -> None:
    _setup_part(store, 4)
    pl = store.part_layout("book-1", "part-001")
    for i in (1, 2, 3, 4):
        c = store.load_chunk("book-1", "part-001", i)
        c.state = STATE_VC_APPROVED
        (pl.narration_dir / f"{i:04d}.wav").write_bytes(b"n")
        (pl.vc_dir / f"{i:04d}.wav").write_bytes(b"v")
        store.save_chunk("book-1", "part-001", c)

    plan = recovery.create_restart_plan("book-1", "part-001")
    assert plan.chunks == [1, 2, 3, 4]


def test_retry_count_increment_on_resume_prep(recovery: RecoveryService, store: ProjectStore) -> None:
    _setup_part(store, 2)
    c = store.load_chunk("book-1", "part-001", 1)
    c.state = STATE_NARRATION_PROCESSING
    store.save_chunk("book-1", "part-001", c)

    recovery.apply_resume_preparation("book-1", "part-001")
    reloaded = store.load_chunk("book-1", "part-001", 1)
    assert reloaded.state == STATE_INTERRUPTED
    assert reloaded.retry_count == 1


def test_retry_limit_exceeded_narration_failed(recovery: RecoveryService, store: ProjectStore) -> None:
    _setup_part(store, 1)
    c = store.load_chunk("book-1", "part-001", 1)
    c.state = STATE_INTERRUPTED
    c.retry_count = MAX_CHUNK_RETRIES
    store.save_chunk("book-1", "part-001", c)

    recovery.apply_resume_preparation("book-1", "part-001")
    reloaded = store.load_chunk("book-1", "part-001", 1)
    assert reloaded.state == STATE_NARRATION_FAILED
    assert reloaded.retry_count == MAX_CHUNK_RETRIES + 1


def test_retry_limit_exceeded_vc_failed(recovery: RecoveryService, store: ProjectStore) -> None:
    _setup_part(store, 1)
    pl = store.part_layout("book-1", "part-001")
    c = store.load_chunk("book-1", "part-001", 1)
    c.state = STATE_INTERRUPTED
    c.retry_count = MAX_CHUNK_RETRIES
    (pl.narration_dir / "0001.wav").write_bytes(b"n")
    store.save_chunk("book-1", "part-001", c)

    recovery.apply_resume_preparation("book-1", "part-001")
    reloaded = store.load_chunk("book-1", "part-001", 1)
    assert reloaded.state == STATE_VC_FAILED


def test_recovery_report_schema(recovery: RecoveryService, store: ProjectStore) -> None:
    _setup_part(store, 2)
    report = recovery.build_recovery_report("book-1", "part-001")
    data = report.to_dict()
    assert set(data.keys()) == {
        "project_id",
        "part_id",
        "last_completed_chunk",
        "next_chunk",
        "interrupted_chunks",
        "failed_chunks",
        "pending_chunks",
        "completed_chunks",
    }


def test_startup_scan_mixed_states(recovery: RecoveryService, store: ProjectStore) -> None:
    _setup_part(store, 4)
    pl = store.part_layout("book-1", "part-001")

    c1 = store.load_chunk("book-1", "part-001", 1)
    c1.state = STATE_VC_READY
    (pl.narration_dir / "0001.wav").write_bytes(b"n")
    (pl.vc_dir / "0001.wav").write_bytes(b"v")
    store.save_chunk("book-1", "part-001", c1)

    c2 = store.load_chunk("book-1", "part-001", 2)
    c2.state = STATE_NARRATION_FAILED
    store.save_chunk("book-1", "part-001", c2)

    c3 = store.load_chunk("book-1", "part-001", 3)
    c3.state = STATE_NARRATION_PROCESSING
    store.save_chunk("book-1", "part-001", c3)

    project_scan = recovery.scan_project("book-1")
    assert len(project_scan.parts) == 1
    part = project_scan.parts[0]
    cats = {r.chunk_id: r.category for r in part.chunks}
    assert cats[1] == RecoveryCategory.COMPLETED
    assert cats[2] == RecoveryCategory.FAILED
    assert cats[3] == RecoveryCategory.INTERRUPTED
    assert cats[4] == RecoveryCategory.PENDING


def test_build_manifest_detected_on_scan(recovery: RecoveryService, store: ProjectStore) -> None:
    _setup_part(store, 1)
    store.create_build("book-1", "part-001", name="Chapter-Final", build_id="build-001")
    scan = recovery.scan_part("book-1", "part-001")
    assert "build-001" in scan.builds_detected


def test_completed_chunks_not_in_resume_plan(recovery: RecoveryService, store: ProjectStore) -> None:
    _setup_part(store, 4)
    pl = store.part_layout("book-1", "part-001")
    for i in (1, 2, 3):
        c = store.load_chunk("book-1", "part-001", i)
        c.state = STATE_VC_APPROVED
        (pl.narration_dir / f"{i:04d}.wav").write_bytes(b"n")
        (pl.vc_dir / f"{i:04d}.wav").write_bytes(b"v")
        store.save_chunk("book-1", "part-001", c)

    c4 = store.load_chunk("book-1", "part-001", 4)
    c4.state = STATE_VC_PROCESSING
    store.save_chunk("book-1", "part-001", c4)

    plan = recovery.create_resume_plan("book-1", "part-001")
    assert 1 not in plan.remaining_chunks
    assert 2 not in plan.remaining_chunks
    assert 3 not in plan.remaining_chunks
