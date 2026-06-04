"""E5.0 VC progress session — runtime only, not persisted."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class VcProgressSession:
    chunk_id: int
    start_time: datetime
    current_step: int
    total_steps: int
    segment_index: int | None = None
    segment_total: int | None = None
    segment_start_time: datetime | None = None
    completed_segment_durations: list[float] = field(default_factory=list)
