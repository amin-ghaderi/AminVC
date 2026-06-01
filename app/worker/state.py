"""E6.0 worker execution states (not persisted)."""

from __future__ import annotations

from enum import Enum


class WorkerState(str, Enum):
    IDLE = "IDLE"
    POLLING = "POLLING"
    EXECUTING = "EXECUTING"
    STOPPED = "STOPPED"
