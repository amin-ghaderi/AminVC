"""E6.2 narration and VC approval workflow."""

from __future__ import annotations

from app.contracts.manifests import ChunkManifest
from app.contracts.states import (
    STATE_NARRATION_APPROVED,
    STATE_NARRATION_READY,
    STATE_VC_APPROVED,
    STATE_VC_READY,
)
from app.events.bus import EventBus
from app.lifecycle.events import (
    publish_narration_approved,
    publish_narration_unapproved,
    publish_vc_approved,
    publish_vc_unapproved,
)
from app.lifecycle.exceptions import InvalidStateTransitionError
from app.lifecycle.lifecycle_service import LifecycleService
from app.storage.project_store import ProjectStore


class ApprovalService:
    def __init__(
        self,
        store: ProjectStore,
        *,
        event_bus: EventBus | None = None,
    ) -> None:
        self._store = store
        self._event_bus = event_bus

    def approve_narration(
        self,
        project_id: str,
        part_id: str,
        chunk_id: int,
    ) -> ChunkManifest:
        chunk = self._store.load_chunk(project_id, part_id, chunk_id)
        if not LifecycleService.can_approve_narration(chunk):
            raise InvalidStateTransitionError(
                f"cannot approve narration from state {chunk.state!r}"
            )
        chunk.state = STATE_NARRATION_APPROVED
        chunk.narration_approved = True
        self._store.save_chunk(project_id, part_id, chunk)
        publish_narration_approved(
            self._event_bus,
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk_id,
        )
        return chunk

    def approve_vc(
        self,
        project_id: str,
        part_id: str,
        chunk_id: int,
    ) -> ChunkManifest:
        chunk = self._store.load_chunk(project_id, part_id, chunk_id)
        if not LifecycleService.can_approve_vc(chunk):
            raise InvalidStateTransitionError(
                f"cannot approve VC from state {chunk.state!r}"
            )
        chunk.state = STATE_VC_APPROVED
        chunk.vc_approved = True
        self._store.save_chunk(project_id, part_id, chunk)
        publish_vc_approved(
            self._event_bus,
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk_id,
        )
        return chunk

    def unapprove_narration(
        self,
        project_id: str,
        part_id: str,
        chunk_id: int,
    ) -> ChunkManifest:
        chunk = self._store.load_chunk(project_id, part_id, chunk_id)
        if not LifecycleService.can_unapprove_narration(chunk):
            raise InvalidStateTransitionError(
                f"cannot unapprove narration from state {chunk.state!r}"
            )
        chunk.state = STATE_NARRATION_READY
        chunk.narration_approved = False
        self._store.save_chunk(project_id, part_id, chunk)
        publish_narration_unapproved(
            self._event_bus,
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk_id,
        )
        return chunk

    def unapprove_vc(
        self,
        project_id: str,
        part_id: str,
        chunk_id: int,
    ) -> ChunkManifest:
        chunk = self._store.load_chunk(project_id, part_id, chunk_id)
        if not LifecycleService.can_unapprove_vc(chunk):
            raise InvalidStateTransitionError(
                f"cannot unapprove VC from state {chunk.state!r}"
            )
        chunk.state = STATE_VC_READY
        chunk.vc_approved = False
        self._store.save_chunk(project_id, part_id, chunk)
        publish_vc_unapproved(
            self._event_bus,
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk_id,
        )
        return chunk
