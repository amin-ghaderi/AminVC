"""
E0 + E4.0 canonical event contracts.

E0: VcProgressEvent (legacy schema for engine compatibility).
E4: EventEnvelope, event types, and typed payloads for the internal Event Bus.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

from app.storage.serialization import utc_now_iso

# ---------------------------------------------------------------------------
# E0 — VC progress (unchanged schema for engine / adapter compatibility)
# ---------------------------------------------------------------------------

VC_PROGRESS_EVENT_TYPE: Literal["vc_progress"] = "vc_progress"


@dataclass(frozen=True, slots=True)
class VcProgressEvent:
    """
    Canonical progress event. Schema must not be changed.
    """

    type: Literal["vc_progress"]
    project_id: str
    part_id: str
    chunk_id: int
    current_step: int
    total_steps: int
    elapsed_seconds: float
    estimated_remaining_seconds: float

    def to_dict(self) -> dict[str, object]:
        return {
            "type": self.type,
            "project_id": self.project_id,
            "part_id": self.part_id,
            "chunk_id": self.chunk_id,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "elapsed_seconds": self.elapsed_seconds,
            "estimated_remaining_seconds": self.estimated_remaining_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> VcProgressEvent:
        return cls(
            type="vc_progress",
            project_id=str(data["project_id"]),
            part_id=str(data["part_id"]),
            chunk_id=int(data["chunk_id"]),
            current_step=int(data["current_step"]),
            total_steps=int(data["total_steps"]),
            elapsed_seconds=float(data["elapsed_seconds"]),
            estimated_remaining_seconds=float(data["estimated_remaining_seconds"]),
        )

    def to_vc_progress_payload(self) -> dict[str, object]:
        """E4.0 `vc.progress` envelope payload."""
        return {
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "elapsed_seconds": self.elapsed_seconds,
            "estimated_remaining_seconds": self.estimated_remaining_seconds,
        }


# ---------------------------------------------------------------------------
# E4.0 — Event Bus
# ---------------------------------------------------------------------------

EventCategory = Literal["queue", "recovery", "narration", "vc", "build", "system", "worker"]

VALID_EVENT_CATEGORIES: frozenset[str] = frozenset(
    {"queue", "recovery", "narration", "vc", "build", "system", "worker"}
)

# Queue
EVENT_QUEUE_JOB_QUEUED: Literal["queue.job_queued"] = "queue.job_queued"
EVENT_QUEUE_JOB_STARTED: Literal["queue.job_started"] = "queue.job_started"
EVENT_QUEUE_JOB_COMPLETED: Literal["queue.job_completed"] = "queue.job_completed"
EVENT_QUEUE_JOB_FAILED: Literal["queue.job_failed"] = "queue.job_failed"
EVENT_QUEUE_JOB_CANCELLED: Literal["queue.job_cancelled"] = "queue.job_cancelled"
EVENT_QUEUE_SNAPSHOT_UPDATED: Literal["queue.snapshot_updated"] = "queue.snapshot_updated"

# Recovery
EVENT_RECOVERY_INTERRUPTED_DETECTED: Literal["recovery.interrupted_detected"] = (
    "recovery.interrupted_detected"
)
EVENT_RECOVERY_RESUME_PLAN_CREATED: Literal["recovery.resume_plan_created"] = (
    "recovery.resume_plan_created"
)
EVENT_RECOVERY_RESTART_PLAN_CREATED: Literal["recovery.restart_plan_created"] = (
    "recovery.restart_plan_created"
)

# Narration
EVENT_NARRATION_CHUNK_STARTED: Literal["narration.chunk_started"] = (
    "narration.chunk_started"
)
EVENT_NARRATION_CHUNK_COMPLETED: Literal["narration.chunk_completed"] = (
    "narration.chunk_completed"
)
EVENT_NARRATION_CHUNK_FAILED: Literal["narration.chunk_failed"] = (
    "narration.chunk_failed"
)
EVENT_NARRATION_APPROVED: Literal["narration.approved"] = "narration.approved"
EVENT_NARRATION_UNAPPROVED: Literal["narration.unapproved"] = "narration.unapproved"
EVENT_NARRATION_REBUILD_REQUESTED: Literal["narration.rebuild_requested"] = (
    "narration.rebuild_requested"
)

# VC
EVENT_VC_CHUNK_STARTED: Literal["vc.chunk_started"] = "vc.chunk_started"
EVENT_VC_CHUNK_COMPLETED: Literal["vc.chunk_completed"] = "vc.chunk_completed"
EVENT_VC_CHUNK_FAILED: Literal["vc.chunk_failed"] = "vc.chunk_failed"
EVENT_VC_PROGRESS: Literal["vc.progress"] = "vc.progress"
EVENT_VC_APPROVED: Literal["vc.approved"] = "vc.approved"
EVENT_VC_UNAPPROVED: Literal["vc.unapproved"] = "vc.unapproved"
EVENT_VC_REBUILD_REQUESTED: Literal["vc.rebuild_requested"] = "vc.rebuild_requested"

# Build
EVENT_BUILD_STARTED: Literal["build.started"] = "build.started"
EVENT_BUILD_COMPLETED: Literal["build.completed"] = "build.completed"
EVENT_BUILD_FAILED: Literal["build.failed"] = "build.failed"

# System
EVENT_SYSTEM_WARNING: Literal["system.warning"] = "system.warning"
EVENT_SYSTEM_ERROR: Literal["system.error"] = "system.error"

# Worker (E6)
EVENT_WORKER_STARTED: Literal["worker.started"] = "worker.started"
EVENT_WORKER_STOPPED: Literal["worker.stopped"] = "worker.stopped"
EVENT_WORKER_JOB_STARTED: Literal["worker.job_started"] = "worker.job_started"
EVENT_WORKER_JOB_COMPLETED: Literal["worker.job_completed"] = "worker.job_completed"
EVENT_WORKER_JOB_FAILED: Literal["worker.job_failed"] = "worker.job_failed"

VALID_EVENT_TYPES: frozenset[str] = frozenset(
    {
        EVENT_QUEUE_JOB_QUEUED,
        EVENT_QUEUE_JOB_STARTED,
        EVENT_QUEUE_JOB_COMPLETED,
        EVENT_QUEUE_JOB_FAILED,
        EVENT_QUEUE_JOB_CANCELLED,
        EVENT_QUEUE_SNAPSHOT_UPDATED,
        EVENT_RECOVERY_INTERRUPTED_DETECTED,
        EVENT_RECOVERY_RESUME_PLAN_CREATED,
        EVENT_RECOVERY_RESTART_PLAN_CREATED,
        EVENT_NARRATION_CHUNK_STARTED,
        EVENT_NARRATION_CHUNK_COMPLETED,
        EVENT_NARRATION_CHUNK_FAILED,
        EVENT_NARRATION_APPROVED,
        EVENT_NARRATION_UNAPPROVED,
        EVENT_NARRATION_REBUILD_REQUESTED,
        EVENT_VC_CHUNK_STARTED,
        EVENT_VC_CHUNK_COMPLETED,
        EVENT_VC_CHUNK_FAILED,
        EVENT_VC_PROGRESS,
        EVENT_VC_APPROVED,
        EVENT_VC_UNAPPROVED,
        EVENT_VC_REBUILD_REQUESTED,
        EVENT_BUILD_STARTED,
        EVENT_BUILD_COMPLETED,
        EVENT_BUILD_FAILED,
        EVENT_SYSTEM_WARNING,
        EVENT_SYSTEM_ERROR,
        EVENT_WORKER_STARTED,
        EVENT_WORKER_STOPPED,
        EVENT_WORKER_JOB_STARTED,
        EVENT_WORKER_JOB_COMPLETED,
        EVENT_WORKER_JOB_FAILED,
    }
)

MAX_EVENT_HISTORY = 1000
MAX_EVENT_LOG_SIZE_BYTES = 10 * 1024 * 1024


@dataclass(slots=True)
class EventEnvelope:
    event_id: str
    event_type: str
    timestamp: str
    project_id: str | None = None
    part_id: str | None = None
    chunk_id: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.event_type not in VALID_EVENT_TYPES:
            raise ValueError(f"Invalid event_type: {self.event_type}")
        category = self.event_type.split(".", 1)[0]
        if category not in VALID_EVENT_CATEGORIES:
            raise ValueError(f"Invalid event category: {category}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "project_id": self.project_id,
            "part_id": self.part_id,
            "chunk_id": self.chunk_id,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EventEnvelope:
        return cls(
            event_id=str(data["event_id"]),
            event_type=str(data["event_type"]),
            timestamp=str(data["timestamp"]),
            project_id=data.get("project_id"),
            part_id=data.get("part_id"),
            chunk_id=data.get("chunk_id") if data.get("chunk_id") is not None else None,
            payload=dict(data.get("payload", {})),
        )


def new_event_id() -> str:
    return uuid.uuid4().hex


def create_event_envelope(
    event_type: str,
    *,
    project_id: str | None = None,
    part_id: str | None = None,
    chunk_id: int | None = None,
    payload: dict[str, Any] | None = None,
    event_id: str | None = None,
    timestamp: str | None = None,
) -> EventEnvelope:
    return EventEnvelope(
        event_id=event_id or new_event_id(),
        event_type=event_type,
        timestamp=timestamp or utc_now_iso(),
        project_id=project_id,
        part_id=part_id,
        chunk_id=chunk_id,
        payload=payload or {},
    )


@dataclass(slots=True)
class QueueSnapshotPayload:
    queued: int
    running: int
    completed: int
    failed: int
    cancelled: int

    def to_dict(self) -> dict[str, int]:
        return {
            "queued": self.queued,
            "running": self.running,
            "completed": self.completed,
            "failed": self.failed,
            "cancelled": self.cancelled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QueueSnapshotPayload:
        return cls(
            queued=int(data["queued"]),
            running=int(data["running"]),
            completed=int(data["completed"]),
            failed=int(data["failed"]),
            cancelled=int(data["cancelled"]),
        )


@dataclass(slots=True)
class VcProgressPayload:
    current_step: int
    total_steps: int
    elapsed_seconds: float
    estimated_remaining_seconds: float
    segment_index: int | None = None
    segment_total: int | None = None

    def to_dict(self) -> dict[str, object]:
        out: dict[str, object] = {
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "elapsed_seconds": self.elapsed_seconds,
            "estimated_remaining_seconds": self.estimated_remaining_seconds,
        }
        if self.segment_index is not None:
            out["segment_index"] = self.segment_index
        if self.segment_total is not None:
            out["segment_total"] = self.segment_total
        return out

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VcProgressPayload:
        seg_idx = data.get("segment_index")
        seg_tot = data.get("segment_total")
        return cls(
            current_step=int(data["current_step"]),
            total_steps=int(data["total_steps"]),
            elapsed_seconds=float(data["elapsed_seconds"]),
            estimated_remaining_seconds=float(data["estimated_remaining_seconds"]),
            segment_index=int(seg_idx) if seg_idx is not None else None,
            segment_total=int(seg_tot) if seg_tot is not None else None,
        )


@dataclass(slots=True)
class ChunkDurationPayload:
    duration_seconds: float

    def to_dict(self) -> dict[str, object]:
        return {"duration_seconds": self.duration_seconds}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChunkDurationPayload:
        return cls(duration_seconds=float(data["duration_seconds"]))
