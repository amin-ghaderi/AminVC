"""
E0 storage path resolver.

Delegates to `ProjectLayoutService` for canonical layout under
`storage/projects/{project_id}/`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config.settings import AppSettings
from app.storage.layout import PartLayout, ProjectLayout, ProjectLayoutService


@dataclass(frozen=True, slots=True)
class ProjectStoragePaths:
    project_dir: Path
    project_manifest_path: Path
    parts_dir: Path
    project_builds_dir: Path


class StorageService:
    def __init__(self, settings: AppSettings | None = None) -> None:
        self._layout = ProjectLayoutService(settings)

    def get_project_layout(self, project_id: str) -> ProjectLayout:
        return self._layout.layout(project_id)

    def get_part_layout(self, project_id: str, part_id: str) -> PartLayout:
        return self._layout.layout(project_id).part_layout(part_id)

    def get_paths(self, project_id: str) -> ProjectStoragePaths:
        layout = self._layout.layout(project_id)
        return ProjectStoragePaths(
            project_dir=layout.root,
            project_manifest_path=layout.project_manifest_path,
            parts_dir=layout.parts_dir,
            project_builds_dir=layout.builds_dir,
        )

    def ensure_project_tree(self, project_id: str) -> ProjectStoragePaths:
        layout = self._layout.ensure_project_tree(project_id)
        return ProjectStoragePaths(
            project_dir=layout.root,
            project_manifest_path=layout.project_manifest_path,
            parts_dir=layout.parts_dir,
            project_builds_dir=layout.builds_dir,
        )

    def ensure_part_tree(self, project_id: str, part_id: str) -> PartLayout:
        return self._layout.ensure_part_tree(project_id, part_id)
