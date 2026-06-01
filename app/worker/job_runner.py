"""E6.0 per-job execution — narration, VC, build."""

from __future__ import annotations

import logging
from pathlib import Path

from app.contracts.manifests import ChunkManifest
from app.contracts.queue import QueueItem
from app.contracts.states import (
    STATE_INTERRUPTED,
    STATE_NARRATION_APPROVED,
    STATE_NARRATION_PROCESSING,
    STATE_NARRATION_QUEUED,
    STATE_NARRATION_READY,
    STATE_VC_APPROVED,
    STATE_VC_PROCESSING,
    STATE_VC_QUEUED,
    STATE_VC_READY,
)
from app.services.build_service import BuildService
from app.services.narration_chunk_executor import NarrationChunkExecutor
from app.services.speaker_service import WorkerSpeakerService
from app.storage.project_store import ProjectStore

logger = logging.getLogger(__name__)

_NARRATION_ALLOWED = frozenset({STATE_NARRATION_QUEUED, STATE_INTERRUPTED})
_NARRATION_BLOCKED = frozenset(
    {STATE_NARRATION_READY, STATE_NARRATION_APPROVED, STATE_NARRATION_PROCESSING}
)
_VC_ALLOWED = frozenset({STATE_VC_QUEUED, STATE_INTERRUPTED})
_VC_BLOCKED = frozenset({STATE_VC_READY, STATE_VC_APPROVED, STATE_VC_PROCESSING})


class JobExecutionError(Exception):
    pass


class JobRunner:
    def __init__(
        self,
        store: ProjectStore,
        narration: NarrationChunkExecutor,
        speaker: WorkerSpeakerService,
        build_service: BuildService,
        *,
        event_bus=None,
    ) -> None:
        self._store = store
        self._narration = narration
        self._speaker = speaker
        self._build_service = build_service
        self._event_bus = event_bus

    def execute(self, job: QueueItem) -> None:
        if job.job_type == "narration":
            self._execute_narration(job)
        elif job.job_type == "vc":
            self._execute_vc(job)
        elif job.job_type == "build":
            self._execute_build(job)
        else:
            raise JobExecutionError(f"Unknown job_type: {job.job_type}")

    def _execute_narration(self, job: QueueItem) -> None:
        if job.chunk_id is None:
            raise JobExecutionError("narration job requires chunk_id")
        chunk = self._load_chunk_validated(
            job,
            allowed=_NARRATION_ALLOWED,
            blocked=_NARRATION_BLOCKED,
        )
        pl = self._store.part_layout(job.project_id, job.part_id)
        output_path = pl.narration_wav_path(job.chunk_id)

        chunk.state = STATE_NARRATION_PROCESSING
        self._store.save_chunk(job.project_id, job.part_id, chunk)

        self._narration.generate_chunk(
            project_id=job.project_id,
            part_id=job.part_id,
            chunk=chunk,
            output_path=output_path,
        )

        chunk = self._store.load_chunk(job.project_id, job.part_id, job.chunk_id)
        chunk.state = STATE_NARRATION_READY
        chunk.narration.file = f"narration/{output_path.name}"
        chunk.narration.status = "ready"
        self._store.save_chunk(job.project_id, job.part_id, chunk)

    def _execute_vc(self, job: QueueItem) -> None:
        if job.chunk_id is None:
            raise JobExecutionError("vc job requires chunk_id")
        chunk = self._load_chunk_validated(
            job,
            allowed=_VC_ALLOWED,
            blocked=_VC_BLOCKED,
        )
        pl = self._store.part_layout(job.project_id, job.part_id)
        narr_path = pl.narration_wav_path(job.chunk_id)
        if not narr_path.is_file():
            raise JobExecutionError(f"narration file missing for chunk {job.chunk_id}")

        chunk.state = STATE_VC_PROCESSING
        self._store.save_chunk(job.project_id, job.part_id, chunk)

        reference = self._resolve_reference_audio(job.project_id, job.part_id)
        output_path = pl.vc_wav_path(job.chunk_id)
        settings = {"diffusion_steps": 30}

        self._speaker.convert_chunk(
            narr_path,
            reference,
            output_path,
            settings=settings,
            project_id=job.project_id,
            part_id=job.part_id,
            chunk_id=job.chunk_id,
            event_bus=self._event_bus,
        )

        chunk = self._store.load_chunk(job.project_id, job.part_id, job.chunk_id)
        chunk.state = STATE_VC_READY
        chunk.vc.file = f"vc/{output_path.name}"
        chunk.vc.status = "ready"
        self._store.save_chunk(job.project_id, job.part_id, chunk)

    def _execute_build(self, job: QueueItem) -> None:
        build_id = job.job_id
        self._build_service.merge(job.project_id, job.part_id, build_id)

    def _load_chunk_validated(
        self,
        job: QueueItem,
        *,
        allowed: frozenset[str],
        blocked: frozenset[str],
    ) -> ChunkManifest:
        chunk = self._store.load_chunk(job.project_id, job.part_id, job.chunk_id)  # type: ignore[arg-type]
        if chunk.state in blocked:
            raise JobExecutionError(
                f"chunk {job.chunk_id} in non-runnable state {chunk.state}"
            )
        if chunk.state not in allowed:
            raise JobExecutionError(
                f"chunk {job.chunk_id} expected {sorted(allowed)}, got {chunk.state}"
            )
        return chunk

    def _resolve_reference_audio(self, project_id: str, part_id: str) -> Path:
        part = self._store.load_part(project_id, part_id)
        if part.processing_profile:
            candidate = self._store.resolve_part_path(
                project_id,
                part_id,
                part.processing_profile,
            )
            if candidate.is_file():
                return candidate
        pl = self._store.part_layout(project_id, part_id)
        default = pl.root / "reference.wav"
        if default.is_file():
            return default
        raise JobExecutionError(
            f"reference audio not found for {project_id}/{part_id}"
        )
