"""Phase 1 local-agent heartbeat / cloud status tests."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from app.agent.device_id import load_or_create_device_id
from app.agent.heartbeat import AgentHeartbeatService
from app.api.app import create_app
from app.api.services import ApplicationServices
from app.config.settings import AppSettings
from cloud_api.app import create_cloud_app
from cloud_api.cors import LOCAL_DEV_ORIGINS, resolve_cors_origins
from cloud_api.store import HeartbeatStore


def test_device_id_is_stable(tmp_path: Path) -> None:
    path = tmp_path / "device_id"
    first = load_or_create_device_id(path)
    second = load_or_create_device_id(path)
    assert first == second
    assert path.read_text(encoding="utf-8").strip() == first


def test_device_id_override_persists(tmp_path: Path) -> None:
    path = tmp_path / "device_id"
    load_or_create_device_id(path)
    overridden = load_or_create_device_id(path, override="fixed-device")
    assert overridden == "fixed-device"
    assert load_or_create_device_id(path) == "fixed-device"


def test_heartbeat_send_once_posts_payload(tmp_path: Path) -> None:
    captured: list[tuple[str, dict[str, str]]] = []

    def fake_post(url: str, json: dict[str, str], timeout: float):
        captured.append((url, json))
        return SimpleNamespace(status_code=200)

    settings = AppSettings(
        agent_cloud_url="http://cloud.test:8090",
        agent_device_id_path=tmp_path / "device_id",
        auto_start_worker=False,
    )
    service = AgentHeartbeatService(
        settings,
        "dev-1",
        post=fake_post,
    )
    assert service.send_once() is True
    assert captured[0][0] == "http://cloud.test:8090/agent/heartbeat"
    assert captured[0][1]["device_id"] == "dev-1"
    assert captured[0][1]["status"] == "online"
    assert "timestamp" in captured[0][1]


def test_heartbeat_network_failure_does_not_raise(tmp_path: Path) -> None:
    def boom(*_args, **_kwargs):
        raise httpx.ConnectError("offline")

    settings = AppSettings(
        agent_cloud_url="http://127.0.0.1:1",
        agent_device_id_path=tmp_path / "device_id",
        auto_start_worker=False,
    )
    service = AgentHeartbeatService(settings, "dev-1", post=boom)
    assert service.send_once() is False


def test_cloud_heartbeat_and_status() -> None:
    store = HeartbeatStore(online_timeout_seconds=30)
    client = TestClient(create_cloud_app(store))
    posted = client.post(
        "/agent/heartbeat",
        json={
            "device_id": "dev-1",
            "timestamp": "2026-09-05T12:00:00+00:00",
            "status": "online",
        },
    )
    assert posted.status_code == 200
    body = posted.json()
    assert body["device_id"] == "dev-1"
    assert body["accepted"] is True

    status = client.get("/agent/status/dev-1")
    assert status.status_code == 200
    payload = status.json()
    assert payload["device_id"] == "dev-1"
    assert payload["last_seen"] is not None


def test_cloud_recent_heartbeat_is_online() -> None:
    store = HeartbeatStore(online_timeout_seconds=30)
    client = TestClient(create_cloud_app(store))
    now = datetime.now(timezone.utc).isoformat()
    posted = client.post(
        "/agent/heartbeat",
        json={"device_id": "dev-live", "timestamp": now},
    )
    assert posted.status_code == 200
    payload = client.get("/agent/status/dev-live").json()
    assert payload["online"] is True
    assert payload["device_id"] == "dev-live"


def test_cloud_unknown_device_is_offline() -> None:
    client = TestClient(create_cloud_app())
    payload = client.get("/agent/status/missing").json()
    assert payload == {
        "device_id": "missing",
        "online": False,
        "last_seen": None,
    }


def test_cloud_timeout_marks_offline() -> None:
    store = HeartbeatStore(online_timeout_seconds=30)
    store.record("dev-1", "2026-09-05T12:00:00+00:00")
    later = datetime(2026, 9, 5, 12, 0, 31, tzinfo=timezone.utc)
    payload = store.status("dev-1", now=later)
    assert payload["online"] is False
    still = store.status(
        "dev-1",
        now=datetime(2026, 9, 5, 12, 0, 30, tzinfo=timezone.utc),
    )
    assert still["online"] is True


def test_local_agent_lifespan_sends_heartbeat(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store = HeartbeatStore(online_timeout_seconds=30)
    cloud = TestClient(create_cloud_app(store))

    def post_to_cloud(url: str, json: dict[str, str], timeout: float):
        path = url[url.find("/agent/") :]
        response = cloud.post(path, json=json)
        return SimpleNamespace(status_code=response.status_code)

    monkeypatch.setattr("app.agent.heartbeat.httpx.post", post_to_cloud)

    settings = AppSettings(
        projects_root=tmp_path / "projects",
        queue_root=tmp_path / "queue",
        events_root=tmp_path / "events",
        agent_device_id_path=tmp_path / "agent" / "device_id",
        agent_cloud_url="http://cloud.test",
        auto_start_worker=False,
        agent_heartbeat_interval_seconds=60,
    )
    services = ApplicationServices.create(settings)
    app = create_app(services)

    with TestClient(app) as client:
        assert client.get("/api/v1/health").status_code == 200
        device_id = (tmp_path / "agent" / "device_id").read_text(encoding="utf-8").strip()
        deadline = time.time() + 2.0
        status = store.status(device_id)
        while not status["online"] and time.time() < deadline:
            time.sleep(0.05)
            status = store.status(device_id)
        assert status["online"] is True
        assert status["device_id"] == device_id


def test_heartbeat_disabled_without_cloud_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AMINVC_AGENT_CLOUD_URL", raising=False)
    settings = AppSettings(
        projects_root=tmp_path / "projects",
        queue_root=tmp_path / "queue",
        events_root=tmp_path / "events",
        agent_device_id_path=tmp_path / "agent" / "device_id",
        agent_cloud_url="",
        auto_start_worker=False,
    )
    app = create_app(ApplicationServices.create(settings))
    with TestClient(app) as client:
        assert client.get("/api/v1/health").status_code == 200
        assert app.state.heartbeat is None


def test_heartbeat_http_error_does_not_raise(tmp_path: Path) -> None:
    def reject(*_args, **_kwargs):
        return SimpleNamespace(status_code=503)

    settings = AppSettings(
        agent_cloud_url="http://cloud.test",
        agent_device_id_path=tmp_path / "device_id",
        auto_start_worker=False,
    )
    service = AgentHeartbeatService(settings, "dev-1", post=reject)
    assert service.send_once() is False


def test_cors_defaults_to_local_vite_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AMINVC_WEB_ORIGIN", raising=False)
    assert resolve_cors_origins() == list(LOCAL_DEV_ORIGINS)
    client = TestClient(create_cloud_app())
    allowed = client.get(
        "/agent/status/dev-1",
        headers={"Origin": "http://localhost:5173"},
    )
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"
    blocked = client.get(
        "/agent/status/dev-1",
        headers={"Origin": "https://evil.example"},
    )
    assert blocked.headers.get("access-control-allow-origin") is None


def test_cors_uses_aminvc_web_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMINVC_WEB_ORIGIN", "https://aminvc.vercel.app")
    origins = resolve_cors_origins()
    assert origins == ["https://aminvc.vercel.app"]
    assert "*" not in origins
    client = TestClient(create_cloud_app(web_origins=origins))
    allowed = client.get(
        "/agent/status/dev-1",
        headers={"Origin": "https://aminvc.vercel.app"},
    )
    assert allowed.headers.get("access-control-allow-origin") == "https://aminvc.vercel.app"
    local = client.get(
        "/agent/status/dev-1",
        headers={"Origin": "http://localhost:5173"},
    )
    assert local.headers.get("access-control-allow-origin") is None


def test_cors_preflight_allows_configured_origin() -> None:
    client = TestClient(
        create_cloud_app(web_origins=["https://aminvc.vercel.app"]),
    )
    preflight = client.options(
        "/agent/status/dev-1",
        headers={
            "Origin": "https://aminvc.vercel.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers.get("access-control-allow-origin") == "https://aminvc.vercel.app"


def test_cloud_surface_is_heartbeat_and_status_only() -> None:
    client = TestClient(create_cloud_app())
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404
    paths = {route.path for route in client.app.routes}
    assert "/agent/heartbeat" in paths
    assert "/agent/status/{device_id}" in paths
    assert "/api/v1/projects" not in paths


def test_heartbeat_rejects_oversized_payload() -> None:
    client = TestClient(create_cloud_app())
    rejected = client.post(
        "/agent/heartbeat",
        json={"device_id": "x" * 200, "timestamp": "2026-09-05T12:00:00+00:00"},
    )
    assert rejected.status_code == 422
