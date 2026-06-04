"""E9.2-C — VC internal segment progress propagation."""

from __future__ import annotations

from app.contracts.events import EVENT_VC_PROGRESS
from app.contracts.worker_messages import ProgressResponse, parse_progress
from app.events.bus import EventBus
from app.vc.bridge import VcProgressBridge
from app.vc.progress_adapter import VcProgressAdapter


def test_parse_progress_segment_fields() -> None:
    progress = parse_progress(
        {
            "type": "progress",
            "chunk_id": 3,
            "current_step": 11,
            "total_steps": 30,
            "segment_index": 3,
            "segment_total": 8,
        }
    )
    assert progress.segment_index == 3
    assert progress.segment_total == 8


def test_parse_progress_segment_backward_compat() -> None:
    progress = parse_progress(
        {"type": "progress", "chunk_id": 1, "current_step": 5, "total_steps": 30}
    )
    assert progress.segment_index == 0
    assert progress.segment_total == 0


def test_adapter_emits_segment_fields_on_progress() -> None:
    bus = EventBus()
    received: list = []
    bus.subscribe(EVENT_VC_PROGRESS, received.append)
    adapter = VcProgressAdapter(
        project_id="p1",
        part_id="part-a",
        event_bus=bus,
        total_steps=30,
    )
    adapter.start_chunk(2)
    adapter.update_progress(11, 30, segment_index=3, segment_total=8)
    assert len(received) == 1
    payload = received[0].payload
    assert payload["current_step"] == 11
    assert payload["segment_index"] == 3
    assert payload["segment_total"] == 8


def test_bridge_forwards_segment_on_step_reset() -> None:
    adapter = VcProgressAdapter(
        project_id="p1",
        part_id="part-a",
        event_bus=None,
        total_steps=30,
    )
    adapter.start_chunk(2)
    bridge = VcProgressBridge(adapter)
    bridge.on_progress_message(
        ProgressResponse(
            chunk_id=2,
            current_step=30,
            total_steps=30,
            segment_index=1,
            segment_total=3,
        )
    )
    bridge.on_progress_message(
        ProgressResponse(
            chunk_id=2,
            current_step=1,
            total_steps=30,
            segment_index=2,
            segment_total=3,
        )
    )
    session = adapter.session
    assert session is not None
    assert session.current_step == 1
    assert session.segment_index == 2
    assert session.segment_total == 3


def _count_default_vc_segments(
    cond_len: int,
    max_source_window: int,
    overlap_frame_len: int,
) -> int:
    """Mirror speaker-engine/modules/v2/vc_wrapper.count_default_vc_segments."""
    if cond_len <= 0:
        return 1
    count = 0
    processed_frames = 0
    while processed_frames < cond_len:
        count += 1
        if processed_frames + max_source_window >= cond_len:
            break
        chunk_frames = min(max_source_window, cond_len - processed_frames)
        advance = chunk_frames - overlap_frame_len
        if advance <= 0:
            advance = chunk_frames if chunk_frames > 0 else 1
        processed_frames += advance
    return max(1, count)


def test_count_default_vc_segments_helper() -> None:
    assert _count_default_vc_segments(100, 40, 5) >= 2
    assert _count_default_vc_segments(10, 100, 5) == 1
    assert max(1, (2500 + 1000 - 1) // 1000) == 3
    assert max(1, (500 + 1000 - 1) // 1000) == 1
