"""E6.2 pure lifecycle validation (no persistence)."""

from __future__ import annotations

from app.contracts.manifests import ChunkManifest
from app.contracts.states import (
    STATE_NARRATION_APPROVED,
    STATE_NARRATION_FAILED,
    STATE_NARRATION_READY,
    STATE_VC_APPROVED,
    STATE_VC_FAILED,
    STATE_VC_READY,
)


class LifecycleService:
    @staticmethod
    def can_approve_narration(chunk: ChunkManifest) -> bool:
        return chunk.state == STATE_NARRATION_READY

    @staticmethod
    def can_approve_vc(chunk: ChunkManifest) -> bool:
        return chunk.state == STATE_VC_READY

    @staticmethod
    def can_unapprove_narration(chunk: ChunkManifest) -> bool:
        return chunk.state == STATE_NARRATION_APPROVED

    @staticmethod
    def can_unapprove_vc(chunk: ChunkManifest) -> bool:
        return chunk.state == STATE_VC_APPROVED

    @staticmethod
    def can_queue_vc(chunk: ChunkManifest) -> bool:
        if chunk.state == STATE_NARRATION_APPROVED:
            return True
        return bool(chunk.narration_approved)

    @staticmethod
    def can_rebuild_narration(chunk: ChunkManifest) -> bool:
        return chunk.state in (
            STATE_NARRATION_READY,
            STATE_NARRATION_APPROVED,
            STATE_NARRATION_FAILED,
        )

    @staticmethod
    def can_rebuild_vc(chunk: ChunkManifest) -> bool:
        return chunk.state in (STATE_VC_READY, STATE_VC_APPROVED, STATE_VC_FAILED)
