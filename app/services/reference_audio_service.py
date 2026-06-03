"""E9.2-A part-level reference voice for VC."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.contracts.wav_validation import is_valid_wav
from app.storage.layout import REFERENCE_WAV_NAME
from app.storage.project_store import ProjectStore


class ReferenceAudioInvalidError(ValueError):
    """Uploaded bytes are not a valid WAV file."""


@dataclass(frozen=True, slots=True)
class ReferenceAudioMetadata:
    exists: bool
    path: str | None
    size_bytes: int | None


@dataclass(frozen=True, slots=True)
class ReferenceAudioUploadResult:
    filename: str
    size_bytes: int
    path: str


def resolve_reference_audio_path(
    store: ProjectStore,
    project_id: str,
    part_id: str,
) -> Path | None:
    """Same resolution order as VC worker: processing_profile then reference.wav."""
    part = store.load_part(project_id, part_id)
    if part.processing_profile:
        candidate = store.resolve_part_path(
            project_id,
            part_id,
            part.processing_profile,
        )
        if candidate.is_file() and is_valid_wav(candidate):
            return candidate
    default = store.part_layout(project_id, part_id).reference_wav_path()
    if default.is_file() and is_valid_wav(default):
        return default
    return None


def reference_audio_ready(
    store: ProjectStore,
    *,
    project_id: str,
    part_id: str,
) -> bool:
    return resolve_reference_audio_path(store, project_id, part_id) is not None


class ReferenceAudioService:
    def __init__(self, store: ProjectStore) -> None:
        self._store = store

    def reference_exists(self, project_id: str, part_id: str) -> bool:
        return reference_audio_ready(
            self._store,
            project_id=project_id,
            part_id=part_id,
        )

    def reference_path(self, project_id: str, part_id: str) -> Path:
        resolved = resolve_reference_audio_path(self._store, project_id, part_id)
        if resolved is None:
            raise FileNotFoundError(
                f"reference audio not found for {project_id}/{part_id}"
            )
        return resolved

    def reference_metadata(self, project_id: str, part_id: str) -> ReferenceAudioMetadata:
        resolved = resolve_reference_audio_path(self._store, project_id, part_id)
        if resolved is None:
            return ReferenceAudioMetadata(exists=False, path=None, size_bytes=None)
        rel = REFERENCE_WAV_NAME
        if resolved.name != REFERENCE_WAV_NAME:
            pl = self._store.part_layout(project_id, part_id)
            try:
                rel = resolved.resolve().relative_to(pl.root.resolve()).as_posix()
            except ValueError:
                rel = resolved.name
        return ReferenceAudioMetadata(
            exists=True,
            path=rel,
            size_bytes=resolved.stat().st_size,
        )

    def upload_reference_audio(
        self,
        project_id: str,
        part_id: str,
        data: bytes,
    ) -> ReferenceAudioUploadResult:
        if not data:
            raise ReferenceAudioInvalidError("Reference audio file is empty")
        pl = self._store.part_layout(project_id, part_id)
        pl.root.mkdir(parents=True, exist_ok=True)
        target = pl.reference_wav_path()
        target.write_bytes(data)
        if not is_valid_wav(target):
            target.unlink(missing_ok=True)
            raise ReferenceAudioInvalidError("Reference audio must be a valid WAV file")
        size = target.stat().st_size
        return ReferenceAudioUploadResult(
            filename=REFERENCE_WAV_NAME,
            size_bytes=size,
            path=REFERENCE_WAV_NAME,
        )

    def delete_reference_audio(self, project_id: str, part_id: str) -> None:
        path = self._store.part_layout(project_id, part_id).reference_wav_path()
        if path.is_file():
            path.unlink()
