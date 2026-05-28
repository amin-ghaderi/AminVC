"""
Project controller placeholder (Phase 1).

Phase 1 hard rule: no routing (no FastAPI), no persistence, no orchestration.
This module defines *intended* entrypoints for Phase 2+ only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.state.project_state import ProjectState


@dataclass(slots=True)
class ProjectController:
    """Phase 1 placeholder. Implementations belong to later phases."""

    def create_project(self, *args: Any, **kwargs: Any) -> ProjectState:
        raise NotImplementedError

    def get_project(self, *args: Any, **kwargs: Any) -> ProjectState:
        raise NotImplementedError

    def cancel_project(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

