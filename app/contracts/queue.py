"""
E3.0 queue contracts — canonical QueueItem, snapshot, and job identity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.storage.serialization import utc_now_iso

JobType = Literal["narration", "vc", "build"]
JobStatus = Literal["queued", "running", "completed", "failed", "cancelled"]

VALID_JOB_TYPES: frozenset[str] = frozenset({"narration", "vc", "build"})
VALID_JOB_STATUSES: frozenset[str] = frozenset(
    {"queued", "running", "completed", "failed", "cancelled"}
)

INTERRUPTED_EXECUTION_ERROR = "Interrupted during execution"

MAX_QUEUE_HISTORY = 1000


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


@dataclass(slots=True)
class QueueItem:
    job_id: str
    project_id: str
    part_id: str
    chunk_id: int | None
    job_type: JobType
    status: JobStatus = "queued"
    created_at: str = ""
    started_at: str | None = None
    completed_at: str | None = None
    attempts: int = 0
    last_error: str | None = None

    def __post_init__(self) -> None:
        if self.job_type not in VALID_JOB_TYPES:
            raise ValueError(f"Invalid job_type: {self.job_type}")
        if self.status not in VALID_JOB_STATUSES:
            raise ValueError(f"Invalid status: {self.status}")
        if self.job_type == "build":
            if self.chunk_id is not None:
                raise ValueError("build jobs must have chunk_id null")
        elif self.chunk_id is None:
            raise ValueError(f"{self.job_type} jobs require chunk_id")
        if not self.created_at:
            self.created_at = utc_now_iso()

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "project_id": self.project_id,
            "part_id": self.part_id,
            "chunk_id": self.chunk_id,
            "job_type": self.job_type,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "attempts": self.attempts,
            "last_error": self.last_error,
        }


@dataclass(slots=True)
class QueueSnapshot:
    queued: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "queued": self.queued,
            "running": self.running,
            "completed": self.completed,
            "failed": self.failed,
            "cancelled": self.cancelled,
        }


@dataclass(slots=True)
class QueueResult:
    job_id: str
    success: bool
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "job_id": self.job_id,
            "success": self.success,
            "error": self.error,
        }


def queue_item_from_dict(data: dict[str, Any]) -> QueueItem:
    return QueueItem(
        job_id=str(data["job_id"]),
        project_id=str(data["project_id"]),
        part_id=str(data["part_id"]),
        chunk_id=data["chunk_id"] if data.get("chunk_id") is not None else None,
        job_type=data["job_type"],  # type: ignore[arg-type]
        status=data.get("status", "queued"),  # type: ignore[arg-type]
        created_at=str(data.get("created_at", "")),
        started_at=data.get("started_at"),
        completed_at=data.get("completed_at"),
        attempts=int(data.get("attempts", 0)),
        last_error=data.get("last_error"),
    )
