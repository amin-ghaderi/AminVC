"""
Project contract models (Contract v1).

Phase 1: schema/model only.
- no persistence
- no runtime state transitions
- no orchestration
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.contracts.pipeline import PipelineState


@dataclass(slots=True)
class ProjectState:
    project_id: str
    status: str
    current_stage: PipelineState
    total_chunks: int = 0
    completed_chunks: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

