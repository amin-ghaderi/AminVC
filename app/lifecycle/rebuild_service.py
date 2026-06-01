"""E6.2 narration/VC rebuild and text-edit invalidation."""

from __future__ import annotations

from app.contracts.manifests import ChunkManifest
from app.contracts.states import (
    STATE_NARRATION_APPROVED,
    STATE_NARRATION_QUEUED,
    STATE_NARRATION_READY,
    STATE_VC_APPROVED,
    STATE_VC_QUEUED,
    STATE_VC_READY,
)
from app.events.bus import EventBus
from app.lifecycle.events import (
    publish_narration_rebuild_requested,
    publish_vc_rebuild_requested,
)
from app.lifecycle.exceptions import InvalidStateTransitionError
from app.lifecycle.lifecycle_service import LifecycleService
from app.storage.project_store import ProjectStore

_INVALIDATE_ON_TEXT_CHANGE = frozenset(
    {
        STATE_NARRATION_READY,
        STATE_NARRATION_APPROVED,
        STATE_VC_READY,
        STATE_VC_APPROVED,
    }
)


class RebuildService:
    def __init__(
        self,
        store: ProjectStore,
        *,
        event_bus: EventBus | None = None,
    ) -> None:
        self._store = store
        self._event_bus = event_bus

    def request_narration_rebuild(
        self,
        project_id: str,
        part_id: str,
        chunk_id: int,
    ) -> ChunkManifest:
        chunk = self._store.load_chunk(project_id, part_id, chunk_id)
        if not LifecycleService.can_rebuild_narration(chunk):
            raise InvalidStateTransitionError(
                f"cannot request narration rebuild from state {chunk.state!r}"
            )
        chunk.state = STATE_NARRATION_QUEUED
        chunk.narration_approved = False
        self._store.save_chunk(project_id, part_id, chunk)
        publish_narration_rebuild_requested(
            self._event_bus,
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk_id,
        )
        return chunk

    def request_vc_rebuild(
        self,
        project_id: str,
        part_id: str,
        chunk_id: int,
    ) -> ChunkManifest:
        chunk = self._store.load_chunk(project_id, part_id, chunk_id)
        if not LifecycleService.can_rebuild_vc(chunk):
            raise InvalidStateTransitionError(
                f"cannot request VC rebuild from state {chunk.state!r}"
            )
        chunk.state = STATE_VC_QUEUED
        chunk.vc_approved = False
        self._store.save_chunk(project_id, part_id, chunk)
        publish_vc_rebuild_requested(
            self._event_bus,
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk_id,
        )
        return chunk

    def update_chunk_text(
        self,
        project_id: str,
        part_id: str,
        chunk_id: int,
        text: str,
    ) -> ChunkManifest:
        chunk = self._store.load_chunk(project_id, part_id, chunk_id)
        new_text = text.strip() if text else ""
        if new_text == (chunk.text or "").strip():
            chunk.text = new_text
            self._store.save_chunk(project_id, part_id, chunk)
            return chunk

        chunk.text = new_text
        if chunk.state in _INVALIDATE_ON_TEXT_CHANGE:
            chunk.state = STATE_NARRATION_QUEUED
            chunk.narration_approved = False
            chunk.vc_approved = False

        self._store.save_chunk(project_id, part_id, chunk)
        return chunk
