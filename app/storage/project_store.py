"""
E0 filesystem project storage — manifests only.

No UI, API, queue engine, recovery engine, or event bus.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from app.config.settings import AppSettings
from app.contracts.manifests import (
    AssetSlot,
    BuildManifest,
    ChunkManifest,
    PartManifest,
    ProjectManifest,
)
from app.contracts.states import PROJECT_STATUS_ACTIVE, STATE_DRAFT
from app.storage.json_io import read_json, write_json_atomic
from app.storage.layout import (
    PartLayout,
    ProjectLayout,
    ProjectLayoutService,
    format_build_id,
    format_part_id,
)
from app.storage.serialization import (
    InvalidStateError,
    build_from_dict,
    build_to_dict,
    chunk_from_dict,
    chunk_to_dict,
    part_from_dict,
    part_to_dict,
    project_from_dict,
    project_to_dict,
    utc_now_iso,
    validate_build_manifest,
    validate_chunk_state,
    validate_part_state,
)

BuildStorageLevel = Literal["project", "part"]
_BUILD_ID_PATTERN = re.compile(r"^build-(\d{3})\.json$")


class ProjectNotFoundError(FileNotFoundError):
    pass


class PartNotFoundError(FileNotFoundError):
    pass


class ChunkNotFoundError(FileNotFoundError):
    pass


class BuildNotFoundError(FileNotFoundError):
    pass


class ProjectStore:
    """Persist E0 Project, Part, and Chunk manifests on disk."""

    def __init__(
        self,
        settings: AppSettings | None = None,
        layout_service: ProjectLayoutService | None = None,
    ) -> None:
        self._settings = settings or AppSettings()
        self._layout = layout_service or ProjectLayoutService(self._settings)

    def layout(self, project_id: str) -> ProjectLayout:
        return self._layout.layout(project_id)

    def part_layout(self, project_id: str, part_id: str) -> PartLayout:
        return self._layout.layout(project_id).part_layout(part_id)

    # --- Project ---

    def create_project(self, project_id: str, *, title: str = "") -> ProjectManifest:
        if self._layout.project_exists(project_id):
            raise FileExistsError(f"Project already exists: {project_id}")
        now = utc_now_iso()
        manifest = ProjectManifest(
            project_id=project_id,
            title=title,
            created_at=now,
            updated_at=now,
            status=PROJECT_STATUS_ACTIVE,
            parts=[],
        )
        self._layout.ensure_project_tree(project_id)
        self.save_project(manifest)
        return manifest

    def load_project(self, project_id: str) -> ProjectManifest:
        data = read_json(self.layout(project_id).project_manifest_path)
        if data is None:
            raise ProjectNotFoundError(f"Project not found: {project_id}")
        return project_from_dict(data)

    def save_project(self, manifest: ProjectManifest) -> None:
        manifest.updated_at = utc_now_iso()
        write_json_atomic(
            self.layout(manifest.project_id).project_manifest_path,
            project_to_dict(manifest),
        )

    def list_project_ids(self) -> list[str]:
        root = self._layout.projects_root
        if not root.is_dir():
            return []
        return sorted(
            p.name
            for p in root.iterdir()
            if p.is_dir() and (p / "project.json").is_file()
        )

    # --- Part (user-created; never auto-split) ---

    def create_part(
        self,
        project_id: str,
        *,
        part_id: str | None = None,
        part_index: int | None = None,
        title: str = "",
        processing_profile: str = "",
    ) -> PartManifest:
        project = self.load_project(project_id)
        if part_id is None:
            if part_index is None:
                part_index = len(project.parts) + 1
            part_id = format_part_id(part_index)
        if part_id in project.parts:
            raise FileExistsError(f"Part already exists: {part_id}")

        now = utc_now_iso()
        manifest = PartManifest(
            part_id=part_id,
            project_id=project_id,
            title=title,
            state=STATE_DRAFT,
            processing_profile=processing_profile,
            created_at=now,
            updated_at=now,
        )
        self._layout.ensure_part_tree(project_id, part_id)
        self.save_part(manifest)
        project.parts.append(part_id)
        self.save_project(project)
        return manifest

    def load_part(self, project_id: str, part_id: str) -> PartManifest:
        data = read_json(self.part_layout(project_id, part_id).manifest_path)
        if data is None:
            raise PartNotFoundError(f"Part not found: {project_id}/{part_id}")
        return part_from_dict(data)

    def save_part(self, manifest: PartManifest) -> None:
        validate_part_state(manifest.state)
        manifest.updated_at = utc_now_iso()
        self._layout.ensure_part_tree(manifest.project_id, manifest.part_id)
        write_json_atomic(
            self.part_layout(manifest.project_id, manifest.part_id).manifest_path,
            part_to_dict(manifest),
        )

    def list_parts(self, project_id: str) -> list[PartManifest]:
        project = self.load_project(project_id)
        parts: list[PartManifest] = []
        for part_id in project.parts:
            try:
                parts.append(self.load_part(project_id, part_id))
            except PartNotFoundError:
                continue
        return parts

    # --- Chunk (smallest processing unit) ---

    def create_chunk(
        self,
        project_id: str,
        part_id: str,
        chunk_id: int,
        *,
        text: str = "",
    ) -> ChunkManifest:
        part = self.load_part(project_id, part_id)
        pl = self.part_layout(project_id, part_id)
        narration_file = self._relative_to_part(pl, pl.narration_wav_path(chunk_id))
        vc_file = self._relative_to_part(pl, pl.vc_wav_path(chunk_id))
        manifest = ChunkManifest(
            chunk_id=chunk_id,
            state=STATE_DRAFT,
            text=text,
            narration=AssetSlot(status="", file=narration_file, duration_seconds=None),
            vc=AssetSlot(status="", file=vc_file, duration_seconds=None),
            updated_at=utc_now_iso(),
        )
        pl.chunks_dir.mkdir(parents=True, exist_ok=True)
        self.save_chunk(project_id, part_id, manifest)
        if chunk_id > part.chunks_total:
            part.chunks_total = chunk_id
            self.save_part(part)
        return manifest

    def load_chunk(self, project_id: str, part_id: str, chunk_id: int) -> ChunkManifest:
        path = self.part_layout(project_id, part_id).chunk_manifest_path(chunk_id)
        data = read_json(path)
        if data is None:
            raise ChunkNotFoundError(
                f"Chunk not found: {project_id}/{part_id}/{chunk_id:04d}"
            )
        return chunk_from_dict(data)

    def save_chunk(self, project_id: str, part_id: str, manifest: ChunkManifest) -> None:
        validate_chunk_state(manifest.state)
        manifest.updated_at = utc_now_iso()
        pl = self.part_layout(project_id, part_id)
        write_json_atomic(pl.chunk_manifest_path(manifest.chunk_id), chunk_to_dict(manifest))

    def list_chunks(self, project_id: str, part_id: str) -> list[ChunkManifest]:
        chunks_dir = self.part_layout(project_id, part_id).chunks_dir
        if not chunks_dir.is_dir():
            return []
        manifests: list[ChunkManifest] = []
        for path in sorted(chunks_dir.glob("*.json")):
            data = read_json(path)
            if data is None:
                continue
            manifests.append(chunk_from_dict(data))
        return sorted(manifests, key=lambda c: c.chunk_id)

    def resolve_part_path(self, project_id: str, part_id: str, relative_path: str) -> Path:
        return (self.part_layout(project_id, part_id).root / relative_path).resolve()

    # --- Build (user-created merged output; permanent asset) ---

    def create_build(
        self,
        project_id: str,
        part_id: str,
        *,
        name: str,
        chunks: list[int] | None = None,
        build_id: str | None = None,
        build_index: int | None = None,
        level: BuildStorageLevel = "part",
    ) -> BuildManifest:
        self.load_project(project_id)
        self.load_part(project_id, part_id)
        builds_dir = self._builds_dir(project_id, part_id, level)
        builds_dir.mkdir(parents=True, exist_ok=True)

        if build_id is None:
            if build_index is None:
                build_index = self._next_build_index(builds_dir)
            build_id = format_build_id(build_index)

        manifest_path = self._build_manifest_path(project_id, part_id, build_id, level)
        if manifest_path.is_file():
            raise FileExistsError(f"Build already exists: {build_id}")

        now = utc_now_iso()
        output_rel = self._default_build_output_file(build_id)
        manifest = BuildManifest(
            build_id=build_id,
            project_id=project_id,
            part_id=part_id,
            name=name,
            created_at=now,
            updated_at=now,
            chunks=list(chunks or []),
            output_file=output_rel,
            duration_seconds=None,
        )
        self.save_build(manifest, level=level)
        return manifest

    def load_build(
        self,
        project_id: str,
        part_id: str,
        build_id: str,
        *,
        level: BuildStorageLevel = "part",
    ) -> BuildManifest:
        data = read_json(self._build_manifest_path(project_id, part_id, build_id, level))
        if data is None:
            raise BuildNotFoundError(f"Build not found: {project_id}/{part_id}/{build_id}")
        return build_from_dict(data)

    def save_build(self, manifest: BuildManifest, *, level: BuildStorageLevel = "part") -> None:
        validate_build_manifest(manifest)
        manifest.updated_at = utc_now_iso()
        builds_dir = self._builds_dir(manifest.project_id, manifest.part_id, level)
        builds_dir.mkdir(parents=True, exist_ok=True)
        write_json_atomic(
            self._build_manifest_path(
                manifest.project_id,
                manifest.part_id,
                manifest.build_id,
                level,
            ),
            build_to_dict(manifest),
        )

    def list_builds(
        self,
        project_id: str,
        part_id: str,
        *,
        level: BuildStorageLevel = "part",
    ) -> list[BuildManifest]:
        builds_dir = self._builds_dir(project_id, part_id, level)
        if not builds_dir.is_dir():
            return []
        manifests: list[BuildManifest] = []
        for path in sorted(builds_dir.glob("build-*.json")):
            data = read_json(path)
            if data is None:
                continue
            manifest = build_from_dict(data)
            if manifest.part_id == part_id:
                manifests.append(manifest)
        return sorted(manifests, key=lambda b: b.build_id)

    def _builds_dir(
        self,
        project_id: str,
        part_id: str,
        level: BuildStorageLevel,
    ) -> Path:
        if level == "project":
            return self.layout(project_id).builds_dir
        return self.part_layout(project_id, part_id).builds_dir

    def _build_manifest_path(
        self,
        project_id: str,
        part_id: str,
        build_id: str,
        level: BuildStorageLevel,
    ) -> Path:
        if level == "project":
            return self.layout(project_id).build_manifest_path(build_id)
        return self.part_layout(project_id, part_id).build_manifest_path(build_id)

    @staticmethod
    def _default_build_output_file(build_id: str) -> str:
        return f"builds/{build_id}.wav"

    @staticmethod
    def _next_build_index(builds_dir: Path) -> int:
        max_index = 0
        for path in builds_dir.glob("build-*.json"):
            match = _BUILD_ID_PATTERN.match(path.name)
            if not match:
                continue
            max_index = max(max_index, int(match.group(1)))
        return max_index + 1

    @staticmethod
    def _relative_to_part(part_layout: PartLayout, absolute: Path) -> str:
        try:
            return absolute.resolve().relative_to(part_layout.root.resolve()).as_posix()
        except ValueError:
            return absolute.resolve().as_posix()


if __name__ == "__main__":
    import json
    import tempfile

    from app.contracts.states import STATE_TEXT_SAVED

    with tempfile.TemporaryDirectory() as tmp:
        settings = AppSettings(projects_root=Path(tmp) / "projects")
        store = ProjectStore(settings=settings)
        store.create_project("zaman-entekhab", title="زمان انتخاب")
        store.create_part("zaman-entekhab", part_id="part-001", title="فصل اول")
        chunk = store.create_chunk("zaman-entekhab", "part-001", 1, text="Paragraph one.")
        chunk.state = STATE_TEXT_SAVED
        store.save_chunk("zaman-entekhab", "part-001", chunk)
        print(json.dumps(project_to_dict(store.load_project("zaman-entekhab")), indent=2, ensure_ascii=False))
        print(json.dumps(chunk_to_dict(store.load_chunk("zaman-entekhab", "part-001", 1)), indent=2, ensure_ascii=False))
