"""FastAPI application factory (E7.0)."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.routes import api_router
from app.api.services import ApplicationServices
from app.api.version import API_VERSION


def create_app(services: ApplicationServices | None = None) -> FastAPI:
    app = FastAPI(
        title="AminVC API",
        version=API_VERSION,
        description="REST API for AminVC audiobook backend",
    )
    app.state.services = services or ApplicationServices.create()
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    return app
