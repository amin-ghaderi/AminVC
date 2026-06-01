"""
QueueManager — filesystem-backed FIFO queue (E3.0).

Planning only: no narration/VC engine invocation.
"""

from __future__ import annotations

import uuid
from typing import Literal

from app.config.settings import AppSettings
from app.contracts.queue import (
    INTERRUPTED_EXECUTION_ERROR,
    JobType,
    QueueItem,
    QueueResult,
    QueueSnapshot,
)
from app.contracts.recovery import ResumePlan
from app.contracts.states import STATE_NARRATION_QUEUED, STATE_VC_QUEUED
from app.queue.store import QueueStore
from app.storage.project_store import ChunkNotFoundError, ProjectStore
from app.storage.serialization import utc_now_iso

JobTypeArg = Literal["narration", "vc", "build"]


class QueueError(ValueError):
    pass


class QueueManager:
    def __init__(
        self,
        store: QueueStore | None = None,
        project_store: ProjectStore | None = None,
    ) -> None:
        settings = AppSettings()
        self._store = store or QueueStore(settings)
        self._project_store = project_store or ProjectStore(settings)

    def enqueue(
        self,
        *,
        project_id: str,
        part_id: str,
        job_type: JobTypeArg,
        chunk_id: int | None = None,
    ) -> QueueItem:
        self._store.ensure_tree()
        if job_type in ("narration", "vc") and chunk_id is None:
            raise QueueError(f"{job_type} jobs require chunk_id")
        if job_type == "build" and chunk_id is not None:
            raise QueueError("build jobs must have chunk_id null")

        item = QueueItem(
            job_id=self._new_job_id(),
            project_id=project_id,
            part_id=part_id,
            chunk_id=chunk_id,
            job_type=job_type,
            status="queued",
        )
        items = self._store.load_queued()
        items.append(item)
        self._store.save_queued(items)
        self._update_chunk_queued_state(item)
        return item

    def enqueue_resume_plan(
        self,
        plan: ResumePlan,
        *,
        job_type: JobTypeArg,
    ) -> list[QueueItem]:
        if job_type == "build":
            raise QueueError("resume plan enqueue supports narration or vc only")
        created: list[QueueItem] = []
        for chunk_id in plan.remaining_chunks:
            created.append(
                self.enqueue(
                    project_id=plan.project_id,
                    part_id=plan.part_id,
                    job_type=job_type,
                    chunk_id=chunk_id,
                )
            )
        return created

    def dequeue(self) -> QueueItem | None:
        self._store.ensure_tree()
        items = self._store.load_queued()
        if not items:
            return None
        item = items.pop(0)
        self._store.save_queued(items)
        return item

    def peek(self) -> QueueItem | None:
        self._store.ensure_tree()
        items = self._store.load_queued()
        return items[0] if items else None

    def cancel(self, job_id: str) -> QueueItem:
        self._store.ensure_tree()
        running = self._store.load_running()
        if running is not None and running.job_id == job_id:
            raise QueueError("cannot cancel a running job")

        items = self._store.load_queued()
        for index, item in enumerate(items):
            if item.job_id == job_id:
                removed = items.pop(index)
                self._store.save_queued(items)
                removed.status = "cancelled"
                self._store.append_history_cancelled(removed)
                return removed
        raise QueueError(f"queued job not found: {job_id}")

    def restore(self) -> QueueSnapshot:
        self._store.ensure_tree()
        running = self._store.load_running()
        if running is not None:
            running.status = "failed"
            running.last_error = INTERRUPTED_EXECUTION_ERROR
            running.completed_at = utc_now_iso()
            running.attempts += 1
            self._store.append_history_failed(running)
            self._store.save_running(None)
        return self.snapshot()

    def snapshot(self) -> QueueSnapshot:
        self._store.ensure_tree()
        queued_items = self._store.load_queued()
        running = self._store.load_running()
        completed_hist, failed_hist, cancelled_hist = self._store.load_history()
        return QueueSnapshot(
            queued=len(queued_items),
            running=1 if running is not None else 0,
            completed=len(completed_hist),
            failed=len(failed_hist),
            cancelled=len(cancelled_hist),
        )

    def mark_running(self, job: QueueItem) -> QueueItem:
        self._store.ensure_tree()
        if self._store.load_running() is not None:
            raise QueueError("a job is already running")
        job.status = "running"
        job.started_at = utc_now_iso()
        self._store.save_running(job)
        return job

    def mark_completed(self, job_id: str) -> QueueResult:
        job = self._require_running(job_id)
        job.status = "completed"
        job.completed_at = utc_now_iso()
        job.last_error = None
        self._store.append_history_completed(job)
        self._store.save_running(None)
        return QueueResult(job_id=job_id, success=True, error=None)

    def mark_failed(self, job_id: str, error: str) -> QueueResult:
        job = self._require_running(job_id)
        job.status = "failed"
        job.completed_at = utc_now_iso()
        job.last_error = error
        job.attempts += 1
        self._store.append_history_failed(job)
        self._store.save_running(None)
        return QueueResult(job_id=job_id, success=False, error=error)

    def _require_running(self, job_id: str) -> QueueItem:
        running = self._store.load_running()
        if running is None or running.job_id != job_id:
            raise QueueError(f"running job not found: {job_id}")
        return running

    def _new_job_id(self) -> str:
        return uuid.uuid4().hex

    def _update_chunk_queued_state(self, item: QueueItem) -> None:
        if item.chunk_id is None:
            return
        try:
            chunk = self._project_store.load_chunk(
                item.project_id,
                item.part_id,
                item.chunk_id,
            )
        except ChunkNotFoundError:
            return
        if item.job_type == "narration":
            chunk.state = STATE_NARRATION_QUEUED
        elif item.job_type == "vc":
            chunk.state = STATE_VC_QUEUED
        self._project_store.save_chunk(item.project_id, item.part_id, chunk)
