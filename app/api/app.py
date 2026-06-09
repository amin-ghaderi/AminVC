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
    yield
    if services.worker.is_running():
        services.worker.stop()


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
