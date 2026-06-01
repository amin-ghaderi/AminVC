"""E4.0 — Event Bus."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from app.config.settings import AppSettings
from app.contracts.events import (
    EVENT_NARRATION_CHUNK_COMPLETED,
    EVENT_QUEUE_SNAPSHOT_UPDATED,
    EVENT_SYSTEM_WARNING,
    EVENT_VC_PROGRESS,
    MAX_EVENT_HISTORY,
    ChunkDurationPayload,
    EventEnvelope,
    QueueSnapshotPayload,
    VcProgressEvent,
    VcProgressPayload,
    create_event_envelope,
)
from app.contracts.queue import QueueSnapshot
from app.events.bus import EventBus
from app.events.store import EventStore


@pytest.fixture
def event_store(tmp_path: Path) -> EventStore:
    return EventStore(settings=AppSettings(events_root=tmp_path / "events"))


@pytest.fixture
def bus(event_store: EventStore) -> EventBus:
    return EventBus(store=event_store)


def test_subscribe(bus: EventBus) -> None:
    received: list[EventEnvelope] = []

    def handler(event: EventEnvelope) -> None:
        received.append(event)

    bus.subscribe(EVENT_VC_PROGRESS, handler)
    assert bus.subscriber_count(EVENT_VC_PROGRESS) == 1

    event = create_event_envelope(
        EVENT_VC_PROGRESS,
        project_id="p",
        part_id="part-001",
        chunk_id=1,
        payload=VcProgressPayload(1, 30, 0.0, 0.0).to_dict(),
    )
    bus.publish_now(event)
    assert len(received) == 1
    assert received[0].event_id == event.event_id


def test_unsubscribe(bus: EventBus) -> None:
    received: list[EventEnvelope] = []

    def handler(event: EventEnvelope) -> None:
        received.append(event)

    bus.subscribe(EVENT_VC_PROGRESS, handler)
    bus.unsubscribe(EVENT_VC_PROGRESS, handler)
    assert bus.subscriber_count(EVENT_VC_PROGRESS) == 0

    bus.publish_now(
        create_event_envelope(EVENT_VC_PROGRESS, payload=VcProgressPayload(0, 30, 0.0, 0.0).to_dict())
    )
    assert received == []


def test_publish_appends_history_and_dispatches(
    bus: EventBus,
    event_store: EventStore,
) -> None:
    received: list[EventEnvelope] = []
    bus.subscribe(EVENT_QUEUE_SNAPSHOT_UPDATED, lambda e: received.append(e))

    payload = QueueSnapshotPayload(1, 0, 2, 0, 1).to_dict()
    event = create_event_envelope(EVENT_QUEUE_SNAPSHOT_UPDATED, payload=payload)
    bus.publish(event)

    assert len(received) == 1
    assert len(event_store) == 1
    assert event_store.recent(1)[0].event_id == event.event_id


def test_multiple_subscribers(bus: EventBus) -> None:
    a: list[str] = []
    b: list[str] = []

    bus.subscribe(EVENT_VC_PROGRESS, lambda e: a.append(e.event_id))
    bus.subscribe(EVENT_VC_PROGRESS, lambda e: b.append(e.event_id))

    event = create_event_envelope(
        EVENT_VC_PROGRESS,
        payload=VcProgressPayload(2, 30, 1.0, 9.0).to_dict(),
    )
    bus.publish_now(event)
    assert a == [event.event_id]
    assert b == [event.event_id]


def test_subscriber_exception_isolation(bus: EventBus, caplog: pytest.LogCaptureFixture) -> None:
    received: list[EventEnvelope] = []

    def bad(_: EventEnvelope) -> None:
        raise RuntimeError("subscriber boom")

    def good(event: EventEnvelope) -> None:
        received.append(event)

    bus.subscribe(EVENT_VC_PROGRESS, bad)
    bus.subscribe(EVENT_VC_PROGRESS, good)

    with caplog.at_level(logging.ERROR):
        bus.publish_now(
            create_event_envelope(
                EVENT_VC_PROGRESS,
                payload=VcProgressPayload(0, 30, 0.0, 0.0).to_dict(),
            )
        )

    assert len(received) == 1
    assert any("subscriber failed" in r.message for r in caplog.records)


def test_event_history_append(event_store: EventStore, tmp_path: Path) -> None:
    event = create_event_envelope(
        EVENT_QUEUE_SNAPSHOT_UPDATED,
        payload=QueueSnapshotPayload(0, 0, 0, 0, 0).to_dict(),
    )
    event_store.append(event)
    assert len(event_store) == 1
    latest = tmp_path / "events" / "latest.jsonl"
    assert latest.is_file()
    line = latest.read_text(encoding="utf-8").strip()
    parsed = json.loads(line)
    assert parsed["event_id"] == event.event_id


def test_event_history_retention_limit() -> None:
    store = EventStore(max_events=5)
    for i in range(10):
        store.append(
            create_event_envelope(
                EVENT_VC_PROGRESS,
                payload={"current_step": i, "total_steps": 30, "elapsed_seconds": 0.0, "estimated_remaining_seconds": 0.0},
            )
        )
    assert len(store) == 5
    recent = store.recent(10)
    assert len(recent) == 5
    assert recent[0].payload["current_step"] == 5


def test_event_store_recent(event_store: EventStore) -> None:
    for i in range(3):
        event_store.append(
            create_event_envelope(
                EVENT_NARRATION_CHUNK_COMPLETED,
                chunk_id=i,
                payload=ChunkDurationPayload(float(i)).to_dict(),
            )
        )
    recent = event_store.recent(2)
    assert len(recent) == 2
    assert recent[-1].chunk_id == 2

    event_store.clear()
    assert len(event_store) == 0
    assert event_store.recent(10) == []


def test_event_envelope_creation() -> None:
    event = create_event_envelope(
        EVENT_NARRATION_CHUNK_COMPLETED,
        project_id="book-1",
        part_id="part-001",
        chunk_id=7,
        payload={"duration_seconds": 12.5},
    )
    assert event.event_id
    assert event.timestamp.endswith("+00:00") or "T" in event.timestamp
    data = event.to_dict()
    restored = EventEnvelope.from_dict(data)
    assert restored.project_id == "book-1"
    assert restored.chunk_id == 7

    with pytest.raises(ValueError):
        create_event_envelope("invalid.type", payload={})


def test_event_payload_integrity() -> None:
    snap = QueueSnapshot(queued=3, running=1, completed=2, failed=0, cancelled=4)
    payload = QueueSnapshotPayload(
        queued=snap.queued,
        running=snap.running,
        completed=snap.completed,
        failed=snap.failed,
        cancelled=snap.cancelled,
    )
    event = create_event_envelope(EVENT_QUEUE_SNAPSHOT_UPDATED, payload=payload.to_dict())
    restored = QueueSnapshotPayload.from_dict(event.payload)
    assert restored.queued == 3
    assert restored.cancelled == 4

    vc_e0 = VcProgressEvent(
        type="vc_progress",
        project_id="p",
        part_id="part-001",
        chunk_id=1,
        current_step=5,
        total_steps=30,
        elapsed_seconds=10.0,
        estimated_remaining_seconds=50.0,
    )
    vc_payload = VcProgressPayload.from_dict(vc_e0.to_vc_progress_payload())
    assert vc_payload.total_steps == 30

    narr = ChunkDurationPayload(42.0)
    event2 = create_event_envelope(
        EVENT_NARRATION_CHUNK_COMPLETED,
        payload=narr.to_dict(),
    )
    assert ChunkDurationPayload.from_dict(event2.payload).duration_seconds == 42.0


def test_wildcard_subscribe_rejected(bus: EventBus) -> None:
    with pytest.raises(ValueError):
        bus.subscribe("vc.*", lambda _: None)


def test_startup_empty_registry() -> None:
    fresh = EventBus()
    assert fresh.subscriber_count(EVENT_VC_PROGRESS) == 0
    assert len(fresh.store) == 0


def test_publish_now_skips_history(bus: EventBus, event_store: EventStore) -> None:
    bus.subscribe(EVENT_SYSTEM_WARNING, lambda _: None)
    bus.publish_now(create_event_envelope(EVENT_SYSTEM_WARNING, payload={"message": "x"}))
    assert len(event_store) == 0
