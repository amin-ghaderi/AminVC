"""E7.1 — Part-level progress metrics (computed, not persisted)."""

from __future__ import annotations

from dataclasses import dataclass

from app.contracts.states import (
    STATE_INTERRUPTED,
    STATE_NARRATION_APPROVED,
    STATE_NARRATION_FAILED,
    STATE_NARRATION_READY,
    STATE_VC_APPROVED,
    STATE_VC_FAILED,
    STATE_VC_READY,
)
from app.storage.project_store import ProjectStore


@dataclass(frozen=True, slots=True)
class PartSummary:
    total_chunks: int
    narration_ready: int
    narration_approved: int
    vc_ready: int
    vc_approved: int
    failed: int
    interrupted: int


class PartSummaryService:
    def __init__(self, store: ProjectStore) -> None:
        self._store = store

    def summarize(self, project_id: str, part_id: str) -> PartSummary:
        self._store.load_part(project_id, part_id)
        chunks = self._store.list_chunks(project_id, part_id)
        narration_ready = 0
        narration_approved = 0
        vc_ready = 0
        vc_approved = 0
        failed = 0
        interrupted = 0

        for chunk in chunks:
            if chunk.state in (STATE_NARRATION_READY, STATE_NARRATION_APPROVED):
                narration_ready += 1
            if chunk.state == STATE_NARRATION_APPROVED or chunk.narration_approved:
                narration_approved += 1
            if chunk.state in (STATE_VC_READY, STATE_VC_APPROVED):
                vc_ready += 1
            if chunk.state == STATE_VC_APPROVED or chunk.vc_approved:
                vc_approved += 1
            if chunk.state in (STATE_NARRATION_FAILED, STATE_VC_FAILED):
                failed += 1
            if chunk.state == STATE_INTERRUPTED:
                interrupted += 1

        return PartSummary(
            total_chunks=len(chunks),
            narration_ready=narration_ready,
            narration_approved=narration_approved,
            vc_ready=vc_ready,
            vc_approved=vc_approved,
            failed=failed,
            interrupted=interrupted,
        )
