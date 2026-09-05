"""FastAPI application factory (E7.0)."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.routes import api_router
from app.api.services import ApplicationServices
from app.api.version import API_VERSION


@asynccontextmanager
async def _lifespan(app: FastAPI):
    services: ApplicationServices = app.state.services
    if services.settings.auto_start_worker:
        services.worker.start()
    heartbeat = _maybe_start_heartbeat(services)
    app.state.heartbeat = heartbeat
    yield
    if heartbeat is not None:
        heartbeat.stop()
    if services.worker.is_running():
        services.worker.stop()


def _maybe_start_heartbeat(services: ApplicationServices):
    import os

    from app.agent.device_id import load_or_create_device_id
    from app.agent.heartbeat import AgentHeartbeatService

    settings = services.settings
    cloud_url = settings.agent_cloud_url or os.environ.get(
        "AMINVC_AGENT_CLOUD_URL",
        "",
    ).strip()
    if not cloud_url:
        return None
    device_id = load_or_create_device_id(settings.agent_device_id_path)
    service = AgentHeartbeatService(settings, device_id, cloud_url=cloud_url)
    service.start()
    return service


def create_app(services: ApplicationServices | None = None) -> FastAPI:
    resolved = services or ApplicationServices.create()
    app = FastAPI(
        title="AminVC API",
        version=API_VERSION,
        description="REST API for AminVC audiobook backend",
        lifespan=_lifespan,
    )
    app.state.services = resolved
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    return app
