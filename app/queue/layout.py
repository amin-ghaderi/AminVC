"""E3.0 filesystem queue layout."""

from __future__ import annotations

from pathlib import Path

from app.config.settings import AppSettings


class QueueLayout:
    def __init__(self, queue_root: Path) -> None:
        self.queue_root = queue_root
        self.queue_path = queue_root / "queue.json"
        self.running_path = queue_root / "running.json"
        self.history_path = queue_root / "history.json"
        self.checkpoints_dir = queue_root / "checkpoints"

    def ensure_tree(self) -> None:
        self.queue_root.mkdir(parents=True, exist_ok=True)
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)


class QueueLayoutService:
    def __init__(self, settings: AppSettings | None = None) -> None:
        settings = settings or AppSettings()
        self._root = settings.queue_root

    def layout(self) -> QueueLayout:
        return QueueLayout(self._root)
