"""E3.0 queue persistence — queue.json, running.json, history.json."""

from __future__ import annotations

from typing import Any

from app.config.settings import AppSettings
from app.contracts.queue import QueueItem, queue_item_from_dict
from app.queue.layout import QueueLayout, QueueLayoutService
from app.storage.json_io import read_json, write_json_atomic


class QueueStore:
    def __init__(
        self,
        settings: AppSettings | None = None,
        layout_service: QueueLayoutService | None = None,
    ) -> None:
        self._layout = (layout_service or QueueLayoutService(settings)).layout()

    @property
    def layout(self) -> QueueLayout:
        return self._layout

    def ensure_tree(self) -> None:
        self._layout.ensure_tree()
        if read_json(self._layout.queue_path) is None:
            self.save_queued([])
        if read_json(self._layout.running_path) is None:
            self.save_running(None)
        if read_json(self._layout.history_path) is None:
            self.save_history([], [], [])

    def load_queued(self) -> list[QueueItem]:
        data = read_json(self._layout.queue_path) or {"items": []}
        items = data.get("items", [])
        if not isinstance(items, list):
            return []
        return [queue_item_from_dict(i) for i in items if isinstance(i, dict)]

    def save_queued(self, items: list[QueueItem]) -> None:
        write_json_atomic(
            self._layout.queue_path,
            {"items": [item.to_dict() for item in items]},
        )

    def load_running(self) -> QueueItem | None:
        data = read_json(self._layout.running_path) or {"current_job": None}
        current = data.get("current_job")
        if current is None:
            return None
        if not isinstance(current, dict):
            return None
        return queue_item_from_dict(current)

    def save_running(self, job: QueueItem | None) -> None:
        payload: dict[str, Any] = {
            "current_job": job.to_dict() if job is not None else None,
        }
        write_json_atomic(self._layout.running_path, payload)

    def load_history(
        self,
    ) -> tuple[list[QueueItem], list[QueueItem], list[QueueItem]]:
        data = read_json(self._layout.history_path) or {
            "completed": [],
            "failed": [],
        }
        completed = _items_from_list(data.get("completed", []))
        failed = _items_from_list(data.get("failed", []))
        cancelled = _items_from_list(data.get("cancelled", []))
        return completed, failed, cancelled

    def save_history(
        self,
        completed: list[QueueItem],
        failed: list[QueueItem],
        cancelled: list[QueueItem],
    ) -> None:
        write_json_atomic(
            self._layout.history_path,
            {
                "completed": [item.to_dict() for item in completed],
                "failed": [item.to_dict() for item in failed],
                "cancelled": [item.to_dict() for item in cancelled],
            },
        )

    def append_history_completed(self, item: QueueItem) -> None:
        completed, failed, cancelled = self.load_history()
        completed.append(item)
        self.save_history(completed, failed, cancelled)

    def append_history_failed(self, item: QueueItem) -> None:
        completed, failed, cancelled = self.load_history()
        failed.append(item)
        self.save_history(completed, failed, cancelled)

    def append_history_cancelled(self, item: QueueItem) -> None:
        completed, failed, cancelled = self.load_history()
        cancelled.append(item)
        self.save_history(completed, failed, cancelled)


def _items_from_list(raw: object) -> list[QueueItem]:
    if not isinstance(raw, list):
        return []
    out: list[QueueItem] = []
    for entry in raw:
        if isinstance(entry, dict):
            out.append(queue_item_from_dict(entry))
    return out
