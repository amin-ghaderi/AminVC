"""
Manifest contracts (Contract v1).

Phase 1: models only.
- no IO
- no persistence logic
- no helper/service methods
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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
class ChunkManifest:
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

