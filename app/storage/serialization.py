"""E0 manifest JSON serialization (exact field names)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.contracts.manifests import (
    AssetSlot,
    BuildManifest,
    ChunkManifest,
    PartManifest,
    ProjectManifest,
)
from app.contracts.states import VALID_CHUNK_STATES, VALID_PART_STATES


class InvalidStateError(ValueError):
    pass


class InvalidBuildManifestError(ValueError):
    pass


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _asset_to_dict(slot: AssetSlot) -> dict[str, Any]:
    return {
        "status": slot.status,
        "file": slot.file,
        "duration_seconds": slot.duration_seconds,
    }


def _asset_from_dict(data: dict[str, Any] | None) -> AssetSlot:
    if not data:
        return AssetSlot()
    return AssetSlot(
        status=str(data.get("status", "")),
        file=data.get("file"),
        duration_seconds=data.get("duration_seconds"),
    )


def project_to_dict(manifest: ProjectManifest) -> dict[str, Any]:
    return {
        "project_id": manifest.project_id,
        "title": manifest.title,
        "created_at": manifest.created_at,
        "updated_at": manifest.updated_at,
        "status": manifest.status,
        "parts": list(manifest.parts),
    }


def project_from_dict(data: dict[str, Any]) -> ProjectManifest:
    return ProjectManifest(
        project_id=str(data["project_id"]),
        title=str(data.get("title", "")),
        created_at=str(data.get("created_at", "")),
        updated_at=str(data.get("updated_at", "")),
        status=str(data.get("status", "active")),
        parts=[str(p) for p in data.get("parts", [])],
    )


def part_to_dict(manifest: PartManifest) -> dict[str, Any]:
    return {
        "part_id": manifest.part_id,
        "project_id": manifest.project_id,
        "title": manifest.title,
        "state": manifest.state,
        "processing_profile": manifest.processing_profile,
        "chunks_total": manifest.chunks_total,
        "chunks_completed_narration": manifest.chunks_completed_narration,
        "chunks_completed_vc": manifest.chunks_completed_vc,
        "current_chunk": manifest.current_chunk,
        "created_at": manifest.created_at,
        "updated_at": manifest.updated_at,
    }


def part_from_dict(data: dict[str, Any]) -> PartManifest:
    current = data.get("current_chunk")
    return PartManifest(
        part_id=str(data["part_id"]),
        project_id=str(data["project_id"]),
        title=str(data.get("title", "")),
        state=str(data.get("state", "Draft")),
        processing_profile=str(data.get("processing_profile", "")),
        chunks_total=int(data.get("chunks_total", 0)),
        chunks_completed_narration=int(data.get("chunks_completed_narration", 0)),
        chunks_completed_vc=int(data.get("chunks_completed_vc", 0)),
        current_chunk=int(current) if current is not None else None,
        created_at=str(data.get("created_at", "")),
        updated_at=str(data.get("updated_at", "")),
    )


def chunk_to_dict(manifest: ChunkManifest) -> dict[str, Any]:
    return {
        "chunk_id": manifest.chunk_id,
        "state": manifest.state,
        "narration_approved": manifest.narration_approved,
        "vc_approved": manifest.vc_approved,
        "text": manifest.text,
        "narration": _asset_to_dict(manifest.narration),
        "vc": _asset_to_dict(manifest.vc),
        "retry_count": manifest.retry_count,
        "last_error": manifest.last_error,
        "updated_at": manifest.updated_at,
    }


def chunk_from_dict(data: dict[str, Any]) -> ChunkManifest:
    return ChunkManifest(
        chunk_id=int(data["chunk_id"]),
        state=str(data.get("state", "Draft")),
        narration_approved=bool(data.get("narration_approved", False)),
        vc_approved=bool(data.get("vc_approved", False)),
        text=str(data.get("text", "")),
        narration=_asset_from_dict(data.get("narration")),
        vc=_asset_from_dict(data.get("vc")),
        retry_count=int(data.get("retry_count", 0)),
        last_error=data.get("last_error"),
        updated_at=str(data.get("updated_at", "")),
    )


def validate_chunk_state(state: str) -> None:
    if state not in VALID_CHUNK_STATES:
        raise InvalidStateError(f"Invalid chunk state: {state!r}")


def validate_part_state(state: str) -> None:
    if state not in VALID_PART_STATES:
        raise InvalidStateError(f"Invalid part state: {state!r}")


def build_to_dict(manifest: BuildManifest) -> dict[str, Any]:
    return {
        "build_id": manifest.build_id,
        "project_id": manifest.project_id,
        "part_id": manifest.part_id,
        "name": manifest.name,
        "created_at": manifest.created_at,
        "updated_at": manifest.updated_at,
        "chunks": list(manifest.chunks),
        "output_file": manifest.output_file,
        "duration_seconds": manifest.duration_seconds,
    }


def build_from_dict(data: dict[str, Any]) -> BuildManifest:
    return BuildManifest(
        build_id=str(data["build_id"]),
        project_id=str(data["project_id"]),
        part_id=str(data["part_id"]),
        name=str(data.get("name", "")),
        created_at=str(data.get("created_at", "")),
        updated_at=str(data.get("updated_at", "")),
        chunks=[int(x) for x in data.get("chunks", [])],
        output_file=str(data.get("output_file", "")),
        duration_seconds=data.get("duration_seconds"),
    )


def validate_build_manifest(manifest: BuildManifest) -> None:
    if not manifest.build_id.strip():
        raise InvalidBuildManifestError("build_id must be non-empty")
    if not manifest.project_id.strip():
        raise InvalidBuildManifestError("project_id must be non-empty")
    if not manifest.part_id.strip():
        raise InvalidBuildManifestError("part_id must be non-empty")
