"""
E0 recovery rules (pure helpers only — not a recovery engine).

Diffusion-level resume is NOT supported. Recovery is Chunk-based only.
"""

from __future__ import annotations

from pathlib import Path

from app.contracts.manifests import ChunkManifest
from app.contracts.states import (
    STATE_BUILD_READY,
    STATE_INTERRUPTED,
    STATE_NARRATION_APPROVED,
    STATE_NARRATION_PROCESSING,
    STATE_NARRATION_READY,
    STATE_VC_APPROVED,
    STATE_VC_PROCESSING,
    STATE_VC_QUEUED,
    STATE_VC_READY,
)

# Single `state` field: once the pipeline reaches VC stages, narration is implied done if the file exists.
_PAST_NARRATION_STATES = frozenset(
    {
        STATE_VC_QUEUED,
        STATE_VC_PROCESSING,
        STATE_VC_READY,
        STATE_VC_APPROVED,
        STATE_BUILD_READY,
        STATE_INTERRUPTED,
    }
)


def narration_asset_complete(chunk: ChunkManifest, narration_path: Path) -> bool:
    if chunk.state in (STATE_NARRATION_READY, STATE_NARRATION_APPROVED):
        return narration_path.is_file()
    if chunk.state in _PAST_NARRATION_STATES:
        return narration_path.is_file()
    return False


def vc_asset_complete(chunk: ChunkManifest, vc_path: Path) -> bool:
    if chunk.state not in (STATE_VC_READY, STATE_VC_APPROVED, STATE_BUILD_READY):
        return False
    return vc_path.is_file()


def chunk_pipeline_completed(chunk: ChunkManifest, narration_path: Path, vc_path: Path) -> bool:
    return narration_asset_complete(chunk, narration_path) and vc_asset_complete(
        chunk, vc_path
    )


def detect_interrupted_narration(
    chunk: ChunkManifest, narration_output_path: Path
) -> bool:
    if chunk.state != STATE_NARRATION_PROCESSING:
        return False
    return not narration_output_path.is_file()


def detect_interrupted_vc(chunk: ChunkManifest, vc_output_path: Path) -> bool:
    """
  Interrupted detection (E0):

      state == VCProcessing AND output file missing
      → Interrupted
    """
    if chunk.state != STATE_VC_PROCESSING:
        return False
    return not vc_output_path.is_file()
