"""E6.0 build merge service — canonical E0 layout outputs."""

from __future__ import annotations

from pathlib import Path

from app.services.audiobook_service import merge_pcm_wavs
from app.storage.project_store import ProjectStore


class BuildService:
    def __init__(self, store: ProjectStore | None = None) -> None:
        from app.config.settings import AppSettings

        self._store = store or ProjectStore(AppSettings())

    def merge(self, project_id: str, part_id: str, build_id: str) -> Path:
        build = self._store.load_build(project_id, part_id, build_id)
        pl = self._store.part_layout(project_id, part_id)
        audio_paths: list[Path] = []
        for chunk_id in build.chunks:
            vc_path = pl.vc_wav_path(chunk_id)
            if not vc_path.is_file():
                raise FileNotFoundError(f"Missing VC audio for chunk {chunk_id}: {vc_path}")
            audio_paths.append(vc_path)

        output_path = pl.build_output_path(build_id)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        merge_pcm_wavs(audio_paths, output_path)

        build.output_file = f"builds/{build_id}.wav"
        self._store.save_build(build)
        return output_path
