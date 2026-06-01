"""
E0 queue item identity contract (schema only — no queue engine).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

JobType = Literal["narration", "vc", "build"]

VALID_JOB_TYPES: frozenset[str] = frozenset({"narration", "vc", "build"})


@dataclass(frozen=True, slots=True)
class QueueItemIdentity:
    """Queue operates on Chunks. Identity: project_id, part_id, chunk_id, job_type."""

    project_id: str
    part_id: str
    chunk_id: int
    job_type: JobType

    def to_dict(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "part_id": self.part_id,
            "chunk_id": self.chunk_id,
            "job_type": self.job_type,
        }
