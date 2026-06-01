"""
E0 canonical event contracts (schema only — no event bus).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

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
