"""
Narration DTO placeholders (Phase 1).

This module defines request/response schemas for app↔narration-engine boundaries.
No engine imports. No API calls. No behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class NarrationRequest:
    """Placeholder request for narration generation (Phase 1)."""

    intake_id: str
    settings: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class NarrationResult:
    """Placeholder result for narration generation (Phase 1)."""

    intake_id: str
    metadata: dict[str, Any] | None = None

