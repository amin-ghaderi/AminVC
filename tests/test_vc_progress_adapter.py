"""E5.0 — VC Progress Adapter."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.contracts.events import (
    EVENT_VC_CHUNK_COMPLETED,
    EVENT_VC_CHUNK_FAILED,
    EVENT_VC_CHUNK_STARTED,
    EVENT_VC_PROGRESS,
    EventEnvelope,
)
from app.events.bus import EventBus
from app.vc.estimation import estimate_remaining_seconds, progress_percent
from app.vc.progress_adapter import VcProgressAdapter, VcProgressError


class FakeClock:
    def __init__(self, start: datetime | None = None) -> None:
        self._current = start or datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self._current

    def advance(self, seconds: float) -> None:
        self._current = self._current + timedelta(seconds=seconds)


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


def _subscribe_all(bus: EventBus) -> list[EventEnvelope]:
    received: list[EventEnvelope] = []
    for event_type in (
        EVENT_VC_CHUNK_STARTED,
        EVENT_VC_PROGRESS,
        EVENT_VC_CHUNK_COMPLETED,
        EVENT_VC_CHUNK_FAILED,
    ):
        bus.subscribe(event_type, received.append)
    return received


@pytest.fixture
def adapter(event_bus: EventBus) -> VcProgressAdapter:
    clock = FakeClock()
    return VcProgressAdapter(
        project_id="book-1",
        part_id="part-001",
        event_bus=event_bus,
        total_steps=30,
        now=clock.now,
    ), clock


def test_chunk_start_event(adapter: tuple[VcProgressAdapter, FakeClock], event_bus: EventBus) -> None:
    vc, _clock = adapter
    received = _subscribe_all(event_bus)
    vc.start_chunk(17)
    assert len(received) == 1
    assert received[0].event_type == EVENT_VC_CHUNK_STARTED
    assert received[0].chunk_id == 17
    assert received[0].payload == {"chunk_id": 17}
    assert vc.session is not None
    assert vc.session.current_step == 0
    assert vc.session.total_steps == 30


def test_progress_event_emission(adapter: tuple[VcProgressAdapter, FakeClock], event_bus: EventBus) -> None:
    vc, clock = adapter
    received = _subscribe_all(event_bus)
    vc.start_chunk(17)
    clock.advance(10)
    vc.update_step(1)
    clock.advance(38)
    vc.update_step(12)
    progress = [e for e in received if e.event_type == EVENT_VC_PROGRESS]
    assert len(progress) == 2
    assert progress[0].payload["current_step"] == 1
    assert progress[1].payload["current_step"] == 12
    assert progress[1].payload["total_steps"] == 30


def test_no_duplicate_step_events(adapter: tuple[VcProgressAdapter, FakeClock], event_bus: EventBus) -> None:
    vc, _clock = adapter
    received = _subscribe_all(event_bus)
    vc.start_chunk(17)
    vc.update_step(5)
    vc.update_step(5)
    vc.update_step(5)
    progress = [e for e in received if e.event_type == EVENT_VC_PROGRESS]
    assert len(progress) == 1
    assert progress[0].payload["current_step"] == 5


def test_elapsed_time_calculation(adapter: tuple[VcProgressAdapter, FakeClock], event_bus: EventBus) -> None:
    vc, clock = adapter
    _subscribe_all(event_bus)
    vc.start_chunk(17)
    clock.advance(43)
    vc.update_step(12)
    assert vc.session is not None
    assert vc.session.current_step == 12


def test_remaining_time_estimation(adapter: tuple[VcProgressAdapter, FakeClock], event_bus: EventBus) -> None:
    vc, clock = adapter
    received = _subscribe_all(event_bus)
    vc.start_chunk(17)
    clock.advance(48)
    vc.update_step(12)
    progress = [e for e in received if e.event_type == EVENT_VC_PROGRESS][0]
    assert progress.payload["elapsed_seconds"] == 48.0
    assert progress.payload["estimated_remaining_seconds"] == 72.0
    assert estimate_remaining_seconds(12, 30, 48) == 72


def test_early_step_estimation_returns_zero(
    adapter: tuple[VcProgressAdapter, FakeClock],
    event_bus: EventBus,
) -> None:
    vc, clock = adapter
    received = _subscribe_all(event_bus)
    vc.start_chunk(17)
    clock.advance(5)
    vc.update_step(1)
    p1 = [e for e in received if e.event_type == EVENT_VC_PROGRESS][0]
    assert p1.payload["estimated_remaining_seconds"] == 0.0
    assert estimate_remaining_seconds(1, 30, int(p1.payload["elapsed_seconds"])) == 0


def test_chunk_completion_event(adapter: tuple[VcProgressAdapter, FakeClock], event_bus: EventBus) -> None:
    vc, clock = adapter
    received = _subscribe_all(event_bus)
    vc.start_chunk(17)
    clock.advance(125)
    duration = vc.complete_chunk()
    assert duration == 125.0
    completed = [e for e in received if e.event_type == EVENT_VC_CHUNK_COMPLETED][0]
    assert completed.payload["duration_seconds"] == 125.0
    assert vc.session is None


def test_chunk_failure_event(adapter: tuple[VcProgressAdapter, FakeClock], event_bus: EventBus) -> None:
    vc, _clock = adapter
    received = _subscribe_all(event_bus)
    vc.start_chunk(17)
    vc.update_step(3)
    vc.fail_chunk("oom")
    failed = [e for e in received if e.event_type == EVENT_VC_CHUNK_FAILED][0]
    assert failed.payload["error"] == "oom"
    assert vc.session is None


def test_event_ordering(adapter: tuple[VcProgressAdapter, FakeClock], event_bus: EventBus) -> None:
    vc, clock = adapter
    received = _subscribe_all(event_bus)
    vc.start_chunk(17)
    vc.update_step(1)
    clock.advance(1)
    vc.update_step(2)
    vc.complete_chunk()
    types = [e.event_type for e in received]
    assert types[0] == EVENT_VC_CHUNK_STARTED
    assert types[1] == EVENT_VC_PROGRESS
    assert types[2] == EVENT_VC_PROGRESS
    assert types[-1] == EVENT_VC_CHUNK_COMPLETED

    received.clear()
    vc2 = VcProgressAdapter(
        project_id="book-1",
        part_id="part-001",
        event_bus=event_bus,
        now=clock.now,
    )
    for event_type in (
        EVENT_VC_CHUNK_STARTED,
        EVENT_VC_PROGRESS,
        EVENT_VC_CHUNK_FAILED,
    ):
        event_bus.subscribe(event_type, received.append)
    vc2.start_chunk(18)
    vc2.update_step(1)
    vc2.fail_chunk("cuda error")
    types2 = [e.event_type for e in received if e.chunk_id == 18]
    assert types2[0] == EVENT_VC_CHUNK_STARTED
    assert EVENT_VC_PROGRESS in types2
    assert types2[-1] == EVENT_VC_CHUNK_FAILED


def test_event_bus_failure_isolation(event_bus: EventBus) -> None:
    clock = FakeClock()
    vc = VcProgressAdapter(
        project_id="book-1",
        part_id="part-001",
        event_bus=event_bus,
        now=clock.now,
    )
    vc.start_chunk(17)
    with patch.object(event_bus, "publish", side_effect=RuntimeError("bus down")):
        vc.update_step(1)
        vc.update_step(2)
        duration = vc.complete_chunk()
    assert duration == 0.0


def test_progress_percent_helper() -> None:
    assert progress_percent(12, 30) == 40.0


def test_active_session_required() -> None:
    vc = VcProgressAdapter(project_id="p", part_id="part-001", event_bus=None)
    with pytest.raises(VcProgressError):
        vc.update_step(1)


def test_no_event_bus_unchanged_execution() -> None:
    clock = FakeClock()
    vc = VcProgressAdapter(
        project_id="p",
        part_id="part-001",
        event_bus=None,
        now=clock.now,
    )
    vc.start_chunk(1)
    vc.update_step(1)
    clock.advance(10)
    assert vc.complete_chunk() == 10.0
