"""E7.1 — Chunk narration/VC audio file access."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.storage.project_store import ProjectStore


class AudioNotFoundError(FileNotFoundError):
    """Raised when a chunk WAV asset is missing on disk."""


@dataclass(frozen=True, slots=True)
class ChunkAssetInfo:
    narration_exists: bool
    vc_exists: bool
    narration_url: str
    vc_url: str
    narration_size: int | None
    vc_size: int | None


class AudioAssetService:
    def __init__(self, store: ProjectStore) -> None:
        self._store = store

    def narration_path(self, project_id: str, part_id: str, chunk_id: int) -> Path:
        self._store.load_chunk(project_id, part_id, chunk_id)
        return self._store.part_layout(project_id, part_id).narration_wav_path(chunk_id)

    def vc_path(self, project_id: str, part_id: str, chunk_id: int) -> Path:
        self._store.load_chunk(project_id, part_id, chunk_id)
        return self._store.part_layout(project_id, part_id).vc_wav_path(chunk_id)

    def resolve_narration_file(
        self,
        project_id: str,
        part_id: str,
        chunk_id: int,
    ) -> Path:
        path = self.narration_path(project_id, part_id, chunk_id)
        if not path.is_file() or path.stat().st_size == 0:
            raise AudioNotFoundError("Audio file not found")
        return path

    def resolve_vc_file(self, project_id: str, part_id: str, chunk_id: int) -> Path:
        path = self.vc_path(project_id, part_id, chunk_id)
        if not path.is_file() or path.stat().st_size == 0:
            raise AudioNotFoundError("Audio file not found")
        return path

    def chunk_assets(
        self,
        project_id: str,
        part_id: str,
        chunk_id: int,
        *,
        api_prefix: str = "/api/v1",
    ) -> ChunkAssetInfo:
        self._store.load_chunk(project_id, part_id, chunk_id)
        narr = self.narration_path(project_id, part_id, chunk_id)
        vc = self.vc_path(project_id, part_id, chunk_id)
        narr_exists = narr.is_file() and narr.stat().st_size > 0
        vc_exists = vc.is_file() and vc.stat().st_size > 0
        base = (
            f"{api_prefix}/projects/{project_id}/parts/{part_id}/chunks/{chunk_id}/audio"
        )
        return ChunkAssetInfo(
            narration_exists=narr_exists,
            vc_exists=vc_exists,
            narration_url=f"{base}/narration",
            vc_url=f"{base}/vc",
            narration_size=narr.stat().st_size if narr_exists else None,
            vc_size=vc.stat().st_size if vc_exists else None,
        )
