"""Map domain manifests to API response models."""

from __future__ import annotations

from app.api.schemas.common import (
    AssetSlotResponse,
    BuildResponse,
    ChunkResponse,
    EventEnvelopeResponse,
    PartResponse,
    ProjectResponse,
    ReferenceAudioResponse,
)
from app.services.reference_audio_service import ReferenceAudioMetadata
from app.contracts.events import EventEnvelope
from app.contracts.manifests import (
    AssetSlot,
    BuildManifest,
    ChunkManifest,
    PartManifest,
    ProjectManifest,
)
from app.contracts.queue import QueueItem, QueueSnapshot


def project_response(manifest: ProjectManifest) -> ProjectResponse:
    return ProjectResponse(
        project_id=manifest.project_id,
        title=manifest.title,
        created_at=manifest.created_at,
        updated_at=manifest.updated_at,
        status=manifest.status,
        parts=list(manifest.parts),
    )


def reference_audio_response(meta: ReferenceAudioMetadata) -> ReferenceAudioResponse:
    return ReferenceAudioResponse(
        exists=meta.exists,
        path=meta.path,
        size_bytes=meta.size_bytes,
    )


def part_response(
    manifest: PartManifest,
    *,
    reference_audio: ReferenceAudioMetadata,
) -> PartResponse:
    return PartResponse(
        part_id=manifest.part_id,
        project_id=manifest.project_id,
        title=manifest.title,
        state=manifest.state,
        processing_profile=manifest.processing_profile,
        reference_audio=reference_audio_response(reference_audio),
        chunks_total=manifest.chunks_total,
        chunks_completed_narration=manifest.chunks_completed_narration,
        chunks_completed_vc=manifest.chunks_completed_vc,
        current_chunk=manifest.current_chunk,
        created_at=manifest.created_at,
        updated_at=manifest.updated_at,
    )


def asset_response(slot: AssetSlot) -> AssetSlotResponse:
    return AssetSlotResponse(
        status=slot.status,
        file=slot.file,
        duration_seconds=slot.duration_seconds,
    )


def chunk_response(manifest: ChunkManifest) -> ChunkResponse:
    return ChunkResponse(
        chunk_id=manifest.chunk_id,
        state=manifest.state,
        narration_approved=manifest.narration_approved,
        vc_approved=manifest.vc_approved,
        text=manifest.text,
        narration=asset_response(manifest.narration),
        vc=asset_response(manifest.vc),
        retry_count=manifest.retry_count,
        last_error=manifest.last_error,
        updated_at=manifest.updated_at,
    )


def build_response(manifest: BuildManifest) -> BuildResponse:
    return BuildResponse(
        build_id=manifest.build_id,
        project_id=manifest.project_id,
        part_id=manifest.part_id,
        name=manifest.name,
        created_at=manifest.created_at,
        updated_at=manifest.updated_at,
        chunks=list(manifest.chunks),
        output_file=manifest.output_file,
        duration_seconds=manifest.duration_seconds,
    )


def queue_snapshot_response(snapshot: QueueSnapshot) -> dict[str, int]:
    return {
        "queued": snapshot.queued,
        "running": snapshot.running,
        "completed": snapshot.completed,
        "failed": snapshot.failed,
        "cancelled": snapshot.cancelled,
    }


def queue_job_response(item: QueueItem) -> dict[str, object]:
    return {
        "job_id": item.job_id,
        "project_id": item.project_id,
        "part_id": item.part_id,
        "chunk_id": item.chunk_id,
        "job_type": item.job_type,
        "status": item.status,
    }


def event_response(envelope: EventEnvelope) -> EventEnvelopeResponse:
    return EventEnvelopeResponse(
        event_id=envelope.event_id,
        event_type=envelope.event_type,
        timestamp=envelope.timestamp,
        project_id=envelope.project_id,
        part_id=envelope.part_id,
        chunk_id=envelope.chunk_id,
        payload=dict(envelope.payload),
    )
