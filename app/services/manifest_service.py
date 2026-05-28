"""
Manifest service interface (Phase 1).

Architecture correction:
- Contract models live under `app/contracts/`
- Services live under `app/services/`

This module provides a service boundary and re-exports contract models for
backwards-compatible imports.
No IO. No persistence. No implementation.
"""

from __future__ import annotations

from typing import Any

from app.contracts.manifests import (
    ChunkManifest,
    NarrationChunk,
    NarrationManifest,
    SpeakerChunk,
    SpeakerManifest,
)


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


__all__ = [
    "ManifestService",
    # Compatibility re-exports
    "NarrationChunk",
    "SpeakerChunk",
    "ChunkManifest",
    "NarrationManifest",
    "SpeakerManifest",
]

