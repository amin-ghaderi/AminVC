"""E5.0 VC progress session — runtime only, not persisted."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class VcProgressSession:
    chunk_id: int
    start_time: datetime
    current_step: int
    total_steps: int
