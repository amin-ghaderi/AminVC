"""
E0 canonical filesystem layout.

projects/{project_id}/
  project.json
  parts/part-XXX/manifest.json
  parts/part-XXX/source/source.pdf
  parts/part-XXX/text/extracted.txt
  parts/part-XXX/text/edited.txt
  parts/part-XXX/narration/0001.wav
  parts/part-XXX/vc/0001.wav
  parts/part-XXX/builds/build-XXX.json
  parts/part-XXX/chunks/0001.json
  parts/part-XXX/checkpoints/
  builds/build-XXX.json
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config.settings import AppSettings

PROJECT_MANIFEST_FILE = "project.json"
PART_MANIFEST_FILE = "manifest.json"
SOURCE_PDF_NAME = "source.pdf"
EXTRACTED_TEXT_NAME = "extracted.txt"
EDITED_TEXT_NAME = "edited.txt"


def format_part_id(index: int) -> str:
    """part-001, part-002, ..."""
    return f"part-{index:03d}"


def format_chunk_basename(chunk_id: int) -> str:
    """0001, 0002, ..."""
    return f"{chunk_id:04d}"


def format_build_id(index: int) -> str:
    """build-001, build-002, ..."""
    return f"build-{index:03d}"


def build_manifest_filename(build_id: str) -> str:
    """build-001.json from build_id build-001."""
    return f"{build_id}.json"


@dataclass(frozen=True, slots=True)
class PartLayout:
    project_id: str
    part_id: str
    root: Path
    manifest_path: Path
    source_dir: Path
    source_pdf_path: Path
    text_dir: Path
    extracted_txt_path: Path
    edited_txt_path: Path
    narration_dir: Path
    vc_dir: Path
    builds_dir: Path
    chunks_dir: Path
    checkpoints_dir: Path

    def chunk_manifest_path(self, chunk_id: int) -> Path:
        return self.chunks_dir / f"{format_chunk_basename(chunk_id)}.json"

    def narration_wav_path(self, chunk_id: int) -> Path:
        return self.narration_dir / f"{format_chunk_basename(chunk_id)}.wav"

    def vc_wav_path(self, chunk_id: int) -> Path:
        return self.vc_dir / f"{format_chunk_basename(chunk_id)}.wav"

    def build_manifest_path(self, build_id: str) -> Path:
        return self.builds_dir / build_manifest_filename(build_id)

    def build_output_path(self, build_id: str) -> Path:
        return self.builds_dir / f"{build_id}.wav"


@dataclass(frozen=True, slots=True)
class ProjectLayout:
    project_id: str
    root: Path
    project_manifest_path: Path
    parts_dir: Path
    builds_dir: Path

    def part_dir(self, part_id: str) -> Path:
        return self.parts_dir / part_id

    def build_manifest_path(self, build_id: str) -> Path:
        return self.builds_dir / build_manifest_filename(build_id)

    def build_output_path(self, build_id: str) -> Path:
        return self.builds_dir / f"{build_id}.wav"

    def part_layout(self, part_id: str) -> PartLayout:
        root = self.part_dir(part_id)
        return PartLayout(
            project_id=self.project_id,
            part_id=part_id,
            root=root,
            manifest_path=root / PART_MANIFEST_FILE,
            source_dir=root / "source",
            source_pdf_path=root / "source" / SOURCE_PDF_NAME,
            text_dir=root / "text",
            extracted_txt_path=root / "text" / EXTRACTED_TEXT_NAME,
            edited_txt_path=root / "text" / EDITED_TEXT_NAME,
            narration_dir=root / "narration",
            vc_dir=root / "vc",
            builds_dir=root / "builds",
            chunks_dir=root / "chunks",
            checkpoints_dir=root / "checkpoints",
        )


class ProjectLayoutService:
    def __init__(self, settings: AppSettings | None = None) -> None:
        self._settings = settings or AppSettings()

    @property
    def projects_root(self) -> Path:
        return self._settings.projects_root

    def layout(self, project_id: str) -> ProjectLayout:
        root = self.projects_root / project_id
        return ProjectLayout(
            project_id=project_id,
            root=root,
            project_manifest_path=root / PROJECT_MANIFEST_FILE,
            parts_dir=root / "parts",
            builds_dir=root / "builds",
        )

    def ensure_project_tree(self, project_id: str) -> ProjectLayout:
        layout = self.layout(project_id)
        layout.root.mkdir(parents=True, exist_ok=True)
        layout.parts_dir.mkdir(parents=True, exist_ok=True)
        layout.builds_dir.mkdir(parents=True, exist_ok=True)
        return layout

    def ensure_part_tree(self, project_id: str, part_id: str) -> PartLayout:
        self.ensure_project_tree(project_id)
        part = self.layout(project_id).part_layout(part_id)
        for path in (
            part.root,
            part.source_dir,
            part.text_dir,
            part.narration_dir,
            part.vc_dir,
            part.builds_dir,
            part.chunks_dir,
            part.checkpoints_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)
        return part

    def project_exists(self, project_id: str) -> bool:
        return self.layout(project_id).project_manifest_path.is_file()

    def part_exists(self, project_id: str, part_id: str) -> bool:
        return self.layout(project_id).part_layout(part_id).manifest_path.is_file()
