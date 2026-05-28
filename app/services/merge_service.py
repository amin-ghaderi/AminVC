"""
Merge/mastering service interface (Phase 1 contract only).

Contract v1: merge/mastering/validation/export are app-owned stages.
Phase 1: define boundary only. No FFmpeg calls. No IO.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True, slots=True)
class MergeSettings:
    """Placeholder settings for merge/mastering (Phase 1)."""

    apply_mastering: bool = False


class MergeService(Protocol):
    def merge_audio(
        self,
        audio_paths: list[Path],
        output_path: Path,
        settings: MergeSettings | None = None,
    ) -> Path:
        raise NotImplementedError

