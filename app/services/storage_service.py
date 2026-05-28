"""
Storage path contracts (Phase 1).

Phase 1 hard rule: define deterministic paths only.
- no filesystem IO
- no directory creation
- no reading/writing manifests
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config.settings import AppSettings


@dataclass(frozen=True, slots=True)
class StoragePaths:
    """
    Deterministic project path layout (Contract v1).

    All paths are *references* only. Creation and IO are out of scope for Phase 1.
    """

    project_dir: Path
    input_dir: Path
    extracted_dir: Path
    narration_dir: Path
    speaker_dir: Path
    merged_dir: Path
    final_dir: Path
    reports_dir: Path


class StorageService:
    """
    Contract-only storage path resolver.

    This service defines the project directory layout under:
    `storage/projects/{project_id}/...`
    """

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def get_project_dir(self, project_id: str) -> Path:
        raise NotImplementedError

    def get_input_dir(self, project_id: str) -> Path:
        raise NotImplementedError

    def get_extracted_dir(self, project_id: str) -> Path:
        raise NotImplementedError

    def get_narration_dir(self, project_id: str) -> Path:
        raise NotImplementedError

    def get_speaker_dir(self, project_id: str) -> Path:
        raise NotImplementedError

    def get_merged_dir(self, project_id: str) -> Path:
        raise NotImplementedError

    def get_final_dir(self, project_id: str) -> Path:
        raise NotImplementedError

    def get_reports_dir(self, project_id: str) -> Path:
        raise NotImplementedError

    def get_paths(self, project_id: str) -> StoragePaths:
        raise NotImplementedError

