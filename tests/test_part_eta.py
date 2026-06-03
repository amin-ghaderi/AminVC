"""E9.2-B — Part VC ETA utilities and summary counts."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config.settings import AppSettings
from app.contracts.events import EVENT_VC_CHUNK_COMPLETED, create_event_envelope
from app.contracts.states import (
    STATE_VC_PROCESSING,
    STATE_VC_QUEUED,
    STATE_VC_READY,
)
from app.services.part_summary_service import PartSummaryService
from app.storage.project_store import ProjectStore
from app.vc.part_eta import (
    average_vc_chunk_duration,
    calculate_part_eta,
    dedupe_vc_completion_durations,
    remaining_vc_chunks_after_current,
)


@pytest.fixture
def project_store(tmp_path: Path) -> ProjectStore:
    return ProjectStore(settings=AppSettings(projects_root=tmp_path / "projects"))


def _completion(
    *,
    project_id: str = "p1",
    part_id: str = "part-1",
    chunk_id: int,
    duration_seconds: float,
    timestamp: str,
) -> object:
    return create_event_envelope(
        EVENT_VC_CHUNK_COMPLETED,
        project_id=project_id,
        part_id=part_id,
        chunk_id=chunk_id,
        payload={"duration_seconds": duration_seconds},
        timestamp=timestamp,
    )


def test_calculate_part_eta() -> None:
    assert calculate_part_eta(120.0, 480.0, 4) == 120.0 + 480.0 * 4


def test_remaining_vc_chunks_after_current() -> None:
    assert remaining_vc_chunks_after_current(7, 2, 1) == 4
    assert remaining_vc_chunks_after_current(7, 2, 0) == 5


def test_dedupe_vc_completion_durations_keeps_latest() -> None:
    events = [
        _completion(chunk_id=1, duration_seconds=480.0, timestamp="2026-01-01T10:00:00Z"),
        _completion(chunk_id=1, duration_seconds=60.0, timestamp="2026-01-01T11:00:00Z"),
        _completion(chunk_id=2, duration_seconds=540.0, timestamp="2026-01-01T10:30:00Z"),
        _completion(
            chunk_id=3,
            duration_seconds=999.0,
            timestamp="2026-01-01T12:00:00Z",
            project_id="other",
            part_id="other",
        ),
    ]
    result = dedupe_vc_completion_durations(events, project_id="p1", part_id="part-1")
    assert result == {1: 60.0, 2: 540.0}


def test_average_vc_chunk_duration_none_when_empty() -> None:
    assert (
        average_vc_chunk_duration([], project_id="p1", part_id="part-1") is None
    )


def test_average_vc_chunk_duration_from_deduped_events() -> None:
    events = [
        _completion(chunk_id=1, duration_seconds=480.0, timestamp="2026-01-01T10:00:00Z"),
        _completion(chunk_id=2, duration_seconds=600.0, timestamp="2026-01-01T11:00:00Z"),
    ]
    assert average_vc_chunk_duration(events, project_id="p1", part_id="part-1") == 540.0


def test_part_summary_exposes_vc_queued_and_processing(project_store) -> None:
    store = project_store
    store.create_project("eta-p", title="ETA")
    store.create_part("eta-p", part_id="part-a")
    store.create_chunk("eta-p", "part-a", 1)
    c1 = store.load_chunk("eta-p", "part-a", 1)
    c1.state = STATE_VC_QUEUED
    store.save_chunk("eta-p", "part-a", c1)
    store.create_chunk("eta-p", "part-a", 2)
    c2 = store.load_chunk("eta-p", "part-a", 2)
    c2.state = STATE_VC_PROCESSING
    store.save_chunk("eta-p", "part-a", c2)
    store.create_chunk("eta-p", "part-a", 3)
    c3 = store.load_chunk("eta-p", "part-a", 3)
    c3.state = STATE_VC_READY
    store.save_chunk("eta-p", "part-a", c3)

    summary = PartSummaryService(store).summarize("eta-p", "part-a")
    assert summary.vc_queued == 1
    assert summary.vc_processing == 1
    assert summary.vc_ready == 1
    assert summary.total_chunks == 3
