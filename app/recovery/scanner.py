"""
RecoveryScanner — inspect manifests and files; apply Interrupted transitions.
"""

from __future__ import annotations

from pathlib import Path

from app.contracts.manifests import ChunkManifest
from app.contracts.recovery import ChunkScanResult, PartScanResult, ProjectScanResult, RecoveryCategory
from app.contracts.recovery_rules import (
    chunk_pipeline_completed,
    detect_interrupted_narration,
    detect_interrupted_vc,
)
from app.contracts.states import (
    STATE_DRAFT,
    STATE_INTERRUPTED,
    STATE_NARRATION_FAILED,
    STATE_NARRATION_PROCESSING,
    STATE_NARRATION_QUEUED,
    STATE_TEXT_SAVED,
    STATE_VC_FAILED,
    STATE_VC_PROCESSING,
    STATE_VC_QUEUED,
)
from app.events.bus import EventBus
from app.recovery.events import publish_interrupted_detected
from app.storage.project_store import ProjectStore

_PENDING_STATES = frozenset(
    {
        STATE_DRAFT,
        STATE_TEXT_SAVED,
        STATE_NARRATION_QUEUED,
        STATE_VC_QUEUED,
    }
)
_FAILED_STATES = frozenset({STATE_NARRATION_FAILED, STATE_VC_FAILED})


class RecoveryScanner:
    def __init__(
        self,
        store: ProjectStore,
        event_bus: EventBus | None = None,
    ) -> None:
        self._store = store
        self._event_bus = event_bus

    def scan_project(self, project_id: str) -> ProjectScanResult:
        project = self._store.load_project(project_id)
        parts: list[PartScanResult] = []
        for part_id in project.parts:
            parts.append(self.scan_part(project_id, part_id))
        return ProjectScanResult(project_id=project_id, parts=parts)

    def scan_part(self, project_id: str, part_id: str) -> PartScanResult:
        self._store.load_part(project_id, part_id)
        chunks = self._store.list_chunks(project_id, part_id)
        results: list[ChunkScanResult] = []
        for chunk in chunks:
            results.append(self.scan_chunk(project_id, part_id, chunk.chunk_id))
        builds = [b.build_id for b in self._store.list_builds(project_id, part_id)]
        builds.extend(
            b.build_id
            for b in self._store.list_builds(project_id, part_id, level="project")
        )
        return PartScanResult(
            project_id=project_id,
            part_id=part_id,
            chunks=results,
            builds_detected=sorted(set(builds)),
        )

    def scan_chunk(
        self,
        project_id: str,
        part_id: str,
        chunk_id: int,
    ) -> ChunkScanResult:
        chunk = self._store.load_chunk(project_id, part_id, chunk_id)
        narration_path, vc_path = self._asset_paths(project_id, part_id, chunk)

        if detect_interrupted_narration(chunk, narration_path):
            prior_state = chunk.state
            chunk.state = STATE_INTERRUPTED
            self._store.save_chunk(project_id, part_id, chunk)
            if prior_state == STATE_NARRATION_PROCESSING:
                publish_interrupted_detected(
                    self._event_bus,
                    project_id=project_id,
                    part_id=part_id,
                    chunk_id=chunk.chunk_id,
                    state=prior_state,
                )
        elif detect_interrupted_vc(chunk, vc_path):
            prior_state = chunk.state
            chunk.state = STATE_INTERRUPTED
            self._store.save_chunk(project_id, part_id, chunk)
            if prior_state == STATE_VC_PROCESSING:
                publish_interrupted_detected(
                    self._event_bus,
                    project_id=project_id,
                    part_id=part_id,
                    chunk_id=chunk.chunk_id,
                    state=prior_state,
                )

        category = self._classify(chunk, narration_path, vc_path)
        return ChunkScanResult(
            chunk_id=chunk.chunk_id,
            category=category,
            state=chunk.state,
            retry_count=chunk.retry_count,
        )

    def _classify(
        self,
        chunk: ChunkManifest,
        narration_path: Path,
        vc_path: Path,
    ) -> RecoveryCategory:
        if chunk.state in _FAILED_STATES:
            return RecoveryCategory.FAILED
        if chunk.state == STATE_INTERRUPTED:
            return RecoveryCategory.INTERRUPTED
        if chunk_pipeline_completed(chunk, narration_path, vc_path):
            return RecoveryCategory.COMPLETED
        if chunk.state in _PENDING_STATES:
            return RecoveryCategory.PENDING
        return RecoveryCategory.HEALTHY

    def _asset_paths(
        self,
        project_id: str,
        part_id: str,
        chunk: ChunkManifest,
    ) -> tuple[Path, Path]:
        pl = self._store.part_layout(project_id, part_id)
        narration = (
            self._store.resolve_part_path(project_id, part_id, chunk.narration.file)
            if chunk.narration.file
            else pl.narration_wav_path(chunk.chunk_id)
        )
        vc = (
            self._store.resolve_part_path(project_id, part_id, chunk.vc.file)
            if chunk.vc.file
            else pl.vc_wav_path(chunk.chunk_id)
        )
        return narration, vc
