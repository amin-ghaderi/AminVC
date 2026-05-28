"""
Manifest contracts (Phase 1).

These are the app-owned data contracts that describe *what exists* in storage.
In Phase 1 we define only schemas/types, not IO.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class NarrationChunk:
    """
    Contract v1 NarrationChunk.

    Notes:
    - `duration_estimate` is a contract field but is not computed in Phase 1.
    - `tts_audio_path` is a *path reference* only; creation is out of scope.
    """

    chunk_id: int
    text: str
    duration_estimate: float | None = None
    tts_audio_path: Path | None = None


@dataclass(frozen=True, slots=True)
class SpeakerChunk:
    """Contract v1 SpeakerChunk mapping: preserves chunk_id and file mapping."""

    chunk_id: int
    source_audio_path: Path
    speaker_audio_path: Path | None = None


@dataclass(frozen=True, slots=True)
class ChunkManifest:
    """
    Ordered chunk list for a project.

    Phase 1: schema only.
    """

    project_id: str
    chunks: list[NarrationChunk]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class NarrationManifest:
    """Describes narration artifacts produced for a project (schema only)."""

    project_id: str
    intake_id: str | None
    chunk_audio_paths: list[Path] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SpeakerManifest:
    """Describes speaker conversion artifacts produced for a project (schema only)."""

    project_id: str
    reference_audio_path: Path | None = None
    converted_audio_paths: list[Path] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


class ManifestService:
    """
    Contract-only service for creating/validating manifests.

    Phase 1: no persistence and no filesystem IO. Phase 2+ may add read/write.
    """

    def build_chunk_manifest(self, *args: Any, **kwargs: Any) -> ChunkManifest:
        raise NotImplementedError

    def build_narration_manifest(self, *args: Any, **kwargs: Any) -> NarrationManifest:
        raise NotImplementedError

    def build_speaker_manifest(self, *args: Any, **kwargs: Any) -> SpeakerManifest:
        raise NotImplementedError

