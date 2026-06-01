"""
E2.0 recovery contracts — reports and plans (not manifest states).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RecoveryCategory(str, Enum):
    """Recovery classification only — not manifest states."""

    HEALTHY = "Healthy"
    INTERRUPTED = "Interrupted"
    FAILED = "Failed"
    COMPLETED = "Completed"
    PENDING = "Pending"


@dataclass(slots=True)
class ChunkScanResult:
    chunk_id: int
    category: RecoveryCategory
    state: str
    retry_count: int


@dataclass(slots=True)
class PartScanResult:
    project_id: str
    part_id: str
    chunks: list[ChunkScanResult] = field(default_factory=list)
    builds_detected: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProjectScanResult:
    project_id: str
    parts: list[PartScanResult] = field(default_factory=list)


@dataclass(slots=True)
class RecoveryReport:
    project_id: str
    part_id: str
    last_completed_chunk: int | None = None
    next_chunk: int | None = None
    interrupted_chunks: list[int] = field(default_factory=list)
    failed_chunks: list[int] = field(default_factory=list)
    pending_chunks: list[int] = field(default_factory=list)
    completed_chunks: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "part_id": self.part_id,
            "last_completed_chunk": self.last_completed_chunk,
            "next_chunk": self.next_chunk,
            "interrupted_chunks": list(self.interrupted_chunks),
            "failed_chunks": list(self.failed_chunks),
            "pending_chunks": list(self.pending_chunks),
            "completed_chunks": list(self.completed_chunks),
        }


@dataclass(slots=True)
class ResumePlan:
    project_id: str
    part_id: str
    start_chunk: int
    remaining_chunks: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "part_id": self.part_id,
            "start_chunk": self.start_chunk,
            "remaining_chunks": list(self.remaining_chunks),
        }


@dataclass(slots=True)
class RestartPlan:
    project_id: str
    part_id: str
    chunks: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "part_id": self.part_id,
            "chunks": list(self.chunks),
        }
