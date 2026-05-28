"""
Speaker engine service interface (Phase 1 contract only).

Hard rules:
- no imports from `speaker-engine/`
- do not call vc_wrapper here
- no orchestration logic
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from app.services.manifest_service import SpeakerChunk, SpeakerManifest


@dataclass(frozen=True, slots=True)
class SpeakerSettings:
    """Contract placeholder for speaker conversion settings (Phase 1)."""

    options: dict[str, Any] | None = None


class SpeakerService(Protocol):
    """
    Interface boundary for speaker-engine.

    Phase 2+ will implement these methods by calling speaker-engine core code
    (non-Gradio path) or exposing it via a service boundary. Phase 1 defines
    signatures only.
    """

    def convert_chunk(
        self,
        source_audio_path: Path,
        reference_audio_path: Path,
        settings: SpeakerSettings,
    ) -> Path:
        raise NotImplementedError

    def convert_batch(
        self,
        source_chunks: list[SpeakerChunk],
        reference_audio_path: Path,
        settings: SpeakerSettings,
    ) -> list[SpeakerChunk]:
        raise NotImplementedError

    def build_manifest(self, project_id: str, reference_audio_path: Path | None = None) -> SpeakerManifest:
        raise NotImplementedError

