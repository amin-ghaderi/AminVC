"""E7.1 — Read queue jobs from QueueStore (no duplicate storage)."""

from __future__ import annotations

from dataclasses import dataclass

from app.contracts.queue import QueueItem
from app.queue.store import QueueStore


@dataclass(frozen=True, slots=True)
class QueueJobsView:
    queued: list[QueueItem]
    running: list[QueueItem]
    completed: list[QueueItem]
    failed: list[QueueItem]
    cancelled: list[QueueItem]


class QueueQueryService:
    def __init__(self, store: QueueStore) -> None:
        self._store = store

    def list_jobs(self) -> QueueJobsView:
        self._store.ensure_tree()
        queued = self._store.load_queued()
        running_item = self._store.load_running()
        running = [running_item] if running_item is not None else []
        completed, failed, cancelled = self._store.load_history()
        return QueueJobsView(
            queued=queued,
            running=running,
            completed=completed,
            failed=failed,
            cancelled=cancelled,
        )
