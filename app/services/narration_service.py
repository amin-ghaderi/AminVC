"""
Narration engine service interface (Phase 1 contract only).

Hard rules:
- no imports from `narration-engine/`
- no API calls
- no orchestration logic
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from app.services.manifest_service import NarrationManifest


@dataclass(frozen=True, slots=True)
class NarrationSettings:
    """Contract placeholder for narration settings (Phase 1)."""

    # Future: chunking caps, provider selection, voice, etc.
    # Phase 1: keep open-ended without business logic.
    options: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class IntakeResult:
    """Contract placeholder for upload_pdf(...) return (Phase 1)."""

    intake_id: str
    filename: str
    page_count: int


@dataclass(frozen=True, slots=True)
class NarrationResult:
    """Contract placeholder for generate_narration(...) return (Phase 1)."""

    intake_id: str
    chunk_paths: list[Path]
    metadata: dict[str, Any]


class NarrationService(Protocol):
    """
    Interface boundary for narration-engine.

    Phase 2+ will provide an implementation that calls the narration engine via
    HTTP or process invocation, but Phase 1 defines only the boundary.
    """

    def upload_pdf(self, pdf_bytes: bytes, filename: str) -> IntakeResult:
        raise NotImplementedError

    def update_text(self, intake_id: str, full_text: str) -> None:
        raise NotImplementedError

    def preview_chunks(self, intake_id: str) -> Any:
        raise NotImplementedError

    def generate_narration(self, intake_id: str, settings: NarrationSettings) -> NarrationResult:
        raise NotImplementedError

    def build_manifest(self, project_id: str, intake_id: str | None = None) -> NarrationManifest:
        raise NotImplementedError

