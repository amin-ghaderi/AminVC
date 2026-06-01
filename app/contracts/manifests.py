"""
Manifest contracts — E0 canonical schemas + Phase 1 engine-facing types.

E0 persisted manifests: ProjectManifest, PartManifest, ChunkManifest.
Do not rename entities or simplify schemas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.contracts.states import PROJECT_STATUS_ACTIVE, STATE_DRAFT


# ---------------------------------------------------------------------------
# Phase 1 — engine HTTP / aggregate contracts (not E0 filesystem layout)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class NarrationChunk:
    chunk_id: int
    text: str
    duration_estimate: float | None = None
    tts_audio_path: Path | None = None


@dataclass(frozen=True, slots=True)
class SpeakerChunk:
    chunk_id: int
    source_audio_path: Path
    speaker_audio_path: Path | None = None


@dataclass(frozen=True, slots=True)
class ChunkListManifest:
    """Phase 1 aggregate chunk list (not the E0 per-chunk `chunks/0001.json`)."""

    project_id: str
    chunks: list[NarrationChunk]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class NarrationManifest:
    project_id: str
    intake_id: str | None
    chunk_audio_paths: list[Path] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SpeakerManifest:
    project_id: str
    reference_audio_path: Path | None = None
    converted_audio_paths: list[Path] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# E0 — canonical filesystem manifests
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class AssetSlot:
    """Narration or VC asset slot inside ChunkManifest."""

    status: str = ""
    file: str | None = None
    duration_seconds: float | None = None


@dataclass(slots=True)
class ProjectManifest:
    """
    Location: `{project_id}/project.json`

    Required E0 fields only.
    """

    project_id: str
    title: str = ""
    created_at: str = ""
    updated_at: str = ""
    status: str = PROJECT_STATUS_ACTIVE
    parts: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PartManifest:
    """
    Location: `parts/part-XXX/manifest.json`
    """

    part_id: str
    project_id: str
    title: str = ""
    state: str = STATE_DRAFT
    processing_profile: str = ""
    chunks_total: int = 0
    chunks_completed_narration: int = 0
    chunks_completed_vc: int = 0
    current_chunk: int | None = None
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class ChunkManifest:
    """
    Location: `parts/part-XXX/chunks/0001.json`
    """

    chunk_id: int
    state: str = STATE_DRAFT
    narration_approved: bool = False
    vc_approved: bool = False
    text: str = ""
    narration: AssetSlot = field(default_factory=AssetSlot)
    vc: AssetSlot = field(default_factory=AssetSlot)
    retry_count: int = 0
    last_error: str | None = None
    updated_at: str = ""


@dataclass(slots=True)
class BuildManifest:
    """
    User-created merged output (permanent asset).

    Location (deterministic filename):
      `builds/build-XXX.json` under project or part tree.
    """

    build_id: str
    project_id: str
    part_id: str
    name: str = ""
    created_at: str = ""
    updated_at: str = ""
    chunks: list[int] = field(default_factory=list)
    output_file: str = ""
    duration_seconds: float | None = None
