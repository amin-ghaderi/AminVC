"""E7.0 — REST API layer tests."""

from __future__ import annotations

import json
import wave
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.api.services import ApplicationServices
from app.config.settings import AppSettings
from app.contracts.states import (
    STATE_NARRATION_APPROVED,
    STATE_NARRATION_READY,
    STATE_VC_READY,
)


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


def test_health_endpoint(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_project(api_client: TestClient) -> None:
    response = api_client.post(
        "/api/v1/projects",
        json={"project_id": "zaman-entekhab", "title": "زمان انتخاب"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["project_id"] == "zaman-entekhab"
    assert data["title"] == "زمان انتخاب"


def test_create_part(api_client: TestClient) -> None:
    api_client.post("/api/v1/projects", json={"project_id": "book-1", "title": ""})
    response = api_client.post(
        "/api/v1/projects/book-1/parts",
        json={"part_id": "part-001", "title": "فصل اول"},
    )
    assert response.status_code == 201
    assert response.json()["part_id"] == "part-001"


def test_update_chunk_text(api_client: TestClient) -> None:
    api_client.post("/api/v1/projects", json={"project_id": "book-1", "title": ""})
    api_client.post(
        "/api/v1/projects/book-1/parts",
        json={"part_id": "part-001", "title": ""},
    )
    services = api_client.app.state.services
    services.project_store.create_chunk("book-1", "part-001", 1, text="initial")

    response = api_client.put(
        "/api/v1/projects/book-1/parts/part-001/chunks/1/text",
        json={"text": "edited line"},
    )
    assert response.status_code == 200
    assert response.json()["text"] == "edited line"


def test_approve_narration(api_client: TestClient) -> None:
    api_client.post("/api/v1/projects", json={"project_id": "book-1", "title": ""})
    api_client.post(
        "/api/v1/projects/book-1/parts",
        json={"part_id": "part-001", "title": ""},
    )
    services = api_client.app.state.services
    services.project_store.create_chunk("book-1", "part-001", 1, text="x")
    chunk = services.project_store.load_chunk("book-1", "part-001", 1)
    chunk.state = STATE_NARRATION_READY
    services.project_store.save_chunk("book-1", "part-001", chunk)

    response = api_client.post(
        "/api/v1/projects/book-1/parts/part-001/chunks/1/approve-narration",
    )
    assert response.status_code == 200
    assert response.json()["state"] == STATE_NARRATION_APPROVED
    assert response.json()["narration_approved"] is True


def test_approve_vc(api_client: TestClient) -> None:
    api_client.post("/api/v1/projects", json={"project_id": "book-1", "title": ""})
    api_client.post(
        "/api/v1/projects/book-1/parts",
        json={"part_id": "part-001", "title": ""},
    )
    services = api_client.app.state.services
    services.project_store.create_chunk("book-1", "part-001", 1)
    chunk = services.project_store.load_chunk("book-1", "part-001", 1)
    chunk.state = STATE_VC_READY
    services.project_store.save_chunk("book-1", "part-001", chunk)

    response = api_client.post(
        "/api/v1/projects/book-1/parts/part-001/chunks/1/approve-vc",
    )
    assert response.status_code == 200
    assert response.json()["state"] == "VCApproved"


def test_rebuild_narration(api_client: TestClient) -> None:
    api_client.post("/api/v1/projects", json={"project_id": "book-1", "title": ""})
    api_client.post(
        "/api/v1/projects/book-1/parts",
        json={"part_id": "part-001", "title": ""},
    )
    services = api_client.app.state.services
    services.project_store.create_chunk("book-1", "part-001", 1)
    chunk = services.project_store.load_chunk("book-1", "part-001", 1)
    chunk.state = STATE_NARRATION_READY
    services.project_store.save_chunk("book-1", "part-001", chunk)

    response = api_client.post(
        "/api/v1/projects/book-1/parts/part-001/chunks/1/rebuild-narration",
    )
    assert response.status_code == 200
    assert response.json()["state"] == "NarrationQueued"
    assert response.json()["narration_approved"] is False


def test_queue_narration(api_client: TestClient) -> None:
    api_client.post("/api/v1/projects", json={"project_id": "book-1", "title": ""})
    api_client.post(
        "/api/v1/projects/book-1/parts",
        json={"part_id": "part-001", "title": ""},
    )
    services = api_client.app.state.services
    services.project_store.create_chunk("book-1", "part-001", 1)

    response = api_client.post(
        "/api/v1/queue/narration",
        json={"project_id": "book-1", "part_id": "part-001", "chunk_id": 1},
    )
    assert response.status_code == 200
    assert response.json()["job_type"] == "narration"


def test_queue_vc_approval_enforcement(api_client: TestClient) -> None:
    api_client.post("/api/v1/projects", json={"project_id": "book-1", "title": ""})
    api_client.post(
        "/api/v1/projects/book-1/parts",
        json={"part_id": "part-001", "title": ""},
    )
    services = api_client.app.state.services
    services.project_store.create_chunk("book-1", "part-001", 1)
    chunk = services.project_store.load_chunk("book-1", "part-001", 1)
    chunk.state = STATE_NARRATION_READY
    services.project_store.save_chunk("book-1", "part-001", chunk)

    response = api_client.post(
        "/api/v1/queue/vc",
        json={"project_id": "book-1", "part_id": "part-001", "chunk_id": 1},
    )
    assert response.status_code == 409
    assert "approval" in response.json()["error"].lower()


def test_worker_start_stop(api_client: TestClient) -> None:
    status = api_client.get("/api/v1/worker")
    assert status.status_code == 200
    assert status.json()["running"] is False

    start = api_client.post("/api/v1/worker/start")
    assert start.status_code == 200
    assert api_client.get("/api/v1/worker").json()["running"] is True

    stop = api_client.post("/api/v1/worker/stop")
    assert stop.status_code == 200
    assert api_client.get("/api/v1/worker").json()["running"] is False


def test_build_creation(api_client: TestClient) -> None:
    api_client.post("/api/v1/projects", json={"project_id": "book-1", "title": ""})
    api_client.post(
        "/api/v1/projects/book-1/parts",
        json={"part_id": "part-001", "title": ""},
    )
    services = api_client.app.state.services
    services.project_store.create_chunk("book-1", "part-001", 1)
    services.project_store.create_chunk("book-1", "part-001", 2)

    response = api_client.post(
        "/api/v1/projects/book-1/parts/part-001/builds",
        json={"name": "Chapter03-Final", "chunks": [1, 2]},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Chapter03-Final"
    assert response.json()["chunks"] == [1, 2]


def test_resume_plan_endpoint(api_client: TestClient) -> None:
    api_client.post("/api/v1/projects", json={"project_id": "book-1", "title": ""})
    api_client.post(
        "/api/v1/projects/book-1/parts",
        json={"part_id": "part-001", "title": ""},
    )
    services = api_client.app.state.services
    services.project_store.create_chunk("book-1", "part-001", 1)

    response = api_client.get("/api/v1/projects/book-1/parts/part-001/resume-plan")
    assert response.status_code == 200
    data = response.json()
    assert "start_chunk" in data
    assert "remaining_chunks" in data


def test_recent_events_endpoint(api_client: TestClient) -> None:
    api_client.post("/api/v1/projects", json={"project_id": "book-1", "title": ""})
    response = api_client.get("/api/v1/events/recent?limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_error_mapping_invalid_approval(api_client: TestClient) -> None:
    api_client.post("/api/v1/projects", json={"project_id": "book-1", "title": ""})
    api_client.post(
        "/api/v1/projects/book-1/parts",
        json={"part_id": "part-001", "title": ""},
    )
    services = api_client.app.state.services
    services.project_store.create_chunk("book-1", "part-001", 1)

    response = api_client.post(
        "/api/v1/projects/book-1/parts/part-001/chunks/1/approve-narration",
    )
    assert response.status_code == 409
    assert "error" in response.json()


def test_openapi_generation(api_client: TestClient) -> None:
    response = api_client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "AminVC API"
    paths = schema["paths"]
    assert "/api/v1/health" in paths
    assert "/api/v1/projects" in paths
    assert "/api/v1/queue/vc" in paths


def test_full_workflow_via_api(api_client: TestClient) -> None:
    api_client.post("/api/v1/projects", json={"project_id": "book-1", "title": ""})
    api_client.post(
        "/api/v1/projects/book-1/parts",
        json={"part_id": "part-001", "title": ""},
    )
    services = api_client.app.state.services
    services.project_store.create_chunk("book-1", "part-001", 1, text="hello")
    pl = services.project_store.part_layout("book-1", "part-001")
    ref = pl.root / "reference.wav"
    _write_wav(ref)
    part = services.project_store.load_part("book-1", "part-001")
    part.processing_profile = "reference.wav"
    services.project_store.save_part(part)

    chunk = services.project_store.load_chunk("book-1", "part-001", 1)
    chunk.state = STATE_NARRATION_READY
    services.project_store.save_chunk("book-1", "part-001", chunk)
    _write_wav(pl.narration_wav_path(1))

    api_client.post(
        "/api/v1/projects/book-1/parts/part-001/chunks/1/approve-narration",
    )
    edit = api_client.put(
        "/api/v1/projects/book-1/parts/part-001/chunks/1/text",
        json={"text": "changed"},
    )
    assert edit.status_code == 200
    assert edit.json()["state"] == "NarrationQueued"

    reapprove = api_client.post(
        "/api/v1/projects/book-1/parts/part-001/chunks/1/approve-narration",
    )
    assert reapprove.status_code == 409

    chunk = services.project_store.load_chunk("book-1", "part-001", 1)
    chunk.state = STATE_NARRATION_APPROVED
    chunk.narration_approved = True
    services.project_store.save_chunk("book-1", "part-001", chunk)

    vc_queue = api_client.post(
        "/api/v1/queue/vc",
        json={"project_id": "book-1", "part_id": "part-001", "chunk_id": 1},
    )
    assert vc_queue.status_code == 200
