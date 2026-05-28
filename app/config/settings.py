"""
AminVC settings scaffold (Phase 1).

Hard rules for Phase 1:
- no environment-variable complexity
- no runtime behavior beyond defining deterministic paths
- no engine imports
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
"""Repository root directory (AminVC/)."""

STORAGE_ROOT: Path = PROJECT_ROOT / "storage"
"""Repository-level storage root (Contract v1 target: storage/projects/... later)."""

PROJECTS_ROOT: Path = STORAGE_ROOT / "projects"
"""Project workspace root (Contract v1): storage/projects/{project_id}/..."""


@dataclass(frozen=True, slots=True)
class AppSettings:
    """
    Minimal typed settings container.

    This exists so Phase 2+ can evolve configuration without changing call sites.
    """

    project_root: Path = PROJECT_ROOT
    storage_root: Path = STORAGE_ROOT
    projects_root: Path = PROJECTS_ROOT

