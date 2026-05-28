"""
Audiobook pipeline placeholder (Phase 1).

Contract v1: `app/` will orchestrate the end-to-end pipeline in later phases.
Phase 1 hard rule: no orchestration logic and no engine calls here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AudiobookPipeline:
    """
    Phase 1: method signatures only.

    Phase 2+ will provide concrete implementations and will coordinate:
    narration generation → speaker conversion → merge/mastering → validation → export.
    """

    def run(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    def pause(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    def resume(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    def cancel(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

