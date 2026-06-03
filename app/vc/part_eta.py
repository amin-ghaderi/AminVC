"""E9.2-B — Part-level VC ETA from recent completion events (no persistence)."""

from __future__ import annotations

from app.contracts.events import EVENT_VC_CHUNK_COMPLETED, EventEnvelope


def calculate_part_eta(
    current_chunk_remaining: float,
    avg_chunk_duration: float,
    remaining_chunks: int,
) -> float:
    """
    ETA_total = current_chunk_remaining + (avg_chunk_duration × remaining_chunks).
    """
    if remaining_chunks < 0:
        remaining_chunks = 0
    return current_chunk_remaining + avg_chunk_duration * remaining_chunks


def remaining_vc_chunks_after_current(
    total_chunks: int,
    vc_ready: int,
    vc_processing: int,
) -> int:
    """Chunks still to convert after the in-flight chunk finishes."""
    if vc_processing > 0:
        return max(0, total_chunks - vc_ready - 1)
    return max(0, total_chunks - vc_ready)


def dedupe_vc_completion_durations(
    events: list[EventEnvelope],
    *,
    project_id: str,
    part_id: str,
) -> dict[int, float]:
    """Latest vc.chunk_completed duration per chunk_id for a part."""
    latest: dict[int, tuple[str, float]] = {}
    for event in events:
        if event.event_type != EVENT_VC_CHUNK_COMPLETED:
            continue
        if event.project_id != project_id or event.part_id != part_id:
            continue
        if event.chunk_id is None:
            continue
        raw = event.payload.get("duration_seconds")
        if raw is None:
            continue
        duration = float(raw)
        chunk_id = int(event.chunk_id)
        prev = latest.get(chunk_id)
        if prev is None or event.timestamp > prev[0]:
            latest[chunk_id] = (event.timestamp, duration)
    return {cid: duration for cid, (_, duration) in latest.items()}


def average_vc_chunk_duration(
    events: list[EventEnvelope],
    *,
    project_id: str,
    part_id: str,
) -> float | None:
    """Mean duration from deduped vc.chunk_completed events; None if no samples."""
    durations = list(
        dedupe_vc_completion_durations(
            events, project_id=project_id, part_id=part_id
        ).values()
    )
    if not durations:
        return None
    return sum(durations) / len(durations)
