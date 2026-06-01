"""
E6.0 WorkerExecutionEngine — single-process queue consumer.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

from app.config.settings import AppSettings
from app.contracts.queue import QueueItem
from app.events.bus import EventBus
from app.queue.manager import QueueManager
from app.recovery.recovery_service import RecoveryService
from app.services.build_service import BuildService
from app.services.narration_chunk_executor import (
    GeminiNarrationChunkExecutor,
    NarrationChunkExecutor,
)
from app.services.speaker_service import WorkerSpeakerService
from app.storage.project_store import ProjectStore
from app.worker.events import (
    publish_worker_job_completed,
    publish_worker_job_failed,
    publish_worker_job_started,
    publish_worker_started,
    publish_worker_stopped,
)
from app.worker.job_runner import JobExecutionError, JobRunner
from app.worker.state import WorkerState

logger = logging.getLogger(__name__)

DEFAULT_POLL_INTERVAL_SECONDS = 1.0


class WorkerExecutionEngine:
    def __init__(
        self,
        queue: QueueManager | None = None,
        recovery: RecoveryService | None = None,
        project_store: ProjectStore | None = None,
        event_bus: EventBus | None = None,
        narration: NarrationChunkExecutor | None = None,
        speaker: WorkerSpeakerService | None = None,
        build_service: BuildService | None = None,
        poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
    ) -> None:
        settings = AppSettings()
        self._store = project_store or ProjectStore(settings)
        self._event_bus = event_bus or EventBus()
        self._queue = queue or QueueManager(
            project_store=self._store,
            event_bus=self._event_bus,
        )
        self._recovery = recovery or RecoveryService(
            store=self._store,
            event_bus=self._event_bus,
        )
        self._speaker = speaker or WorkerSpeakerService()
        self._runner = JobRunner(
            self._store,
            narration
            or GeminiNarrationChunkExecutor(event_bus=self._event_bus),
            self._speaker,
            build_service or BuildService(self._store),
            event_bus=self._event_bus,
        )
        self._poll_interval = poll_interval
        self._state = WorkerState.STOPPED
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    @property
    def state(self) -> WorkerState:
        return self._state

    def is_running(self) -> bool:
        return self._running

    def startup(self) -> None:
        """Recovery scan + queue restore (no auto-resume)."""
        self._queue.restore()
        for project_id in self._store.list_project_ids():
            try:
                self._recovery.scan_project(project_id)
            except Exception:
                logger.warning(
                    "recovery scan failed for project %s",
                    project_id,
                    exc_info=True,
                )
        self._state = WorkerState.IDLE

    def start(self) -> None:
        if self._running:
            return
        self.startup()
        self._running = True
        publish_worker_started(self._event_bus)
        self._thread = threading.Thread(target=self._loop, name="aminvc-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=120)
            self._thread = None
        self._state = WorkerState.STOPPED
        publish_worker_stopped(self._event_bus)

    def run_once(self) -> bool:
        """Process at most one job (for tests). Returns True if a job ran."""
        self._state = WorkerState.POLLING
        job = self._queue.dequeue()
        if job is None:
            self._state = WorkerState.IDLE
            return False
        self._execute_job(job)
        self._state = WorkerState.IDLE
        return True

    def _loop(self) -> None:
        while self._running:
            self._state = WorkerState.POLLING
            job = self._queue.dequeue()
            if job is None:
                self._state = WorkerState.IDLE
                time.sleep(self._poll_interval)
                continue
            self._execute_job(job)
            if not self._running:
                break
        self._state = WorkerState.STOPPED

    def _execute_job(self, job: QueueItem) -> None:
        self._state = WorkerState.EXECUTING
        publish_worker_job_started(self._event_bus, job)
        self._queue.mark_running(job)
        try:
            self._runner.execute(job)
            self._queue.mark_completed(job.job_id)
            publish_worker_job_completed(self._event_bus, job)
        except Exception as exc:
            error = str(exc)
            logger.exception("worker job failed: %s", job.job_id)
            try:
                self._queue.mark_failed(job.job_id, error)
            except Exception:
                logger.exception("queue mark_failed failed for %s", job.job_id)
            publish_worker_job_failed(self._event_bus, job, error)
        finally:
            if self._running:
                self._state = WorkerState.IDLE
            else:
                self._state = WorkerState.STOPPED
