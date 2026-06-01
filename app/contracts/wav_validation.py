"""WAV file validation helpers (E9.1)."""

from __future__ import annotations

import wave
from pathlib import Path


def is_valid_wav(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.stat().st_size == 0:
        return False
    try:
        with wave.open(str(path), "rb") as handle:
            if handle.getnframes() <= 0:
                return False
            if handle.getnchannels() <= 0:
                return False
            if handle.getframerate() <= 0:
                return False
    except (EOFError, OSError, wave.Error):
        return False
    return True
