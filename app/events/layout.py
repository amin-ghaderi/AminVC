"""E4.0 optional event history filesystem layout."""

from __future__ import annotations

from pathlib import Path

from app.config.settings import AppSettings


class EventsLayout:
    def __init__(self, events_root: Path) -> None:
        self.events_root = events_root
        self.latest_path = events_root / "latest.jsonl"
        self.archive_dir = events_root / "archive"

    def ensure_tree(self) -> None:
        self.events_root.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)


class EventsLayoutService:
    def __init__(self, settings: AppSettings | None = None) -> None:
        settings = settings or AppSettings()
        self._root = settings.events_root

    def layout(self) -> EventsLayout:
        return EventsLayout(self._root)
