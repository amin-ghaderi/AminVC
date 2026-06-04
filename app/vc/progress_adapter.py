"""
E5.0 VC Progress Adapter — engine-agnostic progress → EventBus.

No VC engine imports. Call update_progress() from worker/engine hooks.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from app.events.bus import EventBus
from app.vc.estimation import elapsed_seconds_since, estimate_remaining_seconds
from app.vc.events import (
    publish_chunk_completed,
    publish_chunk_failed,
    publish_chunk_started,
    publish_vc_progress,
)
from app.vc.progress_session import VcProgressSession

DEFAULT_TOTAL_STEPS = 30


class VcProgressError(ValueError):
    pass


class VcProgressAdapter:
    def __init__(
        self,
        *,
        project_id: str,
        part_id: str,
        event_bus: EventBus | None = None,
        total_steps: int = DEFAULT_TOTAL_STEPS,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        if total_steps < 1:
            raise VcProgressError("total_steps must be >= 1")
        self._project_id = project_id
        self._part_id = part_id
        self._event_bus = event_bus
        self._total_steps = total_steps
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._session: VcProgressSession | None = None

    @property
    def session(self) -> VcProgressSession | None:
        return self._session

    def start_chunk(self, chunk_id: int) -> None:
        if self._session is not None:
            raise VcProgressError("a VC progress session is already active")
        start_time = self._now()
        self._session = VcProgressSession(
            chunk_id=chunk_id,
            start_time=start_time,
            current_step=0,
            total_steps=self._total_steps,
        )
        publish_chunk_started(
            self._event_bus,
            project_id=self._project_id,
            part_id=self._part_id,
            chunk_id=chunk_id,
        )

    def update_step(self, step_number: int) -> None:
        """Backward-compatible entry; uses session segment fields when set."""
        session = self._require_session()
        self.update_progress(
            step_number,
            session.total_steps,
            session.segment_index,
            session.segment_total,
        )

    def update_progress(
        self,
        step_number: int,
        total_steps: int,
        segment_index: int | None = None,
        segment_total: int | None = None,
    ) -> None:
        session = self._require_session()
        if total_steps < 1:
            raise VcProgressError("total_steps must be >= 1")
        if step_number < 0 or step_number > total_steps:
            raise VcProgressError(
                f"step_number must be between 0 and {total_steps}"
            )

        now = self._now()
        seg_idx = segment_index if segment_index and segment_index > 0 else None
        seg_tot = segment_total if segment_total and segment_total > 0 else None

        if seg_idx is not None and seg_idx != session.segment_index:
            if session.segment_start_time is not None and session.segment_index is not None:
                seg_elapsed = elapsed_seconds_since(
                    session.segment_start_time.timestamp(),
                    now.timestamp(),
                )
                session.completed_segment_durations.append(float(seg_elapsed))
            session.segment_index = seg_idx
            session.segment_start_time = now
            if seg_tot is not None:
                session.segment_total = seg_tot
        elif seg_tot is not None and session.segment_total is None:
            session.segment_total = seg_tot
            if session.segment_start_time is None:
                session.segment_start_time = now

        if (
            step_number == session.current_step
            and total_steps == session.total_steps
            and seg_idx == session.segment_index
        ):
            return

        session.current_step = step_number
        session.total_steps = total_steps
        elapsed = self._elapsed_seconds(session)
        remaining = estimate_remaining_seconds(
            step_number,
            total_steps,
            elapsed,
        )
        publish_vc_progress(
            self._event_bus,
            project_id=self._project_id,
            part_id=self._part_id,
            chunk_id=session.chunk_id,
            current_step=step_number,
            total_steps=total_steps,
            elapsed_seconds=elapsed,
            estimated_remaining_seconds=remaining,
            segment_index=session.segment_index,
            segment_total=session.segment_total,
        )

    def complete_chunk(self) -> float:
        session = self._require_session()
        duration = float(self._elapsed_seconds(session))
        publish_chunk_completed(
            self._event_bus,
            project_id=self._project_id,
            part_id=self._part_id,
            chunk_id=session.chunk_id,
            duration_seconds=duration,
        )
        self._session = None
        return duration

    def fail_chunk(self, error: str) -> None:
        session = self._require_session()
        publish_chunk_failed(
            self._event_bus,
            project_id=self._project_id,
            part_id=self._part_id,
            chunk_id=session.chunk_id,
            error=error,
        )
        self._session = None

    def _require_session(self) -> VcProgressSession:
        if self._session is None:
            raise VcProgressError("no active VC progress session")
        return self._session

    def _elapsed_seconds(self, session: VcProgressSession) -> int:
        start = session.start_time.timestamp()
        end = self._now().timestamp()
        return elapsed_seconds_since(start, end)
