"""Shared helpers for tests that enqueue VC jobs (E6.2 approval gate)."""

from __future__ import annotations

from app.contracts.states import STATE_NARRATION_APPROVED
from app.storage.project_store import ProjectStore


def mark_narration_approved_for_vc(
    store: ProjectStore,
    project_id: str,
    part_id: str,
    chunk_id: int,
) -> None:
    chunk = store.load_chunk(project_id, part_id, chunk_id)
    chunk.state = STATE_NARRATION_APPROVED
    chunk.narration_approved = True
    store.save_chunk(project_id, part_id, chunk)
