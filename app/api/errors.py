"""E7.0 unified HTTP error mapping."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.lifecycle.exceptions import (
    ApprovalRequiredError,
    InvalidStateTransitionError,
)
from app.queue.manager import QueueError
from app.services.audio_asset_service import AudioNotFoundError
from app.services.part_text_service import PartChunkingError, PdfTextExtractionError
from app.storage.project_store import (
    BuildNotFoundError,
    ChunkNotFoundError,
    PartNotFoundError,
    ProjectNotFoundError,
)
from app.storage.serialization import InvalidStateError


class NotImplementedApiError(Exception):
    """HTTP 501 for unsupported operations."""


def error_body(message: str) -> dict[str, str]:
    return {"error": message}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProjectNotFoundError)
    @app.exception_handler(PartNotFoundError)
    @app.exception_handler(ChunkNotFoundError)
    @app.exception_handler(BuildNotFoundError)
    async def not_found_handler(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=404, content=error_body(str(exc)))

    @app.exception_handler(AudioNotFoundError)
    async def audio_not_found_handler(
        _request: Request,
        _exc: AudioNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content=error_body("Audio file not found"))

    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(_request: Request, exc: FileNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content=error_body(str(exc)))

    @app.exception_handler(PdfTextExtractionError)
    @app.exception_handler(PartChunkingError)
    async def part_text_handler(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=400, content=error_body(str(exc)))

    @app.exception_handler(FileExistsError)
    async def exists_handler(_request: Request, exc: FileExistsError) -> JSONResponse:
        return JSONResponse(status_code=409, content=error_body(str(exc)))

    @app.exception_handler(InvalidStateTransitionError)
    @app.exception_handler(ApprovalRequiredError)
    async def conflict_handler(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=409, content=error_body(str(exc)))

    @app.exception_handler(InvalidStateError)
    @app.exception_handler(QueueError)
    @app.exception_handler(ValueError)
    async def bad_request_handler(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=400, content=error_body(str(exc)))

    @app.exception_handler(NotImplementedApiError)
    async def not_implemented_handler(
        _request: Request,
        exc: NotImplementedApiError,
    ) -> JSONResponse:
        return JSONResponse(status_code=501, content=error_body(str(exc)))

    @app.exception_handler(Exception)
    async def unexpected_handler(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content=error_body(str(exc)))
