"""
Speaker conversion DTO placeholders (Phase 1).

Defines request/response schemas for app↔speaker-engine boundaries.
No speaker-engine imports. No VC calls. No behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class SpeakerRequest:
    """Placeholder request for speaker conversion (Phase 1)."""

    source_audio_path: Path
    reference_audio_path: Path
    settings: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class SpeakerResult:
    """Placeholder result for speaker conversion (Phase 1)."""

    output_audio_path: Path | None = None
    metadata: dict[str, Any] | None = None

