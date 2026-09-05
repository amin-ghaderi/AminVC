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
import os
import sys


PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
"""Repository root directory (AminVC/)."""

STORAGE_ROOT: Path = PROJECT_ROOT / "storage"
"""Repository-level storage root (Contract v1 target: storage/projects/... later)."""

PROJECTS_ROOT: Path = STORAGE_ROOT / "projects"
"""Project workspace root (Contract v1): storage/projects/{project_id}/..."""

QUEUE_ROOT: Path = STORAGE_ROOT / "queue"
"""E3.0 filesystem queue root: storage/queue/queue.json, running.json, history.json."""

EVENTS_ROOT: Path = STORAGE_ROOT / "events"
"""E4.0 optional event history: storage/events/latest.jsonl, archive/."""

SPEAKER_ENGINE_ROOT: Path = PROJECT_ROOT / "speaker-engine"
"""Location of the speaker engine within the monorepo."""


def resolve_speaker_python_executable() -> str:
    """
    Resolve the Python executable used to launch the isolated speaker-engine worker.

    Resolution priority:
    A) explicit env var (highest): SPEAKER_PYTHON_EXECUTABLE
    B) deterministic local venv: <repo_root>/speaker-engine/venv/Scripts/python.exe
    C) fallback: sys.executable

    This function must not crash if the venvs are missing.
    """

    explicit = os.environ.get("SPEAKER_PYTHON_EXECUTABLE", "").strip()
    if explicit:
        return explicit

    venv_python = SPEAKER_ENGINE_ROOT / "venv" / "Scripts" / "python.exe"
    try:
        if venv_python.exists():
            return str(venv_python)
    except OSError:
        pass
    return sys.executable


@dataclass(frozen=True, slots=True)
class AppSettings:
    """
    Minimal typed settings container.

    This exists so Phase 2+ can evolve configuration without changing call sites.
    """

    project_root: Path = PROJECT_ROOT
    storage_root: Path = STORAGE_ROOT
    projects_root: Path = PROJECTS_ROOT
    queue_root: Path = QUEUE_ROOT
    events_root: Path = EVENTS_ROOT
    speaker_python_executable: str = resolve_speaker_python_executable()
    narration_base_url: str = "http://127.0.0.1:8000"
    narration_timeout_seconds: int = 30
    narration_poll_interval_seconds: float = 2.0
    auto_start_worker: bool = True
    agent_cloud_url: str = ""
    agent_heartbeat_interval_seconds: float = 10.0
    agent_device_id_path: Path = STORAGE_ROOT / "agent" / "device_id"

