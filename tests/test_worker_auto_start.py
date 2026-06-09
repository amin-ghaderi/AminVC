"""E9.3-B — Worker auto-start lifecycle tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.api.services import ApplicationServices
from app.config.settings import AppSettings
from app.worker.state import WorkerState


def _settings(tmp_path: Path, *, auto_start_worker: bool) -> AppSettings:
    return AppSettings(
        projects_root=tmp_path / "projects",
        queue_root=tmp_path / "queue",
        events_root=tmp_path / "events",
        auto_start_worker=auto_start_worker,
    )


def test_auto_start_enabled_on_lifespan(tmp_path: Path) -> None:
    services = ApplicationServices.create(_settings(tmp_path, auto_start_worker=True))
    app = create_app(services)

    with TestClient(app) as client:
        response = client.get("/api/v1/worker")
        assert response.status_code == 200
        body = response.json()
        assert body["running"] is True
        assert body["state"] in {WorkerState.IDLE.value, WorkerState.POLLING.value}

    assert services.worker.is_running() is False


def test_auto_start_disabled_on_lifespan(tmp_path: Path) -> None:
    services = ApplicationServices.create(_settings(tmp_path, auto_start_worker=False))
    app = create_app(services)

    with TestClient(app) as client:
        response = client.get("/api/v1/worker")
        assert response.status_code == 200
        body = response.json()
        assert body["running"] is False
        assert body["state"] == WorkerState.STOPPED.value

    assert services.worker.is_running() is False


def test_manual_start_stop_endpoints_still_work(tmp_path: Path) -> None:
    services = ApplicationServices.create(_settings(tmp_path, auto_start_worker=False))
    app = create_app(services)

    with TestClient(app) as client:
        assert client.get("/api/v1/worker").json()["running"] is False

        start = client.post("/api/v1/worker/start")
        assert start.status_code == 200
        assert start.json() == {"status": "started"}
        assert client.get("/api/v1/worker").json()["running"] is True

        stop = client.post("/api/v1/worker/stop")
        assert stop.status_code == 200
        assert stop.json() == {"status": "stopped"}
        assert client.get("/api/v1/worker").json()["running"] is False

    assert services.worker.is_running() is False


def test_auto_start_runs_startup_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    services = ApplicationServices.create(_settings(tmp_path, auto_start_worker=True))
    app = create_app(services)
    calls: list[str] = []

    original_startup = services.worker.startup

    def tracked_startup() -> None:
        calls.append("startup")
        original_startup()

    monkeypatch.setattr(services.worker, "startup", tracked_startup)

    with TestClient(app) as client:
        client.get("/api/v1/health")

    assert "startup" in calls
