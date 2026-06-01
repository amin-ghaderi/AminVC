"""Worker control routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_services
from app.api.schemas.common import WorkerStatusResponse
from app.api.services import ApplicationServices

router = APIRouter(prefix="/worker", tags=["worker"])


@router.get("", response_model=WorkerStatusResponse)
def worker_status(
    services: ApplicationServices = Depends(get_services),
) -> WorkerStatusResponse:
    return WorkerStatusResponse(
        running=services.worker.is_running(),
        state=services.worker.state.value,
    )


@router.post("/start")
def worker_start(services: ApplicationServices = Depends(get_services)) -> dict[str, str]:
    services.worker.start()
    return {"status": "started"}


@router.post("/stop")
def worker_stop(services: ApplicationServices = Depends(get_services)) -> dict[str, str]:
    services.worker.stop()
    return {"status": "stopped"}
