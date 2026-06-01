"""E1.5 — Build manifest serialization and persistence."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config.settings import AppSettings
from app.contracts.manifests import BuildManifest
from app.storage.json_io import read_json
from app.storage.project_store import BuildNotFoundError, ProjectStore
from app.storage.serialization import (
    InvalidBuildManifestError,
    build_from_dict,
    build_to_dict,
    validate_build_manifest,
)


@pytest.fixture
def store(tmp_path: Path) -> ProjectStore:
    return ProjectStore(settings=AppSettings(projects_root=tmp_path / "projects"))


def test_build_serialization_round_trip() -> None:
    manifest = BuildManifest(
        build_id="build-001",
        project_id="book-1",
        part_id="part-001",
        name="Chapter03-Final",
        created_at="2026-05-29T12:00:00+00:00",
        updated_at="2026-05-29T12:00:00+00:00",
        chunks=[3, 1, 2],
        output_file="builds/build-001.wav",
        duration_seconds=125.5,
    )
    data = build_to_dict(manifest)
    assert set(data.keys()) == {
        "build_id",
        "project_id",
        "part_id",
        "name",
        "created_at",
        "updated_at",
        "chunks",
        "output_file",
        "duration_seconds",
    }
    restored = build_from_dict(data)
    assert restored.chunks == [3, 1, 2]
    assert restored.duration_seconds == 125.5


def test_build_validation() -> None:
    with pytest.raises(InvalidBuildManifestError):
        validate_build_manifest(
            BuildManifest(build_id="", project_id="p", part_id="part-001")
        )
    with pytest.raises(InvalidBuildManifestError):
        validate_build_manifest(
            BuildManifest(build_id="build-001", project_id="", part_id="part-001")
        )
    with pytest.raises(InvalidBuildManifestError):
        validate_build_manifest(
            BuildManifest(build_id="build-001", project_id="p", part_id="")
        )


def test_part_level_build_persistence(store: ProjectStore) -> None:
    store.create_project("book-1")
    store.create_part("book-1", part_id="part-001")
    store.create_chunk("book-1", "part-001", 1)
    store.create_chunk("book-1", "part-001", 2)

    build = store.create_build(
        "book-1",
        "part-001",
        name="Chapter03-Test",
        chunks=[2, 1],
        build_id="build-001",
    )
    path = store.part_layout("book-1", "part-001").build_manifest_path("build-001")
    assert path.name == "build-001.json"
    on_disk = read_json(path)
    assert on_disk["name"] == "Chapter03-Test"
    assert on_disk["chunks"] == [2, 1]
    assert on_disk["output_file"] == "builds/build-001.wav"
    assert on_disk["duration_seconds"] is None

    build.duration_seconds = 90.0
    store.save_build(build)
    reloaded = store.load_build("book-1", "part-001", "build-001")
    assert reloaded.duration_seconds == 90.0


def test_build_listing_and_deterministic_ids(store: ProjectStore) -> None:
    store.create_project("book-1")
    store.create_part("book-1", part_id="part-001")

    first = store.create_build("book-1", "part-001", name="A")
    second = store.create_build("book-1", "part-001", name="B")

    assert first.build_id == "build-001"
    assert second.build_id == "build-002"

    listed = store.list_builds("book-1", "part-001")
    assert [b.build_id for b in listed] == ["build-001", "build-002"]


def test_build_reload_after_restart(tmp_path: Path) -> None:
    projects_root = tmp_path / "projects"
    store_a = ProjectStore(settings=AppSettings(projects_root=projects_root))
    store_a.create_project("book-1")
    store_a.create_part("book-1", part_id="part-001")
    store_a.create_build(
        "book-1",
        "part-001",
        name="YouTube-Version",
        chunks=[1],
        build_id="build-001",
    )

    store_b = ProjectStore(settings=AppSettings(projects_root=projects_root))
    loaded = store_b.load_build("book-1", "part-001", "build-001")
    assert loaded.name == "YouTube-Version"

    project = store_b.load_project("book-1")
    part = store_b.load_part("book-1", "part-001")
    assert project.parts == ["part-001"]
    assert part.title == ""


def test_project_level_build_location(store: ProjectStore) -> None:
    store.create_project("book-1")
    store.create_part("book-1", part_id="part-001")

    build = store.create_build(
        "book-1",
        "part-001",
        name="Project-scoped",
        level="project",
        build_id="build-001",
    )
    path = store.layout("book-1").build_manifest_path("build-001")
    assert path.parent.name == "builds"
    assert path.is_file()

    listed = store.list_builds("book-1", "part-001", level="project")
    assert len(listed) == 1
    assert listed[0].build_id == build.build_id


def test_build_does_not_modify_other_manifests(store: ProjectStore) -> None:
    store.create_project("book-1", title="Original")
    store.create_part("book-1", part_id="part-001", title="Part")
    store.create_chunk("book-1", "part-001", 1, text="chunk text")

    part_before = read_json(store.part_layout("book-1", "part-001").manifest_path)
    chunk_before = read_json(store.part_layout("book-1", "part-001").chunk_manifest_path(1))

    store.create_build("book-1", "part-001", name="Merged")

    project_after = read_json(store.layout("book-1").project_manifest_path)
    assert project_after["title"] == "Original"
    assert read_json(store.part_layout("book-1", "part-001").manifest_path) == part_before
    assert (
        read_json(store.part_layout("book-1", "part-001").chunk_manifest_path(1))
        == chunk_before
    )


def test_load_missing_build(store: ProjectStore) -> None:
    store.create_project("book-1")
    store.create_part("book-1", part_id="part-001")
    with pytest.raises(BuildNotFoundError):
        store.load_build("book-1", "part-001", "build-099")
