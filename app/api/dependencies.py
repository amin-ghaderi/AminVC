"""FastAPI dependencies."""

from __future__ import annotations

from fastapi import Request

from app.api.services import ApplicationServices


def get_services(request: Request) -> ApplicationServices:
    return request.app.state.services
