"""E7.1 — UI support API tests."""

from __future__ import annotations

import wave
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.api.services import ApplicationServices
from app.config.settings import AppSettings
from app.contracts.states import (
    STATE_INTERRUPTED,
    STATE_NARRATION_APPROVED,
    STATE_NARRATION_READY,
    STATE_VC_READY,
)
from tests.lifecycle_helpers import mark_narration_approved_for_vc


@pytest.fixture
def api_client(tmp_path: Path) -> TestClient:
    settings = AppSettings(
        projects_root=tmp_path / "projects",
        queue_root=tmp_path / "queue",
        events_root=tmp_path / "events",
    )
    services = ApplicationServices.create(settings)
    app = create_app(services)
    client = TestClient(app)
    try:
        yield client
    finally:
        if services.worker.is_running():
            services.worker.stop()


def _write_wav(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(24000)
        handle.writeframes(b"\x00\x01" * 1200)


def _setup(api_client: TestClient) -> tuple[str, str]:
    api_client.post("/api/v1/projects", json={"project_id": "book-1", "title": ""})
    api_client.post(
        "/api/v1/projects/book-1/parts",
        json={"part_id": "part-001", "title": ""},
    )
    return "book-1", "part-001"


def test_queue_jobs_endpoint(api_client: TestClient) -> None:
    pid, part = _setup(api_client)
    services = api_client.app.state.services
    services.project_store.create_chunk(pid, part, 1)

    api_client.post(
        "/api/v1/queue/narration",
        json={"project_id": pid, "part_id": part, "chunk_id": 1},
    )
    response = api_client.get("/api/v1/queue/jobs")
    assert response.status_code == 200
    data = response.json()
    assert len(data["queued"]) == 1
    assert data["queued"][0]["job_type"] == "narration"
    assert data["queued"][0]["chunk_id"] == 1


def test_running_job_visibility(api_client: TestClient) -> None:
    pid, part = _setup(api_client)
    services = api_client.app.state.services
    services.project_store.create_chunk(pid, part, 2)
    item = services.queue.enqueue(
        project_id=pid,
        part_id=part,
        job_type="narration",
        chunk_id=2,
    )
    services.queue.mark_running(item)

    data = api_client.get("/api/v1/queue/jobs").json()
    assert len(data["running"]) == 1
    assert data["running"][0]["job_id"] == item.job_id
    assert data["running"][0]["status"] == "running"


def test_history_visibility(api_client: TestClient) -> None:
    pid, part = _setup(api_client)
    services = api_client.app.state.services
    services.project_store.create_chunk(pid, part, 3)
    item = services.queue.enqueue(
        project_id=pid,
        part_id=part,
        job_type="narration",
        chunk_id=3,
    )
    services.queue.mark_running(item)
    services.queue.mark_completed(item.job_id)

    data = api_client.get("/api/v1/queue/jobs").json()
    assert len(data["completed"]) == 1
    assert data["completed"][0]["status"] == "completed"


def test_narration_audio_route(api_client: TestClient) -> None:
    pid, part = _setup(api_client)
    pl = api_client.app.state.services.project_store.part_layout(pid, part)
    _write_wav(pl.narration_wav_path(1))
    api_client.app.state.services.project_store.create_chunk(pid, part, 1)

    response = api_client.get(
        f"/api/v1/projects/{pid}/parts/{part}/chunks/1/audio/narration",
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/")


def test_vc_audio_route(api_client: TestClient) -> None:
    pid, part = _setup(api_client)
    pl = api_client.app.state.services.project_store.part_layout(pid, part)
    _write_wav(pl.vc_wav_path(1))
    api_client.app.state.services.project_store.create_chunk(pid, part, 1)

    response = api_client.get(
        f"/api/v1/projects/{pid}/parts/{part}/chunks/1/audio/vc",
    )
    assert response.status_code == 200


def test_missing_audio_file(api_client: TestClient) -> None:
    pid, part = _setup(api_client)
    api_client.app.state.services.project_store.create_chunk(pid, part, 1)

    response = api_client.get(
        f"/api/v1/projects/{pid}/parts/{part}/chunks/1/audio/narration",
    )
    assert response.status_code == 404
    assert response.json()["error"] == "Audio file not found"


def test_extract_text_endpoint(api_client: TestClient) -> None:
    pid, part = _setup(api_client)
    pl = api_client.app.state.services.project_store.part_layout(pid, part)
    pl.source_dir.mkdir(parents=True, exist_ok=True)
    pl.source_pdf_path.write_bytes(b"%PDF-1.4 mock")

    with patch(
        "app.services.part_text_service._extract_pdf_bytes",
        return_value="extracted persian text",
    ):
        response = api_client.post(
            f"/api/v1/projects/{pid}/parts/{part}/extract-text",
        )
    assert response.status_code == 200
    assert response.json()["text"] == "extracted persian text"
    assert pl.extracted_txt_path.read_text(encoding="utf-8") == "extracted persian text"


def test_chunk_creation_endpoint(api_client: TestClient) -> None:
    pid, part = _setup(api_client)
    long_text = "جمله اول. " * 200

    with patch(
        "app.services.part_text_service._split_text",
        return_value=["chunk one", "chunk two", "chunk three"],
    ):
        response = api_client.post(
            f"/api/v1/projects/{pid}/parts/{part}/chunking",
            json={"text": long_text, "chunk_size": 800},
        )
    assert response.status_code == 201
    assert response.json()["chunks_created"] == 3
    chunks = api_client.get(f"/api/v1/projects/{pid}/parts/{part}/chunks").json()
    assert len(chunks) == 3


def test_part_summary_endpoint(api_client: TestClient) -> None:
    pid, part = _setup(api_client)
    store = api_client.app.state.services.project_store
    store.create_chunk(pid, part, 1)
    c1 = store.load_chunk(pid, part, 1)
    c1.state = STATE_NARRATION_READY
    store.save_chunk(pid, part, c1)
    store.create_chunk(pid, part, 2)
    c2 = store.load_chunk(pid, part, 2)
    c2.state = STATE_NARRATION_APPROVED
    c2.narration_approved = True
    store.save_chunk(pid, part, c2)
    store.create_chunk(pid, part, 3)
    c3 = store.load_chunk(pid, part, 3)
    c3.state = STATE_VC_READY
    store.save_chunk(pid, part, c3)

    response = api_client.get(f"/api/v1/projects/{pid}/parts/{part}/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_chunks"] == 3
    assert data["narration_ready"] == 2
    assert data["narration_approved"] == 1
    assert data["vc_ready"] == 1
    assert data["vc_queued"] == 0
    assert data["vc_processing"] == 0


def test_chunk_assets_endpoint(api_client: TestClient) -> None:
    pid, part = _setup(api_client)
    pl = api_client.app.state.services.project_store.part_layout(pid, part)
    store = api_client.app.state.services.project_store
    store.create_chunk(pid, part, 1)
    _write_wav(pl.narration_wav_path(1))
    _write_wav(pl.vc_wav_path(1))

    response = api_client.get(
        f"/api/v1/projects/{pid}/parts/{part}/chunks/1/assets",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["narration_exists"] is True
    assert data["vc_exists"] is True
    assert "/audio/narration" in data["narration_url"]
    assert data["narration_size"] > 0


def test_openapi_includes_e71_routes(api_client: TestClient) -> None:
    schema = api_client.get("/openapi.json").json()
    paths = schema["paths"]
    assert "/api/v1/queue/jobs" in paths
    assert "/api/v1/projects/{project_id}/parts/{part_id}/extract-text" in paths
    assert "/api/v1/projects/{project_id}/parts/{part_id}/chunking" in paths
    assert "/api/v1/projects/{project_id}/parts/{part_id}/summary" in paths
    assert (
        "/api/v1/projects/{project_id}/parts/{part_id}/chunks/{chunk_id}/assets"
        in paths
    )
    assert (
        "/api/v1/projects/{project_id}/parts/{part_id}/chunks/{chunk_id}/audio/narration"
        in paths
    )
