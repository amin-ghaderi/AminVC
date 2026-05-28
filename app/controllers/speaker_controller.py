"""
Speaker conversion controller placeholder (Phase 1).

Defines intended controller-level entrypoints for speaker conversion actions.
No engine calls and no orchestration in Phase 1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SpeakerController:
    def convert_chunk(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    def convert_batch(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

